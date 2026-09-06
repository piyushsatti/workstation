# Installation passed; live desktop acceptance remains pending

- On 2026-09-05, a clean Ubuntu 26.04 amd64 container completed the real installer, a repeat installation, and the standalone verifier.
- Every pass verified the pinned packages, agent CLIs, tmux plugins and status bar, shell aliases, fonts, 50 VS Code extensions, scaffold and persisted desktop settings.
- Docker image export did not finish: Mercury ran out of disk space and Docker Desktop failed. No final image is claimed.
- The subsequently added existing-session tmux reload passes an isolated native test on Mercury. Its Linux rerun is pending; automatic approval review blocked transferring the test files to Europa.
- Europa has not received this replacement installer. GNOME activation, physical shortcuts/appearance and Docker daemon behavior still require acceptance on the target machine.

| Check | Result | Evidence |
|---|---|---|
| Fresh complete Ubuntu install | Passed, 244.1 seconds after package layer | Local log /tmp/workstation-complete-final-20260905.log, lines 6568–6581 |
| Second complete install | Passed, 21.3 seconds | Same log, lines 6689–6702 |
| Standalone verification | Passed, 12.2 seconds | Same log, lines 6705–6716 |
| Final image export | Incomplete | Same log, lines 6718–6719; Docker backend reported no space left on device |
| Latest local source | Four tests passed; ShellCheck, Ruff formatting/lint and diff checks passed | tests/test.sh, tests/test_configuration.py, tests/test_tmux_reload.py |
| Existing tmux session reload | Passed locally; Linux pending | Isolated socket and sentinel session, not the user's live server |
| Live desktop | Pending | Container persistence checks are not visual or compositor checks |

## Reproduce without risking a real home directory

Run tests/test.sh first. Review available host disk space and Docker storage before
the complete image build described in README.md. This profile downloads and builds
large dependencies; do not start another build on Mercury until its space issue is resolved.
The Dockerfile retains a recovery target and performs installation twice before verification.

The logs above are local evidence, not repository assets. Successful commands inside a
build do not imply that the image export succeeded. The exact latest source has not yet
completed a fresh full Linux build because the test environment is unavailable.

## Accept the actual workstation after installation

| Action | Required outcome |
|---|---|
| Run sudo ./bootstrap.sh from a normal Ubuntu account | No selection/removal prompts; every automated check passes |
| Open a new terminal | ll, Starship and zoxide work |
| Open or reattach tmux | Bottom Nord bar, Ctrl+Space prefix and existing sessions preserved |
| Log out and back in when convenient | Newly installed GNOME extensions and Docker group membership active |
| Press Super+Return and Super+T | Ghostty opens; Tactile grid appears |
| Inspect dock and VS Code | Bottom dock, expected appearance, Nord Code theme and selected extensions |
| Run ./verify.sh | Successful report with genuine account/endpoint actions distinguished from failures |

Authentication, private cloud data and the separate model gateway are not fabricated
by the installer. See inventory.md for every deliberate difference from the reference machines.
