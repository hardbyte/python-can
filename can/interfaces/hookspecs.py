from pluggy import HookspecMarker


hookspec = HookspecMarker("pythoncan")


@hookspec
def pythoncan_interface(interface):
    """ return dict containing python-can interface info.
    The following keys are defined:
        "module" - the class implementing the interface API
        "classname" - name for selection from command line
    """