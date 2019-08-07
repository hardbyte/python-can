r"""dg_gryphon_protocol is an implemenation of the Gryphon Protocol
for Python.

Usage:
    >>> import dg_gryphon_protocol
    >>> server = dg_gryphon_protocol.server_commands.Gryphon("localhost")
    >>> reply_dict = server.CMD_SERVER_REG("root", "dgbeacon")
    >>> reply_dict = server.CMD_GET_CONFIG()
    >>> delete server
"""
__version__ = '1.1 of 20190731'
__author__ = 'markc <markc@dgtech.com>'
__servercommands__ = ["Gryphon", "BEACON"]
__genericcommands__ = [""]
