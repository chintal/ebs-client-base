

from twisted.internet.defer import DeferredQueue
from twisted.internet.defer import inlineCallbacks

from ebs.client.extensions.routers import PacketRouter
from .base import ChannelBase


class CompositeChannelBase(ChannelBase):
    _name = "CompositeChannelBase"

    def __init__(self, *args, **kwargs):
        super(CompositeChannelBase, self).__init__(*args, **kwargs)
        self._channels = {}
        self._build()

    def install_channel(self, channel):
        self._channels[channel.local_name] = channel

    @property
    def value(self):
        return {name: chn.value for name, chn in self._channels.items()}

    def _build(self):
        raise NotImplementedError

    def __getattr__(self, item):
        if item in self._channels.keys():
            return self._channels[item]


class TransparentCompositeChannel(CompositeChannelBase):
    _name = "TransparentCompositeChannel"

    def _build(self):
        raise NotImplementedError

    def bind_router(self, router):
        for name, channel in self._channels.items():
            channel.bind_router(router)


class RoutedCompositeChannel(CompositeChannelBase):
    _name = "RoutedCompositeChannel"
    _identifier = None

    def __init__(self, *args, **kwargs):
        self._queue = None
        self._router = PacketRouter(self)
        super(RoutedCompositeChannel, self).__init__(*args, **kwargs)

    def _build(self):
        raise NotImplementedError

    def install_channel(self, channel):
        super(RoutedCompositeChannel, self).install_channel(channel)
        channel.bind_router(self._router)

    def _processor(self, packet):
        raise NotImplementedError

    @inlineCallbacks
    def _packet_handler(self):
        while True:
            packet = yield self._queue.get()
            for identifier, data in self._processor(packet):
                self._router.route_packet(identifier, data)

    def bind_router(self, router):
        self._queue = DeferredQueue()
        router.install_packet_handler(self._identifier, self._queue)
        self._packet_handler()
