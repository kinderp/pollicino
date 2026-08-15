from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parents[1]
BUNDLE_ROOT=REPO_ROOT/'course'/'pollicino-quarto-2026'
BUNDLE_PATH=BUNDLE_ROOT/'bundle.json'

def load_bundle(): return json.loads(BUNDLE_PATH.read_text(encoding='utf-8'))

def test_manifest_and_course_shape():
    b=load_bundle(); assert b['schema_version']=='1.0.0'; assert b['version']=='0.5.0'
    units=b['content']['units']; assert len(units)==6; assert [u['order'] for u in units]==list(range(1,7))
    assert sum(len(u.get('activities',[])) for u in units)==29

def test_manifest_paths_exist_and_stay_inside_bundle():
    b=load_bundle()
    for u in b['content']['units']:
        for collection in ('activities','materials','media','handouts'):
            for relative in u.get(collection,[]):
                p=Path(relative); assert not p.is_absolute(); assert '..' not in p.parts
                resolved=(BUNDLE_ROOT/p).resolve(); resolved.relative_to(BUNDLE_ROOT.resolve()); assert resolved.is_file(),relative

def test_teacher_student_activity_parity():
    for u in load_bundle()['content']['units']:
        assert len(u['activities'])==len(u['materials'])==len(u['handouts'])
        for relative in u['activities']:
            a=json.loads((BUNDLE_ROOT/relative).read_text(encoding='utf-8'))
            assert a['schema_version']=='1.0'; assert a['contesto']['uda']==u['id']; assert a['contesto']['percorso']=='pollicino-quarto-2026'

def test_operational_udas_have_complete_asset_packages():
    operational={'uda-01-informazione','uda-02-compressione-predizione','uda-03-reti-neurali'}
    for u in load_bundle()['content']['units']:
        if u['id'] not in operational: continue
        assert u.get('media'),u['id']
        for relative in u['activities']:
            activity_path=BUNDLE_ROOT/relative; a=json.loads(activity_path.read_text(encoding='utf-8'))
            types={x['type'] for x in a.get('assets',[])}
            assert {'starter','visible_test','hidden_test','teacher_only','fixture'} <= types, relative
            for asset in a['assets']:
                p=Path(asset['path']); assert not p.is_absolute(); assert '..' not in p.parts
                resolved=(activity_path.parent/p).resolve(); resolved.relative_to(activity_path.parent.resolve()); assert resolved.is_file(),f"{relative}: {asset['path']}"
                if asset['type'] in {'hidden_test','teacher_only','runner'}: assert asset.get('visibility')=='teacher'
