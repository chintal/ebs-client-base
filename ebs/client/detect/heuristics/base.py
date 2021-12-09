

class HeuristicBase(object):
    _domain = 'serial'

    def __init__(self):
        pass

    @property
    def domain(self):
        return self._domain

    def test(self, target):
        raise NotImplementedError
