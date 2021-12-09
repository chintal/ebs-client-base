

from serial.tools import list_ports
from twisted.internet.defer import inlineCallbacks
from .base import DetectorBase


class SerialDeviceDetector(DetectorBase):
    def __init__(self, *args, **kwargs):
        super(SerialDeviceDetector, self).__init__(*args, **kwargs)
        self._task = None

    @property
    def candidates(self):
        return [p.device for p in list_ports.comports()]

    @inlineCallbacks
    def search(self):
        for port in self.candidates:
            for name, device in self._supported_devices.items():
                self.log.info("Searching for '{}' on port '{}'"
                              "".format(name, port))
                yield device.test(port)

    def _start(self):
        # self._parent.install_handler("connect:usbserial", self.search)
        self.search()

    def _stop(self):
        pass


def install(manager):
    manager.log.info("Installing {}".format(SerialDeviceDetector.__name__))
    manager.install_detector('serial', SerialDeviceDetector(manager))
