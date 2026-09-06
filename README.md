# Workstation

Run this on Ubuntu 26.04 LTS from your normal user account:

```sh
sudo ./bootstrap.sh
```

That installs the complete profile. There is no TUI, Apply All, desktop flag, or
selection prompt. Sudo authenticates once; system packages run as root, and
configuration, extensions and third-party builds run as the user who invoked sudo.

The profile includes Ghostty, the Nerd Font, Voyager's tmux/plugin setup, shell
aliases and prompt, a bottom GNOME dock with Nordic/Nordzy appearance, Tactile,
the Mac's VS Code extensions/preferences adapted to Linux, Docker, development
runtimes, Claude/Codex/OpenCode, and the Studio scaffold.

[Inventory and deliberate differences](docs/inventory.md) records the actual
reference machines and anything that cannot be reproduced by installing files.
[Versions and licenses](docs/software.md) describes the pinned sources.
[Validation results and remaining acceptance checks](docs/validation.md) distinguish
the completed container runs from the pending live desktop check.
Configuration replacements are saved in ~/.local/state/workstation/TIMESTAMP/.
Editable scaffold notes and existing authenticated application configurations are preserved.

After installation, open a new terminal. A new login is needed for Docker group
membership and newly installed GNOME extensions. The installer never logs you out.
Continue requires your model endpoint; account sign-in and private data remain yours.

Verify again as your normal user:

```sh
./verify.sh
```

Every required check must pass. The detailed result is
~/.local/state/workstation/report.json, including any pending session activation.
Persisted desktop settings do not prove physical display output.

## Installation sources are explicit

| Path | Responsibility |
|---|---|
| bootstrap.sh | OS/sudo gate, pinned apt installation, user handoff, verification |
| scripts/workstation.py | User-owned tools, pinned plugins, rendered dotfiles, themes, extensions, scaffold, checks |
| profiles/ubuntu-26.04/ | Apt versions, npm lockfile, plugin commits, extension IDs/versions and download pins |
| chezmoi/ | Portable source files; rendered using Chezmoi archive |
| seed/ | Create-once notes and integration pointers |
| tests/ | Recovery tests and complete Ubuntu integration build |

Chezmoi renders this source into an archive. The installer backs up and replaces
only the declared files, avoiding an existing Chezmoi configuration's removal
prompts. VS Code settings and keybindings merge with unrelated existing values.

The old TUI, selection manifests and partial Docker recipes have been retired;
their previous versions remain in Git history.

## Verification before shipping

```sh
./tests/test.sh
docker build --platform linux/amd64 --target recovery -f tests/Dockerfile.complete -t workstation:recovery-20260905 .
docker build --platform linux/amd64 --target installed -f tests/Dockerfile.complete -t workstation:verified-20260905 .
```

The recovery image is retained before the install. The complete build executes
the real command twice, then the standalone verifier. It tests Linux userland,
not a physical GPU, running GNOME session or Docker daemon inside the container.
Use Europa for the final session-level checks. macOS support remains deferred.

## Recovery

Each run saves changed files under its recovery directory using paths relative
to your home. The original symlink is preserved if a managed file was a symlink.
To recover a particular file, inspect its backup and copy that specific entry
back. GNOME's original managed values are stored in gnome-settings.json.
Do not recursively restore the entire home directory.

Apt package changes are recorded in /var/log/apt/history.log. These file-level
recovery copies do not undo packages; use the machine backup for a full rollback.
