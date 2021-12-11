

from enum import Enum

from construct import StreamError
from twisted.internet.defer import DeferredQueue, inlineCallbacks, Deferred
from twisted.internet.protocol import Protocol
from tendril.asynchronous.utils.logger import TwistedLoggerMixin


class ProtocolState(Enum):
    UNLOCKED = 0
    SYNC_WAIT = 1
    SYNC_CHECK = 2
    SYNC_LOCKED = 3
    BROKEN = 4


class VariableFrameStreamProtocol(Protocol, TwistedLoggerMixin):
    _frame_marker = None
    _frame_marker_skip = 0
    _frame_max_len = 256
    _sync_timeout = 3
    _construct = None

    def __init__(self, target):
        super(VariableFrameStreamProtocol, self).__init__()
        self._target = target
        self._customers = []
        self._managers = []
        self._detect_result = None
        self.state = ProtocolState.UNLOCKED
        self._reactor = None
        self._data_queue = DeferredQueue()
        self._framer_running = False

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self.log.info("{} Changing State : {}".format(self._target, value))
        for manager in self._managers:
            manager.put(value)
        if self._detect_result and value == ProtocolState.BROKEN:
            self._detect_result.callback(False)
        self._state = value

    def _sync_timeout_handler(self):
        if self.state == ProtocolState.SYNC_WAIT:
            self.state = ProtocolState.BROKEN
        if self.state == ProtocolState.SYNC_CHECK:
            self._reactor.callLater(self._sync_timeout, self._sync_timeout_handler)

    def _start_framer(self):
        if self._framer_running:
            return
        self._framer_running = True
        self._framer()

    @inlineCallbacks
    def _framer(self):
        data_buffer = bytearray()
        while True:
            new_data = yield self._data_queue.get()
            data_buffer.extend(new_data)
            try:
                parsed = self._construct.parse(data_buffer)
                data_buffer = data_buffer[len(parsed.data):]
                self.dispatch_frame(parsed)
                if self.state == ProtocolState.SYNC_CHECK:
                    self.state = ProtocolState.SYNC_LOCKED
                    if self._detect_result:
                        self._detect_result.callback(True)
            except StreamError as e:
                if len(data_buffer) > self._frame_max_len:
                    if self.state == ProtocolState.SYNC_CHECK:
                        self.state = ProtocolState.SYNC_WAIT
                    if self.state == ProtocolState.SYNC_LOCKED:
                        self.state = ProtocolState.BROKEN
                    data_buffer = bytearray()

    def dispatch_frame(self, parsed_frame):
        for customer in self._customers:
            customer.put(parsed_frame)

    def validate_device(self, reactor):
        self.state = ProtocolState.SYNC_WAIT
        self._reactor = reactor
        self._detect_result = Deferred()
        self._reactor.callLater(self._sync_timeout, self._sync_timeout_handler)
        self._start_framer()
        return self._detect_result

    def dataReceived(self, data: bytes):
        if self.state in (ProtocolState.UNLOCKED, ProtocolState.BROKEN):
            return
        if self.state == ProtocolState.SYNC_WAIT:
            sidx = data.find(self._frame_marker)
            if sidx == -1:
                return
            data = bytearray(data[sidx + self._frame_marker_skip:])
            self.state = ProtocolState.SYNC_CHECK
        self._data_queue.put(data)
