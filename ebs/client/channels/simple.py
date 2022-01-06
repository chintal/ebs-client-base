

from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import DeferredQueue
from ebs.client.channels.base import ChannelBase


class SimplePersistentChannel(ChannelBase):
    _name = "SimplePersistentChannel"
    _identifier = None
    _type = None

    def __init__(self, *args, **kwargs):
        super(SimplePersistentChannel, self).__init__(*args, **kwargs)
        self._queue = None
        self._value = None
        self._value_change_handlers = []
        self._value_change_hook_enabled = False

    @property
    def identifier(self):
        if isinstance(self._identifier, slice):
            return ('slice',
                    self._identifier.start,
                    self._identifier.stop,
                    self._identifier.step)
        return self._identifier

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        if self._type and not isinstance(v, self._type):
            v = self._type(v)
        if self._value_change_hook_enabled:
            prev = self._value
        self._value = v
        if self._value_change_hook_enabled and not prev == v:
            self._value_change_hook(v)

    def _value_change_hook(self, value):
        for predicate, handler in self._value_change_handlers:
            if predicate(value):
                handler(self, value)

    def install_value_change_handler(self, predicate, handler):
        self._value_change_hook_enabled = True
        self._value_change_handlers.append((predicate, handler))

    def _processor(self, packet):
        raise NotImplementedError

    @inlineCallbacks
    def _packet_handler(self):
        while True:
            packet = yield self._queue.get()
            self.value = self._processor(packet)

    def bind_router(self, router):
        self._queue = DeferredQueue()
        router.install_packet_handler(self.identifier, self._queue)
        self._packet_handler()
