

from enum import Enum

from construct import StreamError
from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import DeferredQueue
from twisted.internet.defer import DeferredSemaphore
from twisted.internet.protocol import Protocol
from tendril.asynchronous.utils.logger import TwistedLoggerMixin


class ProtocolState(Enum):
    UNLOCKED = 0
    SYNC_WAIT = 1
    SYNC_CHECK = 2
    SYNC_LOCKED = 3
    BROKEN = 4


class TransmitterAckState(Enum):
    UNUSED = 0
    WAITING = 1
    ACKED = 2
    ERRED = 3


class VariableFrameStreamProtocol(Protocol, TwistedLoggerMixin):
    _frame_marker = None
    _frame_marker_skip = 0
    _frame_max_len = 256
    _sync_timeout = 3
    _construct = None
    _tx_wait_ack = False

    def __init__(self, target):
        super(VariableFrameStreamProtocol, self).__init__()
        self._target = target
        self._customers = []
        self._managers = []
        self.state = ProtocolState.UNLOCKED
        self._reactor = None
        self._data_queue = DeferredQueue()
        self._transmit_queue = None
        self._framer_running = False
        self._transmitter_running = False
        self._tx_ack = TransmitterAckState.UNUSED
        self._tx_semaphore = DeferredSemaphore(1)
        self._tx_cb = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self.log.debug("{target} Changing State : {state}",
                       target=self._target, state=value)
        for manager in self._managers:
            manager(self._target, value)
        self._state = value

    def register_manager(self, handler):
        self._managers.append(handler)

    def deregister_manager(self, handler):
        self._managers.remove(handler)

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
            except StreamError as e:
                if len(data_buffer) > self._frame_max_len:
                    if self.state == ProtocolState.SYNC_CHECK:
                        self.state = ProtocolState.SYNC_WAIT
                    if self.state == ProtocolState.SYNC_LOCKED:
                        self.state = ProtocolState.BROKEN
                    data_buffer = bytearray()

    def register_customer(self, handler):
        self._customers.append(handler)

    def deregister_customer(self, handler):
        self._customers.remove(handler)

    def dispatch_frame(self, parsed_frame):
        self.log.debug("{target} Dispatching frame : {frame}",
                       target=self._target, frame=parsed_frame)
        for customer in self._customers:
            customer.put(parsed_frame)

    def initialize_connection(self, reactor):
        self.state = ProtocolState.SYNC_WAIT
        self._reactor = reactor
        self._reactor.callLater(self._sync_timeout, self._sync_timeout_handler)
        self._start_framer()

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

    def bind_transmitter(self, transmit_queue):
        if self._transmit_queue:
            raise IOError("A transmitter is already bound to this protocol!")
        self._transmit_queue = transmit_queue
        self._start_transmitter()

    def _start_transmitter(self):
        if self._transmitter_running:
            return
        self._transmitter_running = True
        self._transmitter()

    @property
    def tx_ack(self):
        return self._tx_ack

    def _tx_end_transaction(self, result):
        self._tx_semaphore.release()
        if self._tx_cb:
            self._tx_cb(result)
            self._tx_cb = None

    @tx_ack.setter
    def tx_ack(self, value):
        if value in [TransmitterAckState.ACKED, TransmitterAckState.ERRED]:
            self._tx_end_transaction(result=value)
        self._tx_ack = value

    @inlineCallbacks
    def _transmitter(self):
        while True:
            message, expect_ack, cb = yield self._transmit_queue.get()
            yield self._tx_semaphore.acquire()
            self._tx_cb = cb
            packed_message = self._construct.build(message)
            self.transport.write(packed_message)
            if expect_ack and self._tx_wait_ack:
                self.tx_ack = TransmitterAckState.WAITING
            else:
                self._tx_end_transaction(True)
