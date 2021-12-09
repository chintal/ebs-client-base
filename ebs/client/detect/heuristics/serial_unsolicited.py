

from .serial_base import SerialHeuristicBase


class SerialUnsolicitedHeuristic(SerialHeuristicBase):
    def __init__(self):
        super(SerialUnsolicitedHeuristic, self).__init__()

    def test(self, target):
        pass
