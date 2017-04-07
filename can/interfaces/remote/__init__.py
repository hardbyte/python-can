from .client import RemoteBus, CyclicSendTask, CanRemoteError
from .server import RemoteServer


# If the protocol changes, increase this number
PROTOCOL_VERSION = 5

DEFAULT_PORT = 54701
