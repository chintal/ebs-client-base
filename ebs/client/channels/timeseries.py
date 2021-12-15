

from tendril.utils.types.signalbase import SignalPoint
from tendril.utils.types.signalbase import SignalWave
from .simple import SimplePersistentChannel


class SimpleTimeSeriesChannel(SimplePersistentChannel):
    _name = "SimpleTimeSeriesChannel"
    _type = int

    def __init__(self, *args, **kwargs):
        super(SimpleTimeSeriesChannel, self).__init__(*args, **kwargs)
        self._create_wave()

    def _create_wave(self):
        self._wave = SignalWave(self._type, use_point_ts=True)

    @property
    def value(self):
        return self._wave.latest_point

    @value.setter
    def value(self, v):
        _point = SignalPoint(self._type, v)
        self._wave.add_point(_point)

    @property
    def wave(self):
        return self._wave

    def _processor(self, packet):
        raise NotImplementedError
