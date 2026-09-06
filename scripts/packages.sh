#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $EUID == 0 ]] || exit 1
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
APT=(apt-get -o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 -o DPkg::Lock::Timeout=120)
timeout 600 "${APT[@]}" update
# The signed Ubuntu packages supply everything needed to configure the Code repository.
timeout 900 "${APT[@]}" install --yes --no-install-recommends \
  ca-certificates=20260601~26.04.1 curl=8.18.0-1ubuntu2.4 gnupg=2.4.8-4ubuntu3.1
TEMP_DIR=$(mktemp -d /tmp/workstation-root.XXXXXX)
trap 'rm -r "$TEMP_DIR"' EXIT
curl --fail --silent --show-error --location --retry 3 --max-time 120 \
  https://packages.microsoft.com/keys/microsoft.asc -o "$TEMP_DIR/microsoft.asc"
gpg --batch --dearmor --output "$TEMP_DIR/microsoft.gpg" "$TEMP_DIR/microsoft.asc"
install -d -m 0755 /etc/apt/keyrings
install -m 0644 "$TEMP_DIR/microsoft.gpg" /etc/apt/keyrings/workstation-microsoft.gpg
printf '%s\n' 'Types: deb' 'URIs: https://packages.microsoft.com/repos/code' 'Suites: stable' \
  'Components: main' "Architectures: $(dpkg --print-architecture)" \
  'Signed-By: /etc/apt/keyrings/workstation-microsoft.gpg' > "$TEMP_DIR/workstation-code.sources"
# Respect an existing Code repository instead of adding a conflicting Signed-By entry.
if ! grep -rl 'packages.microsoft.com/repos/code' /etc/apt/sources.list.d /etc/apt/sources.list 2>/dev/null | grep -q .; then
  install -m 0644 "$TEMP_DIR/workstation-code.sources" /etc/apt/sources.list.d/workstation-code.sources
fi
timeout 600 "${APT[@]}" update
mapfile -t PACKAGES < <(awk 'NF && $1 !~ /^#/ {print $1}' "$SCRIPT_DIR/profiles/ubuntu-26.04/apt.lock")
timeout 120 "${APT[@]}" --simulate install --no-install-recommends "${PACKAGES[@]}" >/dev/null
timeout 1800 "${APT[@]}" install --yes --no-install-recommends "${PACKAGES[@]}" </dev/null
