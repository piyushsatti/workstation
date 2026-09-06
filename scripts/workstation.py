"""Unprivileged workstation installation and verification.

The root launcher installs system packages, then runs this as SUDO_USER.
Only explicitly managed files are replaced; their old contents are recoverable.
"""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles/ubuntu-26.04"
HOME = Path.home()
STATE = HOME / ".local/state/workstation"
DATA = HOME / ".local/share/workstation"
VERSIONS = json.loads((PROFILE / "versions.json").read_text())
PLUGINS = json.loads((PROFILE / "plugins.json").read_text())
EXTENSIONS = json.loads((PROFILE / "extensions.json").read_text())
RUN = None
REPORT = {"status": "running", "stages": [], "pending": [], "failed": []}


def run(*args, cwd=None, capture=False, timeout=300, env=None):
    return subprocess.run(
        [str(a) for a in args],
        cwd=cwd,
        env=env,
        check=True,
        timeout=timeout,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    ).stdout


def save_report():
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / "report.json"
    path.write_text(json.dumps(REPORT, indent=2) + "\n")
    path.chmod(0o600)


def stage(name, action):
    print(f"\n[{name}]", flush=True)
    REPORT["current_stage"] = name
    save_report()
    action()
    REPORT["stages"].append(name)
    save_report()


def backup(path):
    """Copy exactly one managed entry, retaining symlinks as symlinks."""
    if not path.exists() and not path.is_symlink():
        return
    if RUN is None:
        raise RuntimeError("Recovery directory is not initialized")
    dest = RUN / "files" / path.relative_to(HOME)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.copytree(path, dest, symlinks=True)
    else:
        shutil.copy2(path, dest, follow_symlinks=False)


def write(path, content, mode=0o644, seed=False):
    if not path.parent.resolve().is_relative_to(HOME.resolve()):
        raise RuntimeError(f"Managed parent resolves outside the target home: {path}")
    if seed and (path.exists() or path.is_symlink()):
        return
    payload = content.encode() if isinstance(content, str) else content
    if path.is_file() and not path.is_symlink() and path.read_bytes() == payload:
        return
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".workstation-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def install_tree(source, target, revision):
    if not target.parent.resolve().is_relative_to(HOME.resolve()):
        raise RuntimeError(f"Managed parent resolves outside the target home: {target}")
    marker = target / ".workstation-revision"
    if marker.is_file() and marker.read_text().strip() == revision:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        dest = RUN / "files" / target.relative_to(HOME)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() or dest.is_symlink():
            raise RuntimeError(f"Recovery collision at {dest}")
        target.rename(dest)
    shutil.copytree(
        source, target, symlinks=True, ignore=shutil.ignore_patterns(".git")
    )
    marker.write_text(revision + "\n")


def download(url, target, checksum=None):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        temp = target.with_suffix(target.suffix + ".part")
        run(
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--retry",
            "3",
            "--connect-timeout",
            "20",
            "--max-time",
            "300",
            url,
            "--output",
            temp,
            timeout=1000,
        )
        temp.rename(target)
    if checksum and hashlib.sha256(target.read_bytes()).hexdigest() != checksum:
        raise RuntimeError(f"Checksum mismatch: {target}")
    return target


def checkout(name, url, commit):
    target = DATA / "sources" / name / commit
    if (target / ".git").exists():
        if run("git", "rev-parse", "HEAD", cwd=target, capture=True).strip() != commit:
            raise RuntimeError(f"Unexpected revision: {target}")
        if run(
            "git",
            "status",
            "--porcelain",
            "--untracked-files=no",
            cwd=target,
            capture=True,
        ):
            raise RuntimeError(f"Modified pinned source: {target}")
        return target
    target.mkdir(parents=True, exist_ok=True)
    run("git", "init", "--quiet", target)
    run("git", "fetch", "--quiet", "--depth=1", url, commit, cwd=target)
    run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=target)
    if run("git", "rev-parse", "HEAD", cwd=target, capture=True).strip() != commit:
        raise RuntimeError(f"Upstream revision mismatch: {name}")
    return target


def tools():
    architecture = {"x86_64": "amd64", "aarch64": "arm64"}[os.uname().machine]
    version = VERSIONS["chezmoi"]
    asset = f"chezmoi_{version}_linux_{architecture}.tar.gz"
    url = f"https://github.com/twpayne/chezmoi/releases/download/v{version}"
    sums = download(
        f"{url}/chezmoi_{version}_checksums.txt",
        DATA / "cache" / f"chezmoi-{version}.sha256",
    )
    checksum = next(
        line.split()[0]
        for line in sums.read_text().splitlines()
        if line.split()[-1].lstrip("*") == asset
    )
    archive = download(f"{url}/{asset}", DATA / "cache" / asset, checksum)
    with tarfile.open(archive) as tar:
        write(HOME / ".local/bin/chezmoi", tar.extractfile("chezmoi").read(), 0o755)

    npm_dir = DATA / "npm"
    npm_dir.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copy2(PROFILE / "npm" / name, npm_dir / name)
    lock_hash = hashlib.sha256((npm_dir / "package-lock.json").read_bytes()).hexdigest()
    marker = npm_dir / ".installed"
    binaries = [
        npm_dir / "node_modules/.bin" / name for name in ("claude", "codex", "opencode")
    ]
    if (
        not marker.exists()
        or marker.read_text().strip() != lock_hash
        or not all(p.exists() for p in binaries)
    ):
        # Native-package postinstall scripts run only as the workstation user.
        run("npm", "ci", "--no-audit", "--no-fund", cwd=npm_dir, timeout=900)
        marker.write_text(lock_hash + "\n")
    for binary in ("claude", "codex", "opencode"):
        target = npm_dir / "node_modules/.bin" / binary
        if not target.exists():
            raise RuntimeError(f"Missing installed CLI: {binary}")
        write(HOME / ".local/bin" / binary, f'#!/bin/sh\nexec "{target}" "$@"\n', 0o755)
    uv = HOME / ".local/bin/uv"
    if not uv.exists():
        run("pipx", "install", f"uv=={VERSIONS['uv']}", timeout=600)
    elif VERSIONS["uv"] not in run(uv, "--version", capture=True):
        raise RuntimeError(
            "Existing uv differs from the pinned profile; preserve it and report the conflict"
        )
    for name, command in (("fd", "fdfind"), ("bat", "batcat")):
        write(
            HOME / ".local/bin" / name,
            f'#!/bin/sh\nexec /usr/bin/{command} "$@"\n',
            0o755,
        )


def plugins():
    for plugin in PLUGINS:
        source = checkout(
            plugin["name"], f"https://github.com/{plugin['repo']}.git", plugin["commit"]
        )
        if (
            plugin["name"] == "tmux-thumbs"
            and not (source / "target/release/tmux-thumbs").exists()
        ):
            run("cargo", "build", "--release", "--locked", cwd=source, timeout=1200)
        install_tree(source, HOME / ".tmux/plugins" / plugin["name"], plugin["commit"])


def fonts_and_themes():
    version = VERSIONS["fontVersion"]
    archive = download(
        f"https://github.com/ryanoasis/nerd-fonts/releases/download/v{version}/JetBrainsMono.tar.xz",
        DATA / "cache" / f"JetBrainsMono-{version}.tar.xz",
        VERSIONS["fontSha256"],
    )
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if member.isfile() and (
                member.name.endswith(".ttf")
                or Path(member.name).name.startswith(("OFL", "LICENSE"))
            ):
                write(
                    HOME / ".local/share/fonts/JetBrainsMono" / Path(member.name).name,
                    tar.extractfile(member).read(),
                )
    run("fc-cache", HOME / ".local/share/fonts")
    nordic = checkout(
        "Nordic", "https://github.com/EliverLara/Nordic.git", VERSIONS["nordic"]
    )
    install_tree(nordic, HOME / ".themes/Nordic", VERSIONS["nordic"])
    nordzy = checkout(
        "Nordzy", "https://github.com/MolassesLover/Nordzy-icon.git", VERSIONS["nordzy"]
    )
    icon_target = HOME / ".local/share/icons/Nordzy-dark"
    marker = icon_target / ".workstation-revision"
    if not marker.exists() or marker.read_text().strip() != VERSIONS["nordzy"]:
        # Upstream can remove its destination. Give it only a fresh temporary directory.
        with tempfile.TemporaryDirectory(prefix="workstation-icons-") as temp:
            run("bash", "install.sh", "-c", "dark", "-d", temp, cwd=nordzy)
            install_tree(Path(temp) / "Nordzy-dark", icon_target, VERSIONS["nordzy"])


def config():
    import json5

    # Render only this repo's source; do not share another chezmoi source's removal state.
    archive = subprocess.run(
        [
            str(HOME / ".local/bin/chezmoi"),
            "--source",
            str(ROOT / "chezmoi"),
            "--destination",
            str(HOME),
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "archive",
        ],
        check=True,
        stdout=subprocess.PIPE,
        timeout=120,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for member in tar.getmembers():
            rel = Path(member.name)
            if rel.is_absolute() or ".." in rel.parts or not member.isfile():
                if member.isdir():
                    continue
                raise RuntimeError(f"Unexpected rendered entry: {member.name}")
            target = HOME / rel
            contents = tar.extractfile(member).read()
            if rel.name == "settings.json" and target.exists():
                existing = json5.loads(target.read_text())
                existing.update(json.loads(contents))
                contents = (json.dumps(existing, indent=2) + "\n").encode()
            if rel.name == "keybindings.json" and target.exists():
                desired = json.loads(contents)
                keys = {(x["key"], x.get("when")) for x in desired}
                existing = [
                    x
                    for x in json5.loads(target.read_text())
                    if (x.get("key"), x.get("when")) not in keys
                ]
                contents = (json.dumps(existing + desired, indent=2) + "\n").encode()
            write(target, contents, member.mode & 0o777)
    # Safe appearance seeds, without copying authenticated sessions, hooks, or plugins.
    write(
        HOME / ".claude/settings.json",
        '{"theme":"dark-ansi"}\n',
        0o600,
        seed=True,
    )
    write(
        HOME / ".config/opencode/opencode.json",
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "permission": {
                    "*": "deny",
                    "read": "allow",
                    "glob": "allow",
                    "grep": "allow",
                },
            },
            indent=2,
        )
        + "\n",
        0o600,
        seed=True,
    )


def vscode():
    # Install explicit dependencies first, preventing Code from choosing a newer
    # transitive version before our pinned version is installed.
    by_id = {item["id"].lower(): item for item in EXTENSIONS}
    ordered = []
    visited = set()
    visiting = set()

    def visit(item):
        key = item["id"].lower()
        if key in visited:
            return
        if key in visiting:
            raise RuntimeError(f"Circular extension dependency: {key}")
        visiting.add(key)
        for dependency in item.get("dependencies", []):
            if dependency.lower() in by_id:
                visit(by_id[dependency.lower()])
        visiting.remove(key)
        visited.add(key)
        ordered.append(item)

    for item in EXTENSIONS:
        visit(item)
    installed = set(
        run("code", "--list-extensions", "--show-versions", capture=True)
        .lower()
        .splitlines()
    )
    for extension in ordered:
        spec = f"{extension['id']}@{extension['version']}"
        if spec.lower() not in installed:
            run(
                "code",
                "--install-extension",
                spec,
                "--do-not-include-pack-dependencies",
                timeout=300,
            )
    # Continue's schema path must reference the installed Linux extension, not Mac's path.
    import json5

    manifest = HOME / ".vscode/extensions/extensions.json"
    items = json.loads(manifest.read_text())
    continuation = next(
        x for x in items if x["identifier"]["id"].lower() == "continue.continue"
    )
    location = continuation.get("relativeLocation")
    if location:
        schema = HOME / ".vscode/extensions" / location / "config-yaml-schema.json"
        if schema.is_file():
            path = HOME / ".config/Code/User/settings.json"
            settings = json5.loads(path.read_text())
            schemas = settings.setdefault("yaml.schemas", {})
            for key in list(schemas):
                if "/Users/piyushsatti/" in key and "continue" in key:
                    del schemas[key]
            schemas[schema.as_uri()] = [".continue/**/*.yaml"]
            write(path, json.dumps(settings, indent=2) + "\n")


def scaffold():
    studio = HOME / "Studio"
    for rel in (
        "Developer/projects",
        "Developer/agents",
        "Projects",
        "memory",
        "rules",
        ".bootstrap",
    ):
        (studio / rel).mkdir(parents=True, exist_ok=True)
    seeds = {
        "workspace-principles.md": "memory/workspace-principles.md",
        "project-structure.md": "memory/project-structure.md",
        "rules/README.md": "rules/README.md",
        "rules/foundry.md": "rules/foundry.md",
        "bootstrap-context.md": ".bootstrap/context.md",
        "integrations.md": "rules/integrations.md",
    }
    for source, target in seeds.items():
        write(studio / target, (ROOT / "seed" / source).read_bytes(), seed=True)


DESKTOP = {
    "org.gnome.desktop.interface": {
        "color-scheme": "'prefer-dark'",
        "gtk-theme": "'Nordic'",
        "icon-theme": "'Nordzy-dark'",
        "font-name": "'Inter 11'",
        "document-font-name": "'Inter Variable 11'",
        "monospace-font-name": "'JetBrains Mono 13'",
        "clock-format": "'12h'",
        "clock-show-date": "true",
        "clock-show-weekday": "true",
        "accent-color": "'green'",
    },
    "org.gnome.shell.extensions.dash-to-dock": {
        "dock-position": "'BOTTOM'",
        "dock-fixed": "false",
        "extend-height": "false",
        "dash-max-icon-size": "48",
        "autohide": "true",
        "intellihide": "true",
        "intellihide-mode": "'FOCUS_APPLICATION_WINDOWS'",
        "isolate-workspaces": "true",
        "click-action": "'cycle-windows'",
        "hot-keys": "false",
        "show-apps-at-top": "false",
    },
    "org.gnome.shell.extensions.tactile": {
        "show-tiles": "['<Super>t']",
        "show-settings": "['<Super><Shift>t']",
        "col-0": "1",
        "col-1": "1",
        "col-2": "1",
        "col-3": "0",
        "col-4": "0",
        "col-5": "0",
        "col-6": "0",
        "row-0": "1",
        "row-1": "1",
        "row-2": "0",
        "row-3": "0",
        "row-4": "0",
        "gap-size": "0",
        "maximize": "true",
        "tile-0-0": "['q']",
        "tile-1-0": "['w']",
        "tile-2-0": "['e']",
        "tile-0-1": "['a']",
        "tile-1-1": "['s']",
        "tile-2-1": "['d']",
    },
}
TACTILE = HOME / ".local/share/gnome-shell/extensions/tactile@lundal.io"


def tactile():
    source = checkout(
        "tactile", "https://gitlab.com/lundal/tactile.git", VERSIONS["tactile"]
    )
    if not (source / "build/extension.js").exists():
        run(
            "npm",
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
            cwd=source,
            timeout=600,
        )
        run("npm", "run", "check", cwd=source)
        run("npm", "run", "build", cwd=source)
    run("glib-compile-schemas", source / "build/schemas")
    install_tree(source / "build", TACTILE, VERSIONS["tactile"])


def desktop_settings(check=False):
    from gi.repository import Gio, GLib

    schemas = Gio.SettingsSchemaSource.new_from_directory(
        str(TACTILE / "schemas"), Gio.SettingsSchemaSource.get_default(), False
    )

    def settings(name, path=None):
        schema = schemas.lookup(name, True)
        if not schema:
            raise RuntimeError(f"Missing GNOME schema: {name}")
        return Gio.Settings.new_full(schema, None, path)

    originals = {}

    def record_originals():
        # Persist before each mutation so even a partially failed stage is recoverable.
        (RUN / "gnome-settings.json").write_text(json.dumps(originals, indent=2) + "\n")

    for schema, values in DESKTOP.items():
        obj = settings(schema)
        for key, text in values.items():
            expected = GLib.Variant.parse(None, text, None, None)
            if check:
                if obj.get_value(key) != expected:
                    raise RuntimeError(f"GNOME setting mismatch: {schema} {key}")
            else:
                originals[f"{schema}/{key}"] = obj.get_value(key).print_(True)
                record_originals()
                if not obj.set_value(key, expected):
                    raise RuntimeError(f"Cannot set {schema} {key}")
    media = settings("org.gnome.settings-daemon.plugins.media-keys")
    path = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/workstation-terminal/"
    paths = list(media.get_strv("custom-keybindings"))
    originals["custom-keybindings"] = paths.copy()
    # Reuse an existing Super+Return binding, preserving unrelated shortcuts.
    for candidate in paths:
        obj = settings(
            "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding", candidate
        )
        if obj.get_string("binding").lower() == "<super>return":
            path = candidate
            break
    binding = settings(
        "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding", path
    )
    if check:
        if (
            path not in paths
            or binding.get_string("command") != "ghostty"
            or binding.get_string("binding") != "<Super>Return"
        ):
            raise RuntimeError("Super+Return is not bound to Ghostty")
    else:
        originals["terminal-path"] = path
        originals["terminal"] = {
            key: binding.get_string(key) for key in ("name", "command", "binding")
        }
        record_originals()
        if path not in paths:
            paths.append(path)
        media.set_strv("custom-keybindings", paths)
        for key, value in {
            "name": "Ghostty terminal",
            "command": "ghostty",
            "binding": "<Super>Return",
        }.items():
            binding.set_string(key, value)
    shell = settings("org.gnome.shell")
    enabled = list(shell.get_strv("enabled-extensions"))
    required = ["ubuntu-dock@ubuntu.com", "tactile@lundal.io"]
    if check:
        if not all(x in enabled for x in required):
            raise RuntimeError("Dock or Tactile is not enabled in GNOME preferences")
    else:
        originals["enabled-extensions"] = enabled.copy()
        originals["disable-user-extensions"] = shell.get_boolean(
            "disable-user-extensions"
        )
        record_originals()
        shell.set_boolean("disable-user-extensions", False)
        shell.set_strv(
            "enabled-extensions", enabled + [x for x in required if x not in enabled]
        )
        (RUN / "gnome-settings.json").write_text(json.dumps(originals, indent=2) + "\n")
        Gio.Settings.sync()


def desktop(check=False):
    if Path(f"/run/user/{os.getuid()}/bus").exists():
        desktop_settings(check)
    else:
        env = os.environ.copy()
        if RUN:
            env["WORKSTATION_RECOVERY"] = str(RUN)
        with tempfile.TemporaryDirectory(prefix="workstation-runtime-") as runtime:
            env["XDG_RUNTIME_DIR"] = runtime
            run(
                "dbus-run-session",
                "--",
                sys.executable,
                __file__,
                "desktop-check" if check else "desktop",
                env=env,
            )


def verify_tmux():
    # A separate server with persistence disabled cannot restore or stop real sessions.
    name = f"workstation-check-{os.getpid()}"
    config_text = (
        (HOME / ".tmux.base.conf")
        .read_text()
        .replace("set -g @continuum-restore 'on'", "set -g @continuum-restore 'off'")
    )
    with tempfile.TemporaryDirectory(prefix="workstation-tmux-") as temp:
        path = Path(temp) / "tmux.conf"
        path.write_text(config_text + "\nset -s copy-command 'wl-copy'\n")
        try:
            run(
                "tmux",
                "-L",
                name,
                "-f",
                path,
                "new-session",
                "-d",
                "-s",
                "verify",
                "sleep 60",
                capture=True,
            )
            # Startup can report config errors without failing new-session. Explicit
            # sourcing must succeed, just as it must when reloading a live server.
            run("tmux", "-L", name, "source-file", path, capture=True)
            for option, value in (
                ("status", "on"),
                ("status-position", "bottom"),
                ("prefix", "C-Space"),
            ):
                actual = run(
                    "tmux", "-L", name, "show-option", "-gv", option, capture=True
                ).strip()
                if actual != value:
                    raise RuntimeError(
                        f"tmux {option}: expected {value}, found {actual}"
                    )
            bar = run(
                "tmux", "-L", name, "show-option", "-gv", "status-right", capture=True
            )
            if "continuum_save.sh" not in bar or "%H:%M" not in bar:
                raise RuntimeError("Nord status bar or persistence hook is missing")
            popup = run(
                "tmux", "-L", name, "show-option", "-gv", "@popup-toggle", capture=True
            )
            if not popup.strip():
                raise RuntimeError("tmux popup plugin did not load")
        finally:
            subprocess.run(
                ["tmux", "-L", name, "kill-server"], capture_output=True, check=False
            )


def reload_tmux():
    current = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_id}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if current.returncode:
        return
    previous = run(
        "tmux", "show-option", "-gqv", "@continuum-restore-max-delay", capture=True
    ).strip()
    # Reload appearance and bindings without treating this as server startup.
    run("tmux", "set-option", "-g", "@continuum-restore-max-delay", "0")
    try:
        run("tmux", "source-file", HOME / ".tmux.conf", capture=True)
    finally:
        if previous:
            run("tmux", "set-option", "-g", "@continuum-restore-max-delay", previous)
        else:
            run("tmux", "set-option", "-gu", "@continuum-restore-max-delay")
    remaining = run("tmux", "list-sessions", "-F", "#{session_id}", capture=True)
    if not set(current.stdout.splitlines()).issubset(remaining.splitlines()):
        raise RuntimeError("An existing tmux session disappeared during reload")


def verify():
    checks = []
    for line in (PROFILE / "apt.lock").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        package, version = line.split("=", 1)
        actual = run("dpkg-query", "-W", "-f=${Version}", package, capture=True).strip()
        if actual != version:
            raise RuntimeError(
                f"Package version mismatch: {package}: {actual}, expected {version}"
            )
    checks.append("all pinned system packages")
    for command in (
        "ghostty",
        "tmux",
        "starship",
        "docker",
        "fzf",
        "fdfind",
        "batcat",
        "eza",
        "zoxide",
        "wl-copy",
        "lazygit",
        "code",
        "gh",
        "cargo",
        "python3",
        "node",
        "npm",
        "java",
        "cmake",
        "ssh-copy-id",
    ):
        if not shutil.which(command):
            raise RuntimeError(f"Missing command: {command}")
    for command, version in (
        ("uv", VERSIONS["uv"]),
        ("codex", VERSIONS["codex"]),
        ("claude", VERSIONS["claude"]),
        ("opencode", VERSIONS["opencode"]),
    ):
        if version not in run(HOME / ".local/bin" / command, "--version", capture=True):
            raise RuntimeError(f"CLI version mismatch: {command}")
    checks.append("development tools and pinned agent CLIs")
    run("docker", "compose", "version", capture=True)
    run("docker", "buildx", "version", capture=True)
    if run("ps", "-p", "1", "-o", "comm=", capture=True).strip() == "systemd":
        run("docker", "info", "--format", "{{.ServerVersion}}", capture=True)
        checks.append("Docker daemon access, Compose and Buildx")
    else:
        checks.append("Docker Compose and Buildx; daemon requires a systemd host")
    for plugin in PLUGINS:
        marker = HOME / ".tmux/plugins" / plugin["name"] / ".workstation-revision"
        if marker.read_text().strip() != plugin["commit"]:
            raise RuntimeError(f"Plugin mismatch: {plugin['name']}")
    for executable in ("thumbs", "tmux-thumbs"):
        path = HOME / ".tmux/plugins/tmux-thumbs/target/release" / executable
        if not os.access(path, os.X_OK):
            raise RuntimeError(f"Missing precompiled tmux helper: {executable}")
    verify_tmux()
    checks.append("tmux plugins, compiled thumbs, Nord status bar, prefix and popup")
    aliases = run(
        "bash",
        "--noprofile",
        "--rcfile",
        HOME / ".bashrc",
        "-ic",
        "alias ll; declare -F z; command -v starship",
        capture=True,
    )
    if "eza -la" not in aliases:
        raise RuntimeError("ll is not configured")
    checks.append("interactive shell aliases, Starship and zoxide")
    family = run("fc-match", "-f", "%{family}", "JetBrainsMono Nerd Font", capture=True)
    if "Nerd Font" not in family:
        raise RuntimeError("Nerd Font selection fell back to another font")
    checks.append("actual Nerd Font resolution")
    installed = set(
        run("code", "--list-extensions", "--show-versions", capture=True)
        .lower()
        .splitlines()
    )
    missing = [
        f"{e['id']}@{e['version']}"
        for e in EXTENSIONS
        if f"{e['id']}@{e['version']}".lower() not in installed
    ]
    if missing:
        raise RuntimeError("Missing VS Code extensions: " + ", ".join(missing))
    import json5

    code = json5.loads((HOME / ".config/Code/User/settings.json").read_text())
    if code["workbench.colorTheme"] != "Nord":
        raise RuntimeError("VS Code theme is not Nord")
    checks.append(f"{len(EXTENSIONS)} pinned VS Code extensions and Nord selection")
    for path in (
        "Developer/projects",
        "Developer/agents",
        "rules/README.md",
        "rules/foundry.md",
        "rules/integrations.md",
    ):
        if not (HOME / "Studio" / path).exists():
            raise RuntimeError(f"Missing workspace scaffold: {path}")
    desktop(check=True)
    checks.append(
        "workspace scaffold and persisted GNOME dock/theme/tiling/shortcut settings"
    )
    REPORT["checks"] = checks
    REPORT["status"] = "verified"
    REPORT["pending"] = [
        "Account sign-in for Claude/Codex/GitHub is personal and is not copied.",
        "Continue is installed; its existing model configuration is preserved. A fresh machine needs an inference endpoint.",
    ]
    # Stored settings are distinct from a running compositor's extension state.
    if Path(f"/run/user/{os.getuid()}/bus").exists():
        result = subprocess.run(
            ["gnome-extensions", "info", "tactile@lundal.io"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or "State: ACTIVE" not in result.stdout:
            REPORT["pending"].append(
                "Log out and back in to activate the installed Tactile extension."
            )
    else:
        REPORT["pending"].append(
            "GNOME settings checked without a graphical session; desktop appearance remains unverified."
        )
    save_report()
    for check in checks:
        print(f"PASS {check}")
    for item in REPORT["pending"]:
        print(f"NOTE {item}")


def main():
    global RUN
    if os.geteuid() == 0:
        raise RuntimeError(
            "User configuration must run as the workstation user, never root"
        )
    os.umask(0o077)
    os.environ["GIT_TERMINAL_PROMPT"] = "0"
    action = sys.argv[1] if len(sys.argv) == 2 else ""
    if action in ("desktop", "desktop-check"):
        RUN = (
            Path(os.environ["WORKSTATION_RECOVERY"])
            if "WORKSTATION_RECOVERY" in os.environ
            else None
        )
        desktop_settings(action == "desktop-check")
        return
    if action == "verify":
        report_path = STATE / "report.json"
        if report_path.exists():
            REPORT.update(json.loads(report_path.read_text()))
        REPORT["failed"] = []
        verify()
        return
    if action != "install":
        raise RuntimeError(
            "Use sudo ./bootstrap.sh to install, or ./verify.sh to verify"
        )
    STATE.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    RUN = Path(tempfile.mkdtemp(prefix=time.strftime("%Y%m%d-%H%M%S-"), dir=STATE))
    REPORT["recovery"] = str(RUN)
    for name, function in (
        ("CLI tools", tools),
        ("tmux plugins", plugins),
        ("fonts and themes", fonts_and_themes),
        ("configuration", config),
        ("VS Code extensions", vscode),
        ("workspace scaffold", scaffold),
        ("Tactile build", tactile),
        ("GNOME settings", desktop),
        ("existing tmux configuration reload", reload_tmux),
    ):
        stage(name, function)
    REPORT["status"] = "installed-awaiting-verification"
    save_report()
    print(f"Recovery copies: {RUN}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - report every failed installation stage
        REPORT["status"] = "failed"
        detail = (
            (error.stderr or error.stdout or "")[-4000:]
            if isinstance(error, subprocess.CalledProcessError)
            else ""
        )
        REPORT["failed"].append(f"{error}\n{detail}".strip())
        save_report()
        print(f"FAILED: {error}", file=sys.stderr)
        if detail:
            print(detail, file=sys.stderr)
        sys.exit(1)
