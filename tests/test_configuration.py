"""Recovery and repeat-run behavior for the files the installer manages."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "workstation", Path(__file__).resolve().parents[1] / "scripts/workstation.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        MODULE.HOME = Path(self.temp.name)
        MODULE.RUN = MODULE.HOME / "recovery"
        MODULE.RUN.mkdir()

    def test_replacement_retains_original_and_repeat_run_is_unchanged(self):
        target = MODULE.HOME / ".tmux.conf"
        target.write_text("old config")
        MODULE.write(target, "new config")
        stamp = target.stat().st_mtime_ns
        MODULE.write(target, "new config")
        self.assertEqual(target.stat().st_mtime_ns, stamp)
        self.assertEqual((MODULE.RUN / "files/.tmux.conf").read_text(), "old config")

    def test_seed_preserves_existing_notes(self):
        target = MODULE.HOME / "notes.md"
        target.write_text("my edited notes")
        MODULE.write(target, "default notes", seed=True)
        self.assertEqual(target.read_text(), "my edited notes")

    def test_symlink_target_is_not_overwritten(self):
        original = MODULE.HOME / "other.conf"
        original.write_text("outside managed configuration")
        target = MODULE.HOME / ".tmux.conf"
        target.symlink_to(original)
        MODULE.write(target, "new config")
        self.assertEqual(original.read_text(), "outside managed configuration")
        self.assertFalse(target.is_symlink())
        self.assertTrue((MODULE.RUN / "files/.tmux.conf").is_symlink())


if __name__ == "__main__":
    unittest.main()
