#!/usr/bin/env bash
set -u

failures=0

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1"; failures=$((failures + 1)); }
info() { printf 'INFO  %s\n' "$1"; }

if ! command -v systemctl >/dev/null 2>&1; then
  fail "systemctl is unavailable"
else
  for unit in hysteria-server xray caddy; do
    if systemctl is-active --quiet "$unit"; then
      pass "$unit is active"
    else
      fail "$unit is not active"
    fi
  done

  if systemctl is-active --quiet sub-store; then
    pass "sub-store systemd unit is active"
  elif command -v pm2 >/dev/null 2>&1 && pm2 describe sub-store >/dev/null 2>&1; then
    pass "sub-store is registered in pm2"
  else
    fail "sub-store was not found as an active systemd unit or pm2 process"
  fi
fi

if ! command -v ss >/dev/null 2>&1; then
  fail "ss is unavailable"
else
  sockets="$(ss -H -lntup 2>/dev/null || true)"
  ipv4_loopback_re='127[.]0[.]0[.]1'
  ipv4_any_re='0[.]0[.]0[.]0'

  if grep -Eq 'udp.*:443([[:space:]]|$)' <<<"$sockets"; then
    pass "a UDP 443 listener exists"
  else
    fail "no UDP 443 listener found for Hysteria2"
  fi

  if grep -Eq 'tcp.*:443([[:space:]]|$)' <<<"$sockets"; then
    pass "a TCP 443 listener exists"
  else
    fail "no TCP 443 listener found for Caddy"
  fi

  if grep -Eq 'tcp.*:8443([[:space:]]|$)' <<<"$sockets"; then
    pass "a TCP 8443 listener exists"
  else
    fail "no TCP 8443 listener found for Reality"
  fi

  port_3000_lines="$(grep -E 'tcp.*:3000([[:space:]]|$)' <<<"$sockets" || true)"
  if [[ -z "$port_3000_lines" ]]; then
    fail "no TCP 3000 listener found for Sub-Store"
  elif grep -Eq "(${ipv4_loopback_re}|localhost|\[::1\]):3000([[:space:]]|$)" <<<"$port_3000_lines" && ! grep -Eq "(${ipv4_any_re}|\[::\]|\*):3000([[:space:]]|$)" <<<"$port_3000_lines"; then
    pass "Sub-Store port 3000 is loopback-only"
  else
    fail "port 3000 is not confirmed loopback-only"
  fi

  caddy_udp="$(grep -E 'udp.*:443([[:space:]]|$).*caddy' <<<"$sockets" || true)"
  if [[ -n "$caddy_udp" ]]; then
    fail "Caddy appears to own UDP 443; disable HTTP/3"
  else
    pass "Caddy is not shown as an owner of UDP 443"
  fi
fi

if command -v curl >/dev/null 2>&1 && curl --silent --show-error --fail --max-time 3 http://localhost:3000/ >/dev/null 2>&1; then
  pass "Sub-Store responds on loopback"
else
  info "Sub-Store loopback HTTP probe did not return a 2xx response; inspect its configured path and logs"
fi

if (( failures > 0 )); then
  printf '\n%d required check(s) failed.\n' "$failures"
  exit 1
fi

printf '\nAll required local checks passed. External ACL, DNS, TLS, client handshakes, and egress still require separate verification.\n'
