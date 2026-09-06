#!/usr/bin/env bash
# Complete Ubuntu 26.04 workstation installation for the invoking sudo user.
set -Eeuo pipefail
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  printf 'Usage: sudo ./bootstrap.sh\nInstalls the complete workstation for the user invoking sudo. No selection prompts.\n'
  exit 0
fi
[[ $# == 0 ]] || { printf 'Run sudo ./bootstrap.sh without flags. Verification: ./verify.sh\n' >&2; exit 2; }
[[ -r /etc/os-release ]] || { printf 'Ubuntu 26.04 LTS is required.\n' >&2; exit 1; }
# shellcheck disable=SC1091
. /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_ID:-}" == 26.04 ]] || { printf 'Ubuntu 26.04 LTS is required.\n' >&2; exit 1; }
[[ $EUID == 0 && -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]] || {
  printf 'Run sudo ./bootstrap.sh from your normal user account.\n' >&2; exit 1;
}
TARGET_USER=$SUDO_USER
TARGET_UID=$(id -u "$TARGET_USER")
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
[[ -d "$TARGET_HOME" && "$TARGET_HOME" != / && "$TARGET_HOME" != /root ]] || exit 1
exec 9>/run/lock/workstation-bootstrap.lock
flock -n 9 || { printf 'Another workstation installation is running.\n' >&2; exit 1; }
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
as_user() {
  runuser -u "$TARGET_USER" -- env HOME="$TARGET_HOME" USER="$TARGET_USER" LOGNAME="$TARGET_USER" \
    PATH="$TARGET_HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" \
    XDG_CONFIG_HOME="$TARGET_HOME/.config" XDG_DATA_HOME="$TARGET_HOME/.local/share" \
    XDG_STATE_HOME="$TARGET_HOME/.local/state" XDG_CACHE_HOME="$TARGET_HOME/.cache" \
    XDG_RUNTIME_DIR="/run/user/$TARGET_UID" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$TARGET_UID/bus" "$@"
}
STAGE=preflight
trap 'printf "\nFAILED during %s (line %s). Re-run the same command after resolving the reported error.\n" "$STAGE" "$LINENO" >&2' ERR
printf 'Installing the complete workstation for %s in %s\n' "$TARGET_USER" "$TARGET_HOME"
STAGE=packages
bash "$SCRIPT_DIR/scripts/packages.sh"
STAGE=user-configuration
as_user /usr/bin/python3 "$SCRIPT_DIR/scripts/workstation.py" install
STAGE=docker
usermod --append --groups docker "$TARGET_USER"
if [[ "$(ps -p 1 -o comm=)" == systemd ]]; then
  systemctl enable --now docker.service
fi
STAGE=verification
as_user /usr/bin/python3 "$SCRIPT_DIR/scripts/workstation.py" verify
printf '\nInstallation verified. Open a new terminal; a new login activates new desktop extensions and Docker group access.\n'
