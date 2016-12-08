from .client import RemoteBus, CyclicSendTask, CanRemoteError
from .server import RemoteServer


# If the protocol changes, increase this number
PROTOCOL_VERSION = 4

DEFAULT_PORT = 54701
