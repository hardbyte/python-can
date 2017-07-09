import logging
import can
from .protocol import RemoteProtocolBase, RemoteError
from .websocket import WebSocket, WebsocketClosed


logger = logging.getLogger(__name__)


class RemoteBus(can.bus.BusABC):
    """CAN bus over a network connection bridge."""

    def __init__(self, channel, **config):
        """
        :param str channel:
            Address of server as ws://host:port/path.
        """
        url = channel if "://" in channel else "ws://" + channel
        websocket = WebSocket(url, ["can.binary+json.v1", "can.json.v1"])
        self.socket = websocket.socket
        self.protocol = RemoteClientProtocol(config, websocket)
        self.channel_info = self.protocol.channel_info
        self.channel = channel

    def recv(self, timeout=None):
        """Block waiting for a message from the Bus.

        :param float timeout: Seconds to wait for a message.

        :return:
            None on timeout or a Message object.
        :rtype: can.Message
        :raises can.interfaces.remote.protocol.RemoteError:
        """
        event = self.protocol.recv(timeout)
        if isinstance(event, can.Message):
            return event
        return None

    def send(self, msg, timeout=None):
        """Transmit a message to CAN bus.

        :param can.Message msg: A Message object.
        """
        self.protocol.send_msg(msg)

    def send_periodic(self, message, period, duration=None):
        """Start sending a message at a given period on the remote bus.

        :param can.Message msg:
            Message to transmit
        :param float period:
            Period in seconds between each message
        :param float duration:
            The duration to keep sending this message at given rate. If
            no duration is provided, the task will continue indefinitely.

        :return: A started task instance
        """
        return CyclicSendTask(self, message, period, duration)

    def shutdown(self):
        """Close socket connection."""
        # Give threads a chance to finish up
        logger.debug('Closing connection to server')
        self.protocol.close()
        while True:
            try:
                self.protocol.recv(1)
            except WebsocketClosed:
                break
            except RemoteError:
                pass
        self.socket.close()
        logger.debug('Network connection closed')


class RemoteClientProtocol(RemoteProtocolBase):

    def __init__(self, config, websocket):
        super(RemoteClientProtocol, self).__init__(websocket)
        self.send_bus_request(config)
        event = self.recv(5)
        if event is None:
            raise RemoteError("No response from server")
        if event.get("type") != "bus_response":
            raise RemoteError("Invalid response from server")
        self.channel_info = '%s on %s' % (
            event["payload"]["channel_info"], websocket.url)

    def send_bus_request(self, config):
        self.send("bus_request", {"config": config})

    def send_periodic_start(self, msg, period, duration):
        msg_payload = {
            "arbitration_id": msg.arbitration_id,
            "extended_id": msg.id_type,
            "is_remote_frame": msg.is_remote_frame,
            "is_error_frame": msg.is_error_frame,
            "dlc": msg.dlc,
            "data": list(msg.data),
        }
        payload = {
            "period": period,
            "duration": duration,
            "msg": msg_payload
        }
        self.send("periodic_start", payload)

    def send_periodic_stop(self, arbitration_id):
        self.send("periodic_stop", arbitration_id)


class CyclicSendTask(can.broadcastmanager.LimitedDurationCyclicSendTaskABC,
                     can.broadcastmanager.RestartableCyclicTaskABC,
                     can.broadcastmanager.ModifiableCyclicTaskABC):

    def __init__(self, bus, message, period, duration=None):
        """
        :param bus: The remote connection to use.
        :param message: The message to be sent periodically.
        :param period: The rate in seconds at which to send the message.
        """
        self.bus = bus
        super(CyclicSendTask, self).__init__(message, period, duration)
        self.start()

    def start(self):
        self.bus.protocol.send_periodic_start(self.message,
                                              self.period,
                                              self.duration)

    def stop(self):
        self.bus.protocol.send_periodic_stop(self.message.arbitration_id)

    def modify_data(self, message):
        assert message.arbitration_id == self.message.arbitration_id
        self.message = message
        self.bus.protocol.send_periodic_start(self.message,
                                              self.period,
                                              self.duration)
