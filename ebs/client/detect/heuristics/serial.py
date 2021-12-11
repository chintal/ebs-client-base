

from enum import Enum
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol

from twisted.internet.serialport import SerialPort
from twisted.internet.serialport import EIGHTBITS
from twisted.internet.serialport import PARITY_NONE
from twisted.internet.serialport import STOPBITS_ONE

from ebs.client.protocols.stream import ProtocolState

from .base import HeuristicBase


class DetectionStates(Enum):
    NO_INIT = 0
    WAITING = 1
    DETECTED = 2
    NO_DEVICE = 3


class Echo(Protocol):
    def __init__(self, target):
        super(Echo, self).__init__()
        self._target = None
        self._reactor = None

    def initialize_connection(self, reactor):
        self._reactor = reactor

    def dataReceived(self, data: bytes):
        print("Recieved: {}".format(data))


class SerialDeviceHeuristic(HeuristicBase):
    _name = "BaseSerial"
    _baud = 115200
    _width = EIGHTBITS
    _parity = PARITY_NONE
    _stop = STOPBITS_ONE

    _protocol = Echo

    def __init__(self):
        super(SerialDeviceHeuristic, self).__init__()
        self._ports = {}
        self._protocols = {}
        self._detection_states = {}
        self._detection_handlers = {}

    def cleanup(self, target):
        self._protocols[target].deregister_manager(self._state_change_handler)
        self._detection_states.pop(target)
        self._detection_handlers.pop(target)
        self._ports[target].loseConnection()
        self._ports.pop(target)

    def _dispatch_detection_result(self, target, result):
        self._detection_handlers[target].callback(result)
        self.cleanup(target)

    def _verify_device(self, target):
        self.log.info("'{device}' found on port '{target}'",
                      device=self._name, target=target)
        self._dispatch_detection_result(target, True)

    def _state_change_handler(self, target, new_state):
        if new_state == ProtocolState.BROKEN:
            self._detection_states[target] = DetectionStates.NO_DEVICE
            self.log.debug("No '{device}' found on port '{target}'",
                           device=self._name, target=target)
            self._dispatch_detection_result(target, False)
            return
        if self._detection_states[target] == DetectionStates.WAITING:
            if new_state == ProtocolState.SYNC_LOCKED:
                self._detection_states[target] = DetectionStates.DETECTED
                self._verify_device(target)

    def check_for_device(self, reactor, target):
        self._detection_states[target] = DetectionStates.NO_INIT
        self._protocols[target] = self._protocol(target)
        test_port = SerialPort(self._protocols[target], target, reactor,
                               baudrate=self._baud, bytesize=self._width,
                               parity=self._parity, stopbits=self._stop)
        self._ports[target] = test_port
        self._protocols[target].initialize_connection(reactor)
        self._protocols[target].register_manager(self._state_change_handler)
        self._detection_states[target] = DetectionStates.WAITING
        result = Deferred()
        self._detection_handlers[target] = result
        return result
