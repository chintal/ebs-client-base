

from serial import EIGHTBITS
from serial import PARITY_NONE
from serial import STOPBITS_ONE
from twisted.internet.serialport import SerialPort
from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import DeferredQueue

from ebs.client.protocols.stream import ProtocolState
from ebs.client.devices.base import DeviceClientBase
from ebs.client.extensions.routers import PacketRouter


class SerialDeviceClientBase(DeviceClientBase):
    _name = 'BaseSerial'
    _protocol = None
    _baud = 115200
    _width = EIGHTBITS
    _parity = PARITY_NONE
    _stop = STOPBITS_ONE

    def __init__(self, port, *args, **kwargs):
        super(SerialDeviceClientBase, self).__init__(*args, **kwargs)
        self._port = port
        self._port_obj = None
        self._protocol_instance = None
        self._frame_queue = DeferredQueue()
        self._transmit_queue = DeferredQueue()
        self._channels = {}
        self._handlers = {'on_connect': []}
        self._router = PacketRouter(self)

    def _state_change_handler(self, _, state):
        if state == ProtocolState.BROKEN:
            self.log.warn("Device {name} on port {port} "
                          "disconnected due to broken protocol",
                          name=self._name, port=self._port)
            self._disconnect()
        if state == ProtocolState.SYNC_LOCKED:
            for handler in self._handlers['on_connect']:
                handler(self)

    def install_handler(self, event, handler):
        self._handlers[event].append(handler)

    def install_channel(self, channel):
        self._channels[channel.local_name] = channel
        channel.bind_router(self._router)

    def __getattr__(self, item):
        if item in self._channels.keys():
            return self._channels[item]

    @property
    def router(self):
        return self._router

    @inlineCallbacks
    def _frame_router(self):
        while True:
            frame = yield self._frame_queue.get()
            identifier = self._protocol_instance.frame_identifier(frame)
            payload = self._protocol_instance.frame_payload(frame)
            self._router.route_packet(identifier, payload)

    def send_message(self, identifier, payload, expect_ack=True, callback=None):
        message = self._protocol_instance.frame_builder(identifier, payload)
        self._transmit_queue.put((message, expect_ack, callback))

    def _connect(self):
        self.log.info("Connecting to Device '{name}' on port '{port}'",
                      name=self._name, port=self._port)
        self._protocol_instance = self._protocol(self._port)
        conn_port = SerialPort(self._protocol_instance, self._port, self.reactor,
                               baudrate=self._baud, bytesize=self._width,
                               parity=self._parity, stopbits=self._stop)
        self._port_obj = conn_port
        self._protocol_instance.initialize_connection(self.reactor)
        self._protocol_instance.bind_transmitter(self._transmit_queue)
        self._protocol_instance.register_manager(self._state_change_handler)
        self._protocol_instance.register_customer(self._frame_queue)
        self._frame_router()

    def cleanup(self):
        self._protocol.deregister_manager(self._state_change_handler)
        self._protocol.deregister_customer(self._frame_router)
        self._port_obj.loseConnection()

    def _disconnect(self):
        self.cleanup()
