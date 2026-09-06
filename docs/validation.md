# Europa verification passed; new-session desktop acceptance remains pending

- On 2026-09-06, Europa ran the corrected user-configuration phase from commit 903aacb successfully after the user's root package installation had completed.
- The standalone verifier passed all eight groups, including Docker daemon access and explicit tmux configuration parsing.
- All five regression/recovery tests passed on Europa's Ubuntu VM, including existing-session reload and rejection of invalid tmux options.
- Existing tmux session IDs $0, $1, $2 and $4 survived; the live server reports status on and status-position bottom.
- Tactile is installed on disk but not yet recognized by the running GNOME session. Logout/login and physical shortcut/appearance acceptance remain pending.

The agent did not rerun the root package transaction: sudo requires interactive
authentication. It inspected the completed transaction, reran the full unprivileged
configuration phase and verified all pinned installed packages. The successful recovery
directory is /home/pi/.local/state/workstation/20260906-045821-j_yvihs4; the report is
/home/pi/.local/state/workstation/report.json with status verified and no failures.

## Europa exposed a missed tmux configuration error on 2026-09-06

The first real Europa installation of commit 18371f1 completed through VS Code,
scaffolding, Tactile and GNOME settings, then failed while reloading existing tmux
sessions: `invalid option: window-status-silence-style`. Its running tmux 3.6 server
does not support that inherited option. The profile now omits it.

The previous isolated check accepted successful new-session startup even when tmux
reported a configuration error. It now explicitly sources the entire configuration
and requires success. A regression test supplies an invalid option and requires the
verifier to reject it. Failure reports now retain captured command diagnostics.
The earlier container pass below did not establish error-free tmux parsing.

## Earlier container results and limits

- Historical result, 2026-09-05: a clean Ubuntu 26.04 amd64 container completed the real installer, a repeat installation, and the then-current standalone verifier.
- Every pass verified the pinned packages, agent CLIs, tmux plugins and status bar, shell aliases, fonts, 50 VS Code extensions, scaffold and persisted desktop settings.
- Docker image export did not finish: Mercury ran out of disk space and Docker Desktop failed. No final image is claimed.
- At that time, the subsequently added existing-session reload had only passed on Mercury; an isolated test transfer was blocked by approval review. Linux regression testing has since passed through the published repository on Europa.
- At that time, Europa had not received the replacement. The current Europa result is recorded above; GNOME activation and physical appearance still need acceptance.

| Check | Result | Evidence |
|---|---|---|
| Fresh complete Ubuntu install | Passed, 244.1 seconds after package layer | Local log /tmp/workstation-complete-final-20260905.log, lines 6568–6581 |
| Second complete install | Passed, 21.3 seconds | Same log, lines 6689–6702 |
| Standalone verification | Passed, 12.2 seconds | Same log, lines 6705–6716 |
| Final image export | Incomplete | Same log, lines 6718–6719; Docker backend reported no space left on device |
| Original local source | Four tests passed; ShellCheck, Ruff formatting/lint and diff checks passed | Superseded by five-test local and Europa regression runs after the parsing fix |
| Existing tmux session reload | Passed locally and on Europa after correction | Isolated regression test and actual existing server reload |
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
