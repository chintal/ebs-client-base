

from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import DeferredQueue
from ebs.client.channels.base import ChannelBase


class SimplePersistentChannel(ChannelBase):
    _name = "SimplePersistentChannel"
    _identifier = None

    def __init__(self, *args, **kwargs):
        super(SimplePersistentChannel, self).__init__(*args, **kwargs)
        self._queue = None
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v

    def _processor(self, packet):
        raise NotImplementedError

    @inlineCallbacks
    def _packet_handler(self):
        while True:
            packet = yield self._queue.get()
            self.value = self._processor(packet)

    def bind_router(self, router):
        self._queue = DeferredQueue()
        router.install_packet_handler(self._identifier, self._queue)
        self._packet_handler()
