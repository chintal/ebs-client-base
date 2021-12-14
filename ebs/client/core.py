

from tendril.asynchronous.utils.logger import TwistedLoggerMixin
from .devices.manager import DeviceManager


class ClientCore(TwistedLoggerMixin):
    def __init__(self, reactor, *args, **kwargs):
        super(ClientCore, self).__init__(*args, **kwargs)
        self._reactor = reactor
        self.log_init()
        self._device_manager = DeviceManager('ebs.client.devices', self)

    @property
    def reactor(self):
        return self._reactor

    def start(self):
        self._device_manager.start()
