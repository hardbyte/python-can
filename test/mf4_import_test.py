"""Check optional MF4 imports in fresh interpreters."""

import importlib.util
import subprocess
import sys
import textwrap
import unittest


class MF4ImportTest(unittest.TestCase):
    def run_script(self, script, *, circular_import=False):
        script = textwrap.dedent(script)
        if circular_import:
            script = textwrap.dedent("""
                import importlib.abc
                import importlib.machinery
                import sys

                class CircularLoader(importlib.abc.Loader):
                    def __init__(self, loader):
                        self.loader = loader

                    def create_module(self, spec):
                        return None

                    def exec_module(self, module):
                        import can
                        self.loader.exec_module(module)

                class CircularAsammdf(importlib.abc.MetaPathFinder):
                    def find_spec(self, fullname, path=None, target=None):
                        if fullname == "asammdf":
                            spec = importlib.machinery.PathFinder.find_spec(fullname, path)
                            spec.loader = CircularLoader(spec.loader)
                            return spec

                sys.meta_path.insert(0, CircularAsammdf())
            """) + script
        result = subprocess.run(
            [sys.executable, "-c", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(importlib.util.find_spec("asammdf"), "MF4 is unavailable")
    def test_circular_import_reader_and_writer(self):
        # One fresh interpreter reproduces the re-entrant import and exercises
        # both directions of MF4 I/O, avoiding redundant plain-import probes.
        self.run_script("""
            import asammdf
            import can
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "messages.mf4"
                with can.MF4Writer(path) as writer:
                    writer(can.Message(timestamp=1, arbitration_id=0x123,
                                       is_extended_id=False, data=b'\\x01\\x02'))
                with can.MF4Reader(path) as reader:
                    messages = list(reader)
                assert len(messages) == 1
                assert messages[0].arbitration_id == 0x123
                assert messages[0].data == b'\\x01\\x02'
        """, circular_import=True)

    def test_missing_dependency_does_not_open_files(self):
        self.run_script("""
            import importlib.abc
            import sys
            from unittest.mock import patch

            class MissingAsammdf(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname == "asammdf":
                        raise ModuleNotFoundError("asammdf unavailable", name="asammdf")

            sys.meta_path.insert(0, MissingAsammdf())
            import can
            for cls in (can.MF4Reader, can.MF4Writer):
                with patch("builtins.open") as opened:
                    try:
                        cls("must-not-open.mf4")
                    except NotImplementedError as exc:
                        assert "optional dependency [mf4]" in str(exc)
                        assert cls.__name__ in str(exc)
                    else:
                        raise AssertionError("missing dependency was accepted")
                    opened.assert_not_called()
        """)

    def test_broken_dependency_keeps_original_error(self):
        self.run_script("""
            import importlib.abc
            import sys

            class BrokenAsammdf(importlib.abc.MetaPathFinder):
                def find_spec(self, fullname, path=None, target=None):
                    if fullname == "asammdf":
                        raise ModuleNotFoundError(
                            "missing transitive dependency", name="missing_child"
                        )

            sys.meta_path.insert(0, BrokenAsammdf())
            import can
            for cls in (can.MF4Reader, can.MF4Writer):
                try:
                    cls("must-not-open.mf4")
                except ModuleNotFoundError as exc:
                    assert exc.name == "missing_child"
                else:
                    raise AssertionError("original dependency error was hidden")
        """)
