

from tendril.asynchronous.utils.engines import AsyncEngineBase


class DetectorBase(AsyncEngineBase):
    def __init__(self, parent, *args, **kwargs):
        super(DetectorBase, self).__init__(*args, **kwargs)
        self._parent = parent
        self._handlers = {}
        self._supported_devices = {}
        self._connected_devices = {}

    @property
    def reactor(self):
        return self._parent.reactor

    def _start(self):
        raise NotImplementedError

    def _stop(self):
        raise NotImplementedError

    def install_handler(self, event, handler):
        parts = event.split(':')
        action = parts.pop(0)
        filters = parts
        if action not in self._handlers.keys():
            self._handlers[action] = []
        self._handlers[action].append((filters, handler))

    def install_device_heuristic(self, name, heuristic):
        self.log.info("Installing Heuristic for '{}' from '{}'"
                      "".format(name, heuristic.__class__))
        self._supported_devices[name] = heuristic

    def on_connect(self, device_name, parameters):
        for filters, handler in self._handlers['connect']:
            handler(device_name, parameters)

    def on_disconnect(self, device_name, parameters):
        for filters, handler in self._handlers['disconnect']:
            handler(device_name, parameters)


def install(manager):
    pass
