

from twisted.internet.defer import DeferredQueue
from twisted.internet.defer import inlineCallbacks

from .base import ExtensionBase


class PacketRouter(ExtensionBase):
    def __init__(self, *args, **kwargs):
        super(PacketRouter, self).__init__(*args, **kwargs)
        self._route_map = {}
        self._dropped_identifiers = {}
        self._suppressed_identifiers = []

    def suppress_identifiers(self, identifier_spec):
        if not isinstance(identifier_spec, list):
            identifier_spec = [identifier_spec]
        self._suppressed_identifiers.extend(identifier_spec)

    def install_packet_handler(self, identifier_spec, frame_queue, expiry=0):
        if not isinstance(identifier_spec, list):
            identifier_spec = [identifier_spec]
        for identifier in identifier_spec:
            if identifier in self._route_map.keys():
                raise ValueError("Trying to install a duplicate handler for "
                                 "the identifier {}".format(identifier))
            self._route_map[identifier] = (frame_queue, expiry)

    def uninstall_packet_handler(self, identifier_spec):
        if not isinstance(identifier_spec, list):
            identifier_spec = [identifier_spec]
        for identifier in identifier_spec:
            self._route_map.pop(identifier)

    def route_packet(self, identifier, payload):
        if identifier in self._suppressed_identifiers:
            return
        if identifier not in self._route_map.keys():
            if identifier not in self._dropped_identifiers.keys():
                self._dropped_identifiers[identifier] = 0
                self.log.warn("No routes installed for packets with identifier"
                              " {identifier}!", identifier=hex(identifier))
            self._dropped_identifiers[identifier] += 1
            return
        queue, expiry = self._route_map[identifier]
        if expiry:
            expiry = expiry - 1
            if not expiry:
                self.uninstall_packet_handler(identifier)
            else:
                self._route_map[identifier] = (queue, expiry)
        self.log.debug("Dispatching packet with identifier {identifier}",
                       identifier=identifier)
        queue.put(payload)


class UnpackingRouter(ExtensionBase):
    def __init__(self, unpacker, *args, **kwargs):
        super(UnpackingRouter, self).__init__(*args, **kwargs)
        self._unpacker = unpacker
        self._input = DeferredQueue()
        self._router = PacketRouter(self)

    @property
    def input(self):
        return self._input

    _delegated = [
        'install_packet_handler',
        'uninstall_packet_handler',
        'route_packet',
        'suppress_identifiers'
    ]

    def __getattr__(self, item):
        if item in self._delegated:
            return getattr(self._router, item)
        else:
            raise AttributeError("{} has no attribute {}"
                                 "".format(self.__class__, item))

    @inlineCallbacks
    def _packet_handler(self):
        while True:
            packet = yield self._input.get()
            for identifier, data in self._unpacker(packet):
                self._router.route_packet(identifier, data)

    def start(self):
        self._packet_handler()
