

from tendril.asynchronous.utils.engines import AsyncEngineBase


class DeviceClientBase(AsyncEngineBase):
    def __init__(self, *args, **kwargs):
        super(DeviceClientBase, self).__init__(*args, **kwargs)

    def _connect(self):
        raise NotImplementedError

    def _disconnect(self):
        raise NotImplementedError

    def _start(self):
        self._connect()

    def _stop(self):
        self._disconnect()

    def connect(self):
        self.start()

    def disconnect(self):
        self.stop()

    @property
    def connected(self):
        return self._running


