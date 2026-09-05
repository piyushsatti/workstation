#!/usr/bin/env bash
# Ubuntu workstation bootstrap prototype, v0.1.
# Preview is the default. Applying packages or user files requires --apply.
# This script intentionally refuses every non-Ubuntu or non-26.04 target.

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_DIR="$SCRIPT_DIR/profiles"
SOURCE_DIR="$SCRIPT_DIR/chezmoi"
PROFILE="ubuntu-26.04"
MODE="preview"
DESTINATION="${HOME:?HOME must be set}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$DESTINATION/Studio}"
CHEZMOI_VERSION="${CHEZMOI_VERSION:-2.70.5}"
CHEZMOI_CMD=""
WITH_OPTIONAL=0
NO_PACKAGES=0
NONINTERACTIVE=0
TUI=0
CONFIG_ENABLED=1
WORKSPACE_ENABLED=1

usage() {
  cat <<'EOF'
Usage: bootstrap.sh [options]

Preview is the default and never installs packages or applies user files.

Options:
  --preview              Show the plan only (default)
  --apply                Install selected packages and apply user configuration
  --check                Validate the target and source without changing it
  --profile NAME         Select a profile (default: ubuntu-26.04)
  --destination PATH     Use PATH as the destination home (test fixture use)
  --workspace PATH       Use PATH as the workspace root
  --with-optional        Include the optional package set
  --no-packages          Skip package operations
  --no-config            Skip managed user configuration
  --no-workspace         Skip workspace scaffolding
  --noninteractive       Do not prompt before apply
  --tui                  Open the simple capability-selection menu
  -h, --help             Show this help

Examples:
  ./bootstrap.sh --preview
  ./bootstrap.sh --apply --with-optional
  ./bootstrap.sh --check --destination /tmp/ubuntu-bootstrap-home
EOF
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

note() {
  printf '%s\n' "$*"
}

profile_file() {
  local name=$1
  printf '%s/%s/%s\n' "$PROFILE_DIR" "$PROFILE" "$name"
}

read_package_file() {
  local path=$1
  [[ -f "$path" ]] || die "package manifest not found: $path"
  awk 'NF && $1 !~ /^#/ { print $1 }' "$path"
}

target_description() {
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    printf '%s %s (%s)\n' "${NAME:-unknown}" "${VERSION_ID:-unknown}" "${ID:-unknown}"
    return
  fi
  printf 'unknown operating system\n'
}

chezmoi_asset_name() {
  local machine=$1
  case "$machine" in
    x86_64) printf 'chezmoi_%s_linux_amd64.tar.gz\n' "$CHEZMOI_VERSION" ;;
    aarch64|arm64) printf 'chezmoi_%s_linux_arm64.tar.gz\n' "$CHEZMOI_VERSION" ;;
    *) die "unsupported Linux architecture for Chezmoi: $machine" ;;
  esac
}

ensure_chezmoi() {
  if command -v chezmoi >/dev/null 2>&1; then
    CHEZMOI_CMD=$(command -v chezmoi)
    return
  fi

  CHEZMOI_CMD="$DESTINATION/.local/bin/chezmoi"
  if [[ -x "$CHEZMOI_CMD" ]]; then
    return
  fi

  [[ "$MODE" == apply ]] || {
    note "Chezmoi is absent; apply would install pinned version v$CHEZMOI_VERSION to $CHEZMOI_CMD."
    return
  }

  command -v curl >/dev/null 2>&1 || die "curl is required to bootstrap Chezmoi"
  command -v tar >/dev/null 2>&1 || die "tar is required to unpack Chezmoi"
  command -v sha256sum >/dev/null 2>&1 || die "sha256sum is required to verify Chezmoi"

  local machine asset base_url expected archive
  machine=$(uname -m)
  asset=$(chezmoi_asset_name "$machine")
  base_url="https://github.com/twpayne/chezmoi/releases/download/v$CHEZMOI_VERSION"
  mkdir -p "$(dirname "$CHEZMOI_CMD")"
  archive=$(mktemp "$DESTINATION/.local/bin/chezmoi-download.XXXXXX")
  trap 'rm -f "$archive"' RETURN

  note "Downloading Chezmoi v$CHEZMOI_VERSION."
  curl --fail --silent --show-error --location --retry 3 \
    --output "$archive" "$base_url/$asset"
  expected=$(curl --fail --silent --show-error --location --retry 3 \
    "$base_url/chezmoi_${CHEZMOI_VERSION}_checksums.txt" \
    | awk -v asset="$asset" '$2 == asset || $2 == "*" asset { print $1; exit }')
  [[ -n "$expected" ]] || die "Chezmoi checksum not found for $asset"
  printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status - \
    || die "Chezmoi checksum verification failed"
  tar -xzf "$archive" -C "$(dirname "$CHEZMOI_CMD")" chezmoi
  chmod 0755 "$CHEZMOI_CMD"
  [[ -x "$CHEZMOI_CMD" ]] || die "Chezmoi installation did not produce an executable"
  rm -f "$archive"
  trap - RETURN
}

require_supported_target() {
  [[ "$PROFILE" == "ubuntu-26.04" ]] || die "unsupported profile: $PROFILE"
  [[ -r /etc/os-release ]] || die "Ubuntu 26.04 LTS is required; cannot inspect /etc/os-release"

  # shellcheck disable=SC1091
  . /etc/os-release
  [[ "${ID:-}" == "ubuntu" ]] || die "Ubuntu 26.04 LTS is required; found ${ID:-unknown}"
  [[ "${VERSION_ID:-}" == "26.04" ]] || die "Ubuntu 26.04 LTS is required; found ${VERSION_ID:-unknown}"
}

validate_source() {
  [[ -d "$SOURCE_DIR" ]] || die "Chezmoi source directory not found: $SOURCE_DIR"
  [[ -f "$SOURCE_DIR/dot_bashrc" ]] || die "Chezmoi source is missing dot_bashrc"
  [[ -f "$SOURCE_DIR/dot_tmux.conf" ]] || die "Chezmoi source is missing dot_tmux.conf"
  [[ -f "$(profile_file required.txt)" ]] || die "required package manifest is missing"
  [[ -f "$(profile_file optional.txt)" ]] || die "optional package manifest is missing"
}

package_list() {
  read_package_file "$(profile_file required.txt)"
  if (( WITH_OPTIONAL )); then
    read_package_file "$(profile_file optional.txt)"
  fi
}

print_plan() {
  note "Ubuntu workstation bootstrap v0.1"
  note "Target: $(target_description)"
  note "Profile: $PROFILE"
  note "Mode: $MODE"
  note "Destination home: $DESTINATION"
  note "Workspace root: $WORKSPACE_ROOT"
  note "Chezmoi source: $SOURCE_DIR"
  note ""
  note "Packages:"
  package_list | sed 's/^/  - /'
  note ""
  if (( CONFIG_ENABLED )); then
    note "Managed configuration:"
    find "$SOURCE_DIR" -type f -not -path '*/.git/*' -print \
      | sed "s#^$SOURCE_DIR/##" \
      | sort \
      | sed 's/^/  - /'
  else
    note "Managed configuration: not selected"
  fi
  note ""
  if (( WORKSPACE_ENABLED )); then
    note "Workspace directories to create on apply:"
    note "  - $WORKSPACE_ROOT/Developer"
    note "  - $WORKSPACE_ROOT/Projects"
    note "  - $WORKSPACE_ROOT/memory"
    note "  - $WORKSPACE_ROOT/.bootstrap"
  else
    note "Workspace scaffolding: not selected"
  fi
}

run_as_root() {
  if (( EUID == 0 )); then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    die "sudo is required for package installation"
  fi
}

install_packages() {
  (( NO_PACKAGES )) && { note "Skipping packages (--no-packages)."; return; }

  command -v apt-get >/dev/null 2>&1 || die "apt-get is required on Ubuntu"
  mapfile -t packages < <(package_list)
  ((${#packages[@]} > 0)) || die "package manifest produced no packages"

  note "Updating apt metadata."
  run_as_root apt-get update
  note "Installing declared packages."
  run_as_root apt-get install --yes "${packages[@]}"
}

apply_chezmoi() {
  (( CONFIG_ENABLED )) || { note "Skipping managed configuration."; return; }
  ensure_chezmoi
  [[ -x "$CHEZMOI_CMD" ]] || die "chezmoi is not available after bootstrap"
  note "Applying managed user files with Chezmoi."
  TERM=dumb "$CHEZMOI_CMD" --color=false --progress=false \
    --source "$SOURCE_DIR" --destination "$DESTINATION" apply
}

write_if_absent() {
  local source=$1
  local target=$2
  if [[ -e "$target" ]]; then
    note "Preserving existing file: $target"
    return
  fi
  install -D -m 0644 "$source" "$target"
  note "Created: $target"
}

create_workspace() {
  (( WORKSPACE_ENABLED )) || { note "Skipping workspace scaffolding."; return; }
  mkdir -p \
    "$WORKSPACE_ROOT/Developer" \
    "$WORKSPACE_ROOT/Projects" \
    "$WORKSPACE_ROOT/memory" \
    "$WORKSPACE_ROOT/.bootstrap"

  write_if_absent \
    "$SCRIPT_DIR/seed/workspace-principles.md" \
    "$WORKSPACE_ROOT/memory/workspace-principles.md"
  write_if_absent \
    "$SCRIPT_DIR/seed/project-structure.md" \
    "$WORKSPACE_ROOT/memory/project-structure.md"
  write_if_absent \
    "$SCRIPT_DIR/seed/bootstrap-context.md" \
    "$WORKSPACE_ROOT/.bootstrap/context.md"
}

tui_status() {
  if (( $1 )); then
    printf 'on'
  else
    printf 'off'
  fi
}

tui_menu() {
  [[ -t 0 && -t 1 ]] || die "--tui requires an interactive terminal"

  while :; do
    note ""
    note "Ubuntu workstation bootstrap v0.1"
    note "Target: $(target_description)"
    note ""
    note "Select capabilities. Base workstation is always included."
    note "  1) Personal configuration       [$(tui_status "$CONFIG_ENABLED")]"
    note "  2) Workspace and seed notes     [$(tui_status "$WORKSPACE_ENABLED")]"
    note "  3) Optional CLI packages        [$(tui_status "$WITH_OPTIONAL")]"
    note "  4) Review selected changes"
    note "  5) Apply selected changes"
    note "  q) Quit"
    printf 'Choice: '
    read -r choice

    case "$choice" in
      1)
        if (( CONFIG_ENABLED )); then CONFIG_ENABLED=0; else CONFIG_ENABLED=1; fi
        ;;
      2)
        if (( WORKSPACE_ENABLED )); then WORKSPACE_ENABLED=0; else WORKSPACE_ENABLED=1; fi
        ;;
      3)
        if (( WITH_OPTIONAL )); then WITH_OPTIONAL=0; else WITH_OPTIONAL=1; fi
        ;;
      4)
        MODE="preview"
        print_plan
        ensure_chezmoi
        ;;
      5)
        MODE="apply"
        return
        ;;
      q|Q)
        note "Cancelled. No changes were made."
        exit 0
        ;;
      *) note "Choose 1, 2, 3, 4, 5, or q." ;;
    esac
  done
}

confirm_apply() {
  (( NONINTERACTIVE )) && return
  [[ -t 0 ]] || die "apply requires --noninteractive when stdin is not a terminal"
  printf 'Apply this plan to %s? [y/N] ' "$DESTINATION"
  read -r answer
  [[ "$answer" == "y" || "$answer" == "Y" ]] || die "apply cancelled"
}

main() {
  while (($# > 0)); do
    case "$1" in
      --preview) MODE="preview" ;;
      --apply) MODE="apply" ;;
      --check) MODE="check" ;;
      --profile) (($# >= 2)) || die "--profile needs a value"; PROFILE=$2; shift ;;
      --destination) (($# >= 2)) || die "--destination needs a value"; DESTINATION=$2; shift ;;
      --workspace) (($# >= 2)) || die "--workspace needs a value"; WORKSPACE_ROOT=$2; shift ;;
      --with-optional) WITH_OPTIONAL=1 ;;
      --no-packages) NO_PACKAGES=1 ;;
      --no-config) CONFIG_ENABLED=0 ;;
      --no-workspace) WORKSPACE_ENABLED=0 ;;
      --noninteractive) NONINTERACTIVE=1 ;;
      --tui) TUI=1 ;;
      -h|--help) usage; return 0 ;;
      *) die "unknown option: $1" ;;
    esac
    shift
  done

  require_supported_target
  validate_source
  (( TUI )) && tui_menu

  case "$MODE" in
    check)
      note "Target and source checks passed."
      note "Target: $(target_description)"
      ;;
    preview)
      print_plan
      ensure_chezmoi
      note "Preview only. No package or filesystem changes were made."
      ;;
    apply)
      print_plan
      confirm_apply
      install_packages
      apply_chezmoi
      create_workspace
      note "Bootstrap apply completed. Run the verification checklist before treating this as accepted."
      ;;
  esac
}

main "$@"
