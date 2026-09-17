#!/usr/bin/env python3
"""Compatibility CLI: delegate to the evaluation repository; no reporting logic here."""
import json
import os
from pathlib import Path
import runpy
import sys


def main():
    config_path=Path(__file__).resolve().parents[1]/'config.json'
    repo=os.environ.get('A2D_EVAL_REPO')
    if not repo and config_path.exists():
        repo=json.loads(config_path.read_text()).get('eval_repo')
    if not repo:
        raise SystemExit('Set A2D_EVAL_REPO or local config.json eval_repo to the evaluation checkout.')
    target=Path(repo).expanduser().resolve()/'tools/a2d_eval_loop/watch_eval_to_obsidian.py'
    if not target.is_file() or target.resolve()==Path(__file__).resolve():
        raise SystemExit(f'Canonical report script missing or recursive: {target}')
    sys.argv[0]=str(target)
    runpy.run_path(str(target),run_name='__main__')

if __name__=='__main__':
    main()
