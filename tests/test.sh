#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

bash -n "$ROOT/bootstrap.sh"
shellcheck "$ROOT/bootstrap.sh"

help_output=$(bash "$ROOT/bootstrap.sh" --help)
grep -q -- '--apply' <<<"$help_output"
grep -q -- '--destination PATH' <<<"$help_output"
grep -q -- '--tui' <<<"$help_output"
grep -q -- '--with-desktop' <<<"$help_output"

required_manifest="$ROOT/profiles/ubuntu-26.04/required.txt"
for package in tmux ghostty starship docker.io docker-compose-v2 docker-buildx; do
  grep -qx "$package" "$required_manifest"
done
grep -q 'TACTILE_VERSION=.*37' "$ROOT/bootstrap.sh"
grep -q 'TACTILE_UUID=.*tactile@lundal.io' "$ROOT/bootstrap.sh"
grep -q "command 'ghostty'" "$ROOT/bootstrap.sh"
grep -q 'WORKSPACE_ROOT/rules' "$ROOT/bootstrap.sh"
test -f "$ROOT/seed/rules/README.md"
test -f "$ROOT/seed/rules/foundry.md"
if grep -qx 'docker.io' "$ROOT/profiles/ubuntu-26.04/optional.txt"; then
  printf 'docker.io must remain in the default workstation baseline\n' >&2
  exit 1
fi

if bash "$ROOT/bootstrap.sh" --check --no-packages >/tmp/ubuntu-bootstrap-test-output 2>/tmp/ubuntu-bootstrap-test-error; then
  printf 'unexpectedly accepted the current host as Ubuntu 26.04\n' >&2
  exit 1
fi
grep -q 'Ubuntu 26.04 LTS is required' /tmp/ubuntu-bootstrap-test-error

printf 'local safety and syntax checks passed\n'
