from pluggy import PluginManager

from can.interfaces import hookspecs


def get_pluginmanager(load_entrypoints=True):
    pm = PluginManager("pythoncan")
    pm.add_hookspecs(hookspecs)
    # XXX load internal plugins here
    if load_entrypoints:
        pm.load_setuptools_entrypoints("python_can.interface")
    pm.check_pending()
    return pm
