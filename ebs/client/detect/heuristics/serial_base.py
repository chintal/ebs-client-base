

from .base import HeuristicBase


class SerialHeuristicBase(HeuristicBase):
    _baud = 115200
    _width = 8
    _parity = 0
    _stop = 1

    def __init__(self):
        super(SerialHeuristicBase, self).__init__()

    def test(self, target):
        pass
