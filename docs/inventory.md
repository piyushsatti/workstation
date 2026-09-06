# The installer now follows inspected configurations

- Voyager was read over SSH on 2026-09-05. Its real tmux base file, plugin revisions, Bash initialization, dock settings, themes and Tactile layout were inspected.
- Mercury's active VS Code extension registry, settings and keyboard bindings were inspected locally.
- Europa runs Ubuntu 26.04.1 and GNOME Shell 50.1. Tactile files existed but the running shell did not recognize the extension.
- Installation has one entry point: sudo ./bootstrap.sh. There are no capability selection or deletion prompts.
- Configuration recovery copies are automatic. Package transactions are recorded by apt; configuration backups are not a full operating-system rollback.

| Capability | Previous gap | Implementation |
|---|---|---|
| tmux status bar | Tiny substitute configuration; no plugins | Voyager base configuration, explicit bottom status bar, Nord plugin and prefix highlight |
| Existing tmux server | Editing a config does not reload an already running server | Reload the current/default server, suppress startup restoration during reload, verify existing sessions survive |
| tmux navigation | Prefix and pane/window shortcuts missing | Ctrl+Space, Vim pane keys, Alt arrows, window movement, popup, SessionX, copy mode |
| tmux persistence | Resurrect/Continuum absent | Both plugins pinned to Voyager commits; save every ten minutes; restore on startup |
| tmux-thumbs | First-use interactive installer | Cargo and Rust installed, both binaries compiled with Cargo.lock before tmux starts |
| SessionX | Hidden dependencies absent | fzf, fzf-tmux, zoxide, shell utilities installed |
| Shell | ll absent, Starship installed but not initialized | eza aliases, bat/fd command wrappers, fzf previews, zoxide, Starship and login-shell initialization |
| Clipboard | Linux wrapper missing | wl-clipboard and OSC52 configuration |
| Fonts | Font name referenced, actual font absent | Checksum-verified JetBrainsMono Nerd Font 3.4.0, font cache, actual font-match verification |
| GNOME dock | Default left dock | Bottom, 48px, non-full-width, autohide/intellihide, workspace isolation and cycle-windows behavior from Voyager |
| Desktop appearance | Theme names not installed | Nordic commit from Voyager, Nordzy-dark pinned upstream revision, Inter fonts, dark preference |
| Tiling | Incomplete extension install/default grid | Tactile v37 built from pinned commit, QWE/ASD 3x2 grid, no gaps, Super+T |
| Terminal shortcut | Incorrect/missing binding | Reuse existing Super+Return binding or create one targeting Ghostty |
| VS Code | Theme setting without theme extension | Mac's pinned extension set, Nord, editor/font/formatting/Git preferences and terminal keybindings |
| Linux extension binaries | Mac platform paths | Install extension IDs and versions via Code, which selects Linux builds; derive Continue schema path from installed registry |
| CLI harnesses | None installed | Claude 2.1.261, Codex 0.153.4, OpenCode 1.18.27 with locked npm graph, installed as user |
| Runtimes | Partial prerequisites | Ubuntu Python 3.14, Node 22, uv 0.11.3, Rust/Cargo, CMake/Ninja, JDK/Maven |
| Containers | Partial Docker tooling | Docker Engine, Compose, Buildx, service enablement, user group |
| Workspace | Generic directories only | Developer/projects, Developer/agents, Studio/rules, Foundry and integration pointers, preserved editable seeds |
| Failure detection | Generic completion text | Exact package, CLI, extension, font, shell, tmux and GNOME checks; JSON report with failures and pending activation |

## Differences are deliberate and visible

| Reference difference or ambiguity | Resolution |
|---|---|
| Mac active tmux is inline Nord, while its old base file is stale Catppuccin | Use Voyager's actually sourced Nord base for Linux. Do not import the stale Mac base |
| Voyager has tmux-thumbs source but no built target/release binaries | Build both binaries in the installer instead of reproducing the reference machine's incomplete first-use state |
| Voyager hardcodes /home/piyush in the status hook | Use the target user's home |
| Voyager enables Continuum's generated systemd service | Preserve periodic save/restore, but leave automatic boot off. The upstream service can kill the whole tmux server on stop; no such service is installed implicitly |
| Mac restores tmux sessions off; Voyager has it on | Follow Voyager on Linux |
| Mac lists Remote SSH twice | Use the newer installed version, 0.128.0 |
| WSL and the Remote Development umbrella pack | Exclude WSL on Linux; install relevant remote components individually so the pack cannot bring WSL back |
| Mac Code trust/delete/paste protections disabled | Not copied. Automatic approval review rejected copying these reduced protections; unrelated existing target preferences are preserved |
| Continue model endpoint is localhost:4000 | Install Continue and preserve existing configuration; do not invent or install a model gateway |
| Voyager c launcher uses nine custom scripts and destructive session-management operations | Not imported from the old custom tooling. Claude itself is installed; launcher needs a separate explicit review |
| Voyager pyenv/fnm wrappers | Not copied: these wrappers fail without their separate managers. System runtimes plus uv work immediately; project-specific runtime selection stays explicit |
| Vitals/window-toggler/hide-minimized/unblank names appear in GNOME enabled list but extensions are absent | Treat as stale references, not a working desktop dependency |
| Nordic GTK theme versus libadwaita applications | GTK theme is installed and selected; libadwaita apps retain their supported dark appearance rather than globally replacing their CSS |
| Tailscale/SSH identities | SSH client helpers included. Tailscale client installation/enrollment remains excluded from this fixed profile; no copied private keys or machine-specific routes |
| Cloud/Claude files | Include portable appearance and scaffolds; preserve existing authenticated settings, hooks and secrets. Cloud file synchronization is not configured because no service or paths were specified |
| Memory/RAG | LanceDB pointer and small seed notes; no imported corpora or cross-project memory service |

## Verification follows the failure modes

| Layer | Method | What it proves |
|---|---|---|
| Managed files | Automated replacement, repeat-run, symlink and seed-preservation tests | Prior contents survive; unchanged files remain unchanged; external symlink targets survive |
| Linux install | Pinned Ubuntu amd64 image, complete command, repeated complete command, standalone verify | Package availability, build/install execution, selected extensions, dependencies and repeatability |
| tmux | Separate named server, persistence disabled for test | Configuration loads, actual status options and plugin-defined popup hook exist |
| Desktop settings | Read back settings through Gio/dconf | Correct target user's values persisted |
| Live GNOME | Check running extension status separately | Distinguishes installed settings from actual compositor activation |
| Physical appearance | User's desktop session | Remains a separate visual check; a container cannot verify GPU output, panel placement or physical keypresses |

Downloads have finite timeouts and retries. Stages stop on failure. A report says failed,
installed-awaiting-verification, or verified, and lists remaining account/desktop actions.

## Scope and recovery

The installer changes Ubuntu packages, the invoking user's declared configuration, plugins,
fonts, desktop preferences and scaffold. It never formats disks, moves project data, logs out
the user, copies credentials or enrolls a device into a network.
Files replaced by this installation remain under ~/.local/state/workstation/TIMESTAMP/files;
GNOME values are recorded in gnome-settings.json alongside them.

## References

- [VS Code CLI](https://code.visualstudio.com/docs/configure/command-line): extension installation by ID/version.
- [Chezmoi commands](https://www.chezmoi.io/reference/commands/): archive renders the declared source without applying unrelated removal state.
- [tmux-thumbs](https://github.com/fcsonline/tmux-thumbs): Rust build and first-use installer behavior.
- [Nordic](https://github.com/EliverLara/Nordic), [Nordzy](https://github.com/MolassesLover/Nordzy-icon): theme sources.
