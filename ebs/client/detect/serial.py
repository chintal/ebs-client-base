

from functools import partial
from serial.tools import list_ports
from twisted.internet.defer import DeferredList
from twisted.internet.defer import inlineCallbacks
from .base import DetectorBase


class SerialDeviceDetector(DetectorBase):
    def __init__(self, *args, **kwargs):
        super(SerialDeviceDetector, self).__init__(*args, **kwargs)
        self._task = None

    @property
    def candidates(self):
        return [p.device for p in list_ports.comports()]

    def detect_handler(self, name, device, result):
        print(name, device, result)

    @inlineCallbacks
    def search(self):
        for name, device in self._supported_devices.items():
            port_results = []
            for port in self.candidates:
                if port in self._connected_devices.keys():
                    continue
                self.log.info("Searching for '{}' on port '{}'"
                              "".format(name, port))
                result = device.check_for_device(self.reactor, port)
                result.addCallback(partial(self.detect_handler, name, device))
                port_results.append(result)
            yield DeferredList(port_results)

    def _start(self):
        # self._parent.install_handler("connect:usbserial", self.search)
        self.search()

    def _stop(self):
        pass


def install(manager):
    manager.log.info("Installing {}".format(SerialDeviceDetector.__name__))
    manager.install_detector('serial', SerialDeviceDetector(manager))
