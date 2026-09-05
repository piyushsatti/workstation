#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

bash -n "$ROOT/bootstrap.sh"
shellcheck "$ROOT/bootstrap.sh"

help_output=$(bash "$ROOT/bootstrap.sh" --help)
grep -q -- '--apply' <<<"$help_output"
grep -q -- '--destination PATH' <<<"$help_output"
grep -q -- '--tui' <<<"$help_output"

if bash "$ROOT/bootstrap.sh" --check --no-packages >/tmp/ubuntu-bootstrap-test-output 2>/tmp/ubuntu-bootstrap-test-error; then
  printf 'unexpectedly accepted the current host as Ubuntu 26.04\n' >&2
  exit 1
fi
grep -q 'Ubuntu 26.04 LTS is required' /tmp/ubuntu-bootstrap-test-error

printf 'local safety and syntax checks passed\n'
