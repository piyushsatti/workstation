# Ubuntu workstation bootstrap prototype

This is the v0.1 implementation slice described in
`../ubuntu-workstation-bootstrap-plan.md`. It targets Ubuntu 26.04 LTS only.

The script is preview-first. It refuses non-Ubuntu and non-26.04 targets before
package or user-file operations. It uses the profile manifests for packages,
Chezmoi v2.70.5 for declared user configuration, and creates only empty workspace
directories plus three small seed notes. The default package baseline includes
tmux, Ghostty, Starship, Docker Engine with Compose and Buildx, and the tools
needed for development. It configures Microsoft's stable apt repository and
installs VS Code during apply. It does not import repositories, transcripts,
credentials, memory corpora, or RAG indexes.

## Visual TUI prototype

The Textual interface calls the existing bootstrap backend. It defaults to
preview mode, so the review action reports the backend plan without changing
files. Pass `--apply` only when you intentionally want the acceptance action to
apply the selected profile.

Run the preview-backed UI with `uv` in an isolated environment:

```sh
UV_CACHE_DIR=/tmp/codex-textual-cache \
  uv run --with textual python tui_demo.py
```

For a disposable apply test, use a temporary destination and skip package
operations:

```sh
UV_CACHE_DIR=/tmp/codex-textual-cache \
  uv run --with textual python tui_demo.py \
    --apply --no-packages \
    --destination /tmp/tui-home \
    --workspace /tmp/tui-home/Studio
```

The backend output and exit status are shown on the review screen. The TUI
stops waiting for a backend run after 300 seconds. Do not run `--apply` on a
real workstation until the preview has been reviewed.

## Run the fast local checks

On a development Mac, this validates syntax and confirms that the installer
refuses the host without changing it:

```sh
./tests/test.sh
```

The simple capability-selection menu is available on an Ubuntu 26.04 terminal:

```sh
./bootstrap.sh --tui
```

It keeps the base workstation enabled, lets you toggle personal configuration,
workspace seed notes, and optional CLI packages, then gives you a review screen
before apply. Press `q` to leave without changing anything.

The test intentionally does not claim that macOS is supported. Docker is the
Linux userland check, not a macOS system check:

```sh
docker build -f tests/Dockerfile -t ubuntu-workstation-bootstrap:0.1 .
```

The Docker check only proves the target gate and source/manifest integrity. The
v0.1 release gate is a disposable Ubuntu 26.04 VM with a recorded recovery
point. Run the installer there first:

```sh
./bootstrap.sh --preview
./bootstrap.sh --apply
```

For a test home on the VM, use a disposable destination and workspace path:

```sh
./bootstrap.sh \
  --apply \
  --noninteractive \
  --destination /tmp/bootstrap-home \
  --workspace /tmp/bootstrap-home/Studio
```

That test mode still requires the VM to be Ubuntu 26.04. Do not use the primary
Mac, Europa, Voyager 1, or any production machine as the first apply target.

## Current limits

- The canonical source repository is `https://github.com/piyushsatti/workstation`.
- VS Code extensions, fonts, Continue, Tailscale, and harness adapters need
  their own package and acceptance work before being marked complete.
- There is no macOS profile in v0.1.
