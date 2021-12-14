

class ExtensionBase(object):
    def __init__(self, parent):
        self._parent = parent

    @property
    def log(self):
        return self._parent.log
