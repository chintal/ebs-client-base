

class HeuristicBase(object):
    _domain = 'serial'

    def __init__(self):
        pass

    @property
    def domain(self):
        return self._domain

    def check_for_device(self, reactor, target):
        raise NotImplementedError
