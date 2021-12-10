

from functools import partial
from twisted.internet.defer import Deferred
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol

from twisted.internet.serialport import SerialPort
from twisted.internet.serialport import EIGHTBITS
from twisted.internet.serialport import PARITY_NONE
from twisted.internet.serialport import STOPBITS_ONE

from .base import HeuristicBase


class Echo(Protocol):
    def __init__(self):
        super(Echo, self).__init__()

    def validate_device(self, reactor):
        d = Deferred()
        reactor.callLater(1, d.callback, False)
        return d

    def dataReceived(self, data: bytes):
        print("Recieved: {}".format(data))


class SerialDeviceHeuristic(HeuristicBase):
    _baud = 115200
    _width = EIGHTBITS
    _parity = PARITY_NONE
    _stop = STOPBITS_ONE

    _protocol = Echo

    def __init__(self):
        super(SerialDeviceHeuristic, self).__init__()
        self._ports = []

    def cleanup(self, port, result):
        port.loseConnection()
        self._ports.remove(port)
        return result

    def check_for_device(self, reactor, target):
        test_protocol = self._protocol()
        test_port = SerialPort(self._protocol(), target, reactor,
                               baudrate=self._baud, bytesize=self._width,
                               parity=self._parity, stopbits=self._stop)

        self._ports.append(test_port)
        result = test_protocol.validate_device(reactor)
        result.addBoth(partial(self.cleanup, test_port))
        return result
