Fix script command tests by invoking module entry points with
``sys.executable`` and console entry points from the active Python environment
instead of relying on PATH resolution.
