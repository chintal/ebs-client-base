

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

    @property
    def identifier(self):
        return self._identifier

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
        router.install_packet_handler(self.identifier, self._queue)
        self._packet_handler()


class SliceRoutedCompositeChannel(RoutedCompositeChannel):
    def __init__(self, *args, **kwargs):
        super(SliceRoutedCompositeChannel, self).__init__(*args, **kwargs)
        _slices = []

    def _build(self):
        raise NotImplementedError

    def install_channel(self, channel):
        super(SliceRoutedCompositeChannel, self).install_channel(channel)
        idx = channel.identifier
        if not isinstance(idx, (int, slice)):
            raise TypeError("Children of a SliceRoutedCompositeChannel must have "
                            "identifiers which can be used for list slicing "
                            "(int, slice). Got {} ({}).".format(idx, type(idx)))
        self._slices.append(channel.identifier)
        channel.bind_router(self._router)

    def _processor(self, packet):
        rv = []
        for spec in self._slices:
            if isinstance(spec, int):
                rv.append((spec, packet[spec]))
            elif isinstance(spec, tuple) and spec[0] == 'slice':
                cspec = slice(spec[1], spec[2], spec[3])
                rv.append((spec, packet[cspec]))
        return rv

