

from tendril.asynchronous.utils.logger import TwistedLoggerMixin

from .detect.manager import DetectionManager


class ClientCore(TwistedLoggerMixin):
    def __init__(self, reactor, *args, **kwargs):
        super(ClientCore, self).__init__(*args, **kwargs)
        self._reactor = reactor
        self.log_init()
        self._detection_manager = DetectionManager('ebs.client.detect', self)

    @property
    def reactor(self):
        return self._reactor

    def start(self):
        self._detection_manager.start()
