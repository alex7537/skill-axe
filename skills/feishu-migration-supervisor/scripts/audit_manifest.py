#!/usr/bin/env python3
"""Read-only structural audit of a local Feishu migration ledger (no network)."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

STATES = {'pending','reading','prepared','creating','created','verifying','verified',
          'needs_review','blocked','skipped','unknown_write'}
CHECKS = ('body_match','structure_checked','resources_checked','links_checked',
          'owner_checked','placement_checked')

def plan_digest(m):
    plan = {k: m.get(k) for k in ('source_profile','target_profile','scope_description',
                                 'target_root','mode')}
    plan['items'] = [{k: r.get(k) for k in ('source_key','source_url','source_path','target_path','reuse_target')}
                     for r in m.get('items', [])]
    plan['containers'] = [r.get('path') for r in m.get('containers', [])]
    return hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()

def audit(m):
    errors, notes = [], []
    if m.get('version') != 1: errors.append('unsupported manifest version')
    for k in ('source_profile','target_profile','scope_description','target_root','mode'):
        if not m.get(k): errors.append('missing '+k)
    if m.get('source_profile') == m.get('target_profile'):
        errors.append('source and target profiles must differ')
    items, containers = m.get('items', []), m.get('containers', [])
    if not items: errors.append('empty source manifest')
    keys, targets = set(), set()
    for kind, rows in (('item',items), ('container',containers)):
        for index,r in enumerate(rows):
            label=f'{kind}[{index}]'
            if kind == 'item':
                key=r.get('source_key')
                if not key or key in keys: errors.append(label+': missing/duplicate source key')
                keys.add(key)
                if not r.get('source_url') or not r.get('target_path'):
                    errors.append(label+': missing source URL/target path')
            elif not r.get('path'): errors.append(label+': missing container path')
            status=r.get('status')
            if status not in STATES: errors.append(label+': invalid status')
            target=r.get('target') or {}; token=target.get('document_id')
            if token:
                if token in targets: errors.append(label+': target reused by multiple records')
                targets.add(token)
            if status in ('creating','unknown_write'):
                notes.append(label+': reconcile remote result before further writes')
            if status == 'verified':
                for field in ('document_id','node_token','space_id','owner_id','url'):
                    if not target.get(field): errors.append(label+': missing target '+field)
                v=r.get('verification') or {}
                for field in CHECKS:
                    if v.get(field) is not True: errors.append(label+': unverified '+field)
                if not v.get('evidence'): errors.append(label+': missing readback evidence')
    digest=plan_digest(m); approval=m.get('approval') or {}
    approved=(approval.get('status')=='approved' and approval.get('plan_digest')==digest
              and bool(approval.get('evidence')))
    if not approved: notes.append('exact plan approval is pending, missing, or stale')
    if not m.get('scope_complete'): notes.append('global source coverage is not established')
    records=items+containers
    complete=bool(records) and all(r.get('status')=='verified' for r in records) and not errors
    uncertain=any(r.get('status') in ('creating','unknown_write') for r in records)
    return {'items':len(items),'containers':len(containers),
            'item_statuses':dict(Counter(r.get('status') for r in items)),
            'container_statuses':dict(Counter(r.get('status') for r in containers)),
            'plan_digest':digest,'approval_valid':approved,
            'ledger_ready_for_execution':approved and not errors and not uncertain,
            'all_records_verified':complete,'errors':errors,'notes':notes}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('manifest',type=Path)
    args=p.parse_args()
    try: result=audit(json.loads(args.manifest.read_text()))
    except (OSError,ValueError,TypeError,AttributeError) as exc:
        print(json.dumps({'errors':[str(exc)]})); return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 2 if result['errors'] else 0

if __name__ == '__main__': raise SystemExit(main())
