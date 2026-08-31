#!/usr/bin/env bash

# Read-only ZeroTier evidence collector for macOS and Linux.
set -u

section() {
  printf '\n## %s\n' "$1"
}

run_optional() {
  "$@" 2>&1 || true
}

section "platform"
run_optional uname -s
run_optional uname -m

zt_cli="$(command -v zerotier-cli 2>/dev/null || true)"
zt_one="$(command -v zerotier-one 2>/dev/null || true)"

if [[ -z "$zt_one" && -x "/Library/Application Support/ZeroTier/One/zerotier-one" ]]; then
  zt_one="/Library/Application Support/ZeroTier/One/zerotier-one"
fi

section "installation"
printf 'zerotier-cli=%s\n' "${zt_cli:-not-found}"
printf 'zerotier-one=%s\n' "${zt_one:-not-found}"

case "$(uname -s 2>/dev/null || true)" in
  Darwin)
    run_optional ls -ld \
      "/Applications/ZeroTier.app" \
      "/Applications/ZeroTier One.app" \
      "/Library/Application Support/ZeroTier/One" \
      "/Library/LaunchDaemons/com.zerotier.one.plist"
    run_optional pkgutil --pkg-info com.zerotier.pkg.ZeroTierOne
    ;;
  Linux)
    if command -v dpkg-query >/dev/null 2>&1; then
      run_optional dpkg-query -W zerotier-one
    fi
    if command -v rpm >/dev/null 2>&1; then
      run_optional rpm -q zerotier-one
    fi
    ;;
esac

section "version"
if [[ -n "$zt_cli" ]]; then
  run_optional "$zt_cli" -v
else
  printf 'ZeroTier CLI not found\n'
fi

section "service"
case "$(uname -s 2>/dev/null || true)" in
  Darwin)
    run_optional launchctl print system/com.zerotier.one
    ;;
  Linux)
    if command -v systemctl >/dev/null 2>&1; then
      run_optional systemctl is-enabled zerotier-one.service
      run_optional systemctl is-active zerotier-one.service
      run_optional systemctl status --no-pager zerotier-one.service
    fi
    ;;
esac

section "node-status"
if [[ -n "$zt_cli" ]]; then
  run_optional "$zt_cli" info
fi

section "networks"
if [[ -n "$zt_cli" ]]; then
  run_optional "$zt_cli" listnetworks
fi

section "peers"
if [[ -n "$zt_cli" ]]; then
  run_optional "$zt_cli" peers
fi

printf '\nNOTE: If service state is healthy but CLI calls report connection failure, retry the read-only CLI outside any restricted sandbox before repairing the service.\n'
