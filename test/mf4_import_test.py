"""Check optional MF4 imports in fresh interpreters."""

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


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
    def test_both_import_orders(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "messages.mf4")
            self.run_script(f"""
                import can
                with can.MF4Writer({path!r}) as writer:
                    writer(can.Message(timestamp=1, arbitration_id=0x123,
                                       is_extended_id=False, data=b'\\x01\\x02'))
            """)
            for imports, circular_import in (
                ("import asammdf; import can", False),
                ("import can; import asammdf", False),
                ("import asammdf; import can", True),
            ):
                for operation in ("read", "write"):
                    with self.subTest(
                        imports=imports,
                        operation=operation,
                        circular_import=circular_import,
                    ):
                        self.run_script(
                            f"""
                            {imports}
                            if {operation!r} == "read":
                                with can.MF4Reader({path!r}) as reader:
                                    messages = list(reader)
                                assert len(messages) == 1
                                assert messages[0].arbitration_id == 0x123
                                assert messages[0].data == b'\\x01\\x02'
                            else:
                                from io import BytesIO
                                with can.MF4Writer(BytesIO()) as writer:
                                    writer(can.Message(arbitration_id=0x456,
                                                       is_extended_id=False, data=b'\\x03'))
                        """,
                            circular_import=circular_import,
                        )

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
