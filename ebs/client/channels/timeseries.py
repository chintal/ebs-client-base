

from numbers import Number
from tendril.utils.types.unitbase import NumericalUnitBase
from tendril.utils.types.signalbase import SignalPoint
from tendril.utils.types.signalbase import SignalWave
from .simple import SimplePersistentChannel


class SimpleTimeSeriesChannel(SimplePersistentChannel):
    _name = "SimpleTimeSeriesChannel"
    _type = int
    _signalwave_kwargs = {}

    def __init__(self, *args, **kwargs):
        super(SimpleTimeSeriesChannel, self).__init__(*args, **kwargs)
        self._create_wave()
        self._stability_change_handlers = []

    def _create_wave(self):
        self._wave = SignalWave(self._type, use_point_ts=True,
                                **self._signalwave_kwargs)

    @property
    def value(self):
        return self._wave.latest_point

    @value.setter
    def value(self, v):
        _point = SignalPoint(self._type, v)
        prev_value = self._wave.latest_point
        if issubclass(self._type, (Number, NumericalUnitBase)):
            prev_stability = self._wave.is_stable
        self._wave.add_point(_point)
        if prev_value != _point.value:
            self._value_change_hook(_point)
        if issubclass(self._type, (Number, NumericalUnitBase)):
            stability = self._wave.is_stable
            if prev_stability != stability:
                self._stability_change_hook(stability)

    @property
    def wave(self):
        return self._wave

    def _stability_change_hook(self, value):
        for predicate, handler in self._stability_change_handlers:
            if predicate(value):
                handler(self, value)

    def install_stability_change_handler(self, predicate, handler):
        self._stability_change_handlers.append((predicate, handler))

    def _processor(self, packet):
        raise NotImplementedError
