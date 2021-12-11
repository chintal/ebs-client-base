

from tendril.asynchronous.utils.logger import TwistedLoggerMixin


class HeuristicBase(TwistedLoggerMixin):
    _domain = 'serial'

    @property
    def domain(self):
        return self._domain

    def check_for_device(self, reactor, target):
        raise NotImplementedError
