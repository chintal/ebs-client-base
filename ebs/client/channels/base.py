

from tendril.asynchronous.utils.logger import TwistedLoggerMixin


class ChannelBase(TwistedLoggerMixin):
    _name = "ChannelBase"

    def __init__(self, parent, *args, index=None, **kwargs):
        super(ChannelBase, self).__init__(*args, **kwargs)
        self._parent = parent
        self._index = index
        self._queues = {}

    @property
    def parent(self):
        return self._parent

    @property
    def device(self):
        target = self._parent
        while isinstance(target, ChannelBase):
            target = target.parent
        return target

    @property
    def name(self):
        parts = [self._name]
        if self._index is not None:
            parts.append(str(self._index))
        if isinstance(self._parent, ChannelBase):
            parts.insert(0, self._parent.name)
        return '.'.join(parts)

    @property
    def local_name(self):
        return self._name

    def bind_router(self, router):
        raise NotImplementedError
