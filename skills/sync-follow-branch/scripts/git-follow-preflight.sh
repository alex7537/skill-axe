#!/usr/bin/env bash
set -euo pipefail

target_branch="${1:-}"
remote_name="${2:-origin}"

if [[ -z "${target_branch}" ]]; then
  echo "usage: $0 <target-branch> [remote]" >&2
  exit 2
fi

git rev-parse --is-inside-work-tree >/dev/null

local_ref="refs/heads/${target_branch}"
remote_ref="refs/remotes/${remote_name}/${target_branch}"

echo "repository: $(git rev-parse --show-toplevel)"
echo "current branch: $(git branch --show-current)"
echo "target branch: ${target_branch}"
echo "remote: ${remote_name}"

if git remote get-url "${remote_name}" >/dev/null 2>&1; then
  echo "remote URL: $(git remote get-url "${remote_name}")"
else
  echo "remote status: missing"
fi

echo
echo "working tree:"
git status --short --branch

echo
if git show-ref --verify --quiet "${local_ref}"; then
  echo "local target: exists"
  upstream="$(git for-each-ref --format='%(upstream:short)' "${local_ref}")"
  echo "local upstream: ${upstream:-none}"
else
  echo "local target: missing"
fi

if git show-ref --verify --quiet "${remote_ref}"; then
  echo "remote target ref: exists"
else
  echo "remote target ref: missing or not fetched"
fi

if git show-ref --verify --quiet "${local_ref}" && git show-ref --verify --quiet "${remote_ref}"; then
  echo "ahead/behind (local remote): $(git rev-list --left-right --count "${local_ref}...${remote_ref}")"
fi

echo
echo "recent stashes:"
git stash list --date=local | sed -n '1,5p'

echo
echo "recent checkouts:"
git reflog --date=iso --format='%h %gd %gs' -20 | grep 'checkout: moving from' | sed -n '1,5p' || true
