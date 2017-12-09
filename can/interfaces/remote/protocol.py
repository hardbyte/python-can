import logging
import json
import struct
from can import CanError, Message

from .websocket import WebSocket, WebsocketClosed


LOGGER = logging.getLogger(__name__)

# Timestamp, arbitration ID, DLC, flags
BINARY_MSG_STRUCT = struct.Struct(">dIBB")
BINARY_MESSAGE_TYPE = 1


class RemoteProtocolBase(object):

    def __init__(self, websocket):
        self._ws = websocket
        self._use_binary = websocket.protocol == "can.binary+json.v1"

    def recv(self, timeout=None):
        try:
            if not self._ws.wait(timeout):
                return None
            data = self._ws.read()
            if isinstance(data, bytearray):
                if data[0] == BINARY_MESSAGE_TYPE:
                    timestamp, arb_id, dlc, flags = \
                        BINARY_MSG_STRUCT.unpack_from(data, 1)
                    return Message(timestamp=timestamp,
                                   arbitration_id=arb_id,
                                   dlc=dlc,
                                   extended_id=bool(flags & 0x1),
                                   is_remote_frame=bool(flags & 0x2),
                                   is_error_frame=bool(flags & 0x4),
                                   data=data[15:])
                else:
                    return None
            event = json.loads(data)
            if not isinstance(event, dict):
                raise TypeError("Message is not a dictionary")
            if "type" not in event:
                raise ValueError("Message must contain a 'type' key")
            if event["type"] == "error":
                raise RemoteError(event["payload"])
            if event["type"] == "message":
                return Message(**event["payload"])
        except (ValueError, TypeError, KeyError) as exc:
            LOGGER.warning("An error occurred: %s", exc)
            self.send_error(exc)
            return None
        return event

    def send(self, event_type, payload):
        self._ws.send(json.dumps({"type": event_type, "payload": payload}))

    def send_msg(self, msg):
        if self._use_binary:
            flags = 0
            if msg.id_type:
                flags |= 0x1
            if msg.is_remote_frame:
                flags |= 0x2
            if msg.is_error_frame:
                flags |= 0x4
            data = BINARY_MSG_STRUCT.pack(msg.timestamp,
                                          msg.arbitration_id,
                                          msg.dlc,
                                          flags)
            payload = bytearray([BINARY_MESSAGE_TYPE])
            payload.extend(data)
            payload.extend(msg.data)
            self._ws.send(payload)
        else:
            payload = {
                "timestamp": msg.timestamp,
                "arbitration_id": msg.arbitration_id,
                "extended_id": msg.id_type,
                "is_remote_frame": msg.is_remote_frame,
                "is_error_frame": msg.is_error_frame,
                "dlc": msg.dlc,
                "data": list(msg.data),
            }
            self.send("message", payload)

    def send_error(self, exc):
        self.send("error", str(exc))

    def close(self):
        self._ws.close()

    def terminate(self, exc):
        self._ws.close(1011, str(exc))


class RemoteError(CanError):
    pass
