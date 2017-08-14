from pluggy import HookspecMarker


hookspec = HookspecMarker("pythoncan")


@hookspec
def pythoncan_interface(interface):
    """ return tuple (module, classname) containing python-can interface info
    for the interface if supported by this implementation
    """
