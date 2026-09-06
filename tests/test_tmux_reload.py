"""Exercise the real reload function against an isolated tmux server."""

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "workstation", Path(__file__).resolve().parents[1] / "scripts/workstation.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(shutil.which("tmux"), "tmux is needed for the integration check")
class TmuxReloadTest(unittest.TestCase):
    def test_verifier_rejects_startup_configuration_errors(self):
        with tempfile.TemporaryDirectory(prefix="workstation-invalid-config-") as temp:
            previous_home = MODULE.HOME
            MODULE.HOME = Path(temp)
            (MODULE.HOME / ".tmux.base.conf").write_text(
                "set -g workstation-deliberately-invalid-option none\n"
            )
            try:
                with self.assertRaises(subprocess.CalledProcessError) as caught:
                    MODULE.verify_tmux()
                self.assertIn("invalid option", caught.exception.stderr)
            finally:
                MODULE.HOME = previous_home

    def test_live_session_survives_and_configuration_is_reloaded(self):
        with tempfile.TemporaryDirectory(prefix="workstation-reload-") as temp:
            root = Path(temp)
            socket = str(root / "socket")
            previous_tmux = os.environ.get("TMUX")
            previous_home = MODULE.HOME
            MODULE.HOME = root
            (root / ".tmux.conf").write_text(
                "set -g status-right WORKSTATION_RELOAD_TEST\n"
                "set -g status-position bottom\n"
                "set -g @observed-restore-delay '#{@continuum-restore-max-delay}'\n"
            )
            subprocess.run(
                [
                    "tmux",
                    "-S",
                    socket,
                    "-f",
                    "/dev/null",
                    "new-session",
                    "-d",
                    "-s",
                    "sentinel",
                    "sleep 60",
                ],
                check=True,
            )
            os.environ["TMUX"] = f"{socket},0,0"
            try:
                MODULE.reload_tmux()
                subprocess.run(["tmux", "has-session", "-t", "sentinel"], check=True)
                value = subprocess.check_output(
                    ["tmux", "show-option", "-gv", "status-right"], text=True
                ).strip()
                self.assertEqual(value, "WORKSTATION_RELOAD_TEST")
                delay = subprocess.check_output(
                    ["tmux", "show-option", "-gqv", "@continuum-restore-max-delay"],
                    text=True,
                ).strip()
                self.assertEqual(delay, "")
            finally:
                subprocess.run(["tmux", "-S", socket, "kill-server"], check=False)
                MODULE.HOME = previous_home
                if previous_tmux is None:
                    os.environ.pop("TMUX", None)
                else:
                    os.environ["TMUX"] = previous_tmux


if __name__ == "__main__":
    unittest.main()
