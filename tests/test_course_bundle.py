from __future__ import annotations
import json
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[1];BUNDLE_ROOT=REPO_ROOT/'course'/'pollicino-quarto-2026';BUNDLE_PATH=BUNDLE_ROOT/'bundle.json'
def load_bundle():return json.loads(BUNDLE_PATH.read_text(encoding='utf-8'))
def test_manifest_and_course_shape():
 b=load_bundle();assert b['schema_version']=='1.0.0';assert b['version']=='0.6.0';u=b['content']['units'];assert len(u)==6;assert [x['order'] for x in u]==list(range(1,7));assert sum(len(x.get('activities',[])) for x in u)==29
def test_manifest_paths_exist_and_stay_inside_bundle():
 for u in load_bundle()['content']['units']:
  for c in ('activities','materials','media','handouts'):
   for rel in u.get(c,[]):
    p=Path(rel);assert not p.is_absolute() and '..' not in p.parts;resolved=(BUNDLE_ROOT/p).resolve();resolved.relative_to(BUNDLE_ROOT.resolve());assert resolved.is_file(),rel
def test_teacher_student_activity_parity():
 for u in load_bundle()['content']['units']:
  assert len(u['activities'])==len(u['materials'])==len(u['handouts'])
  for rel in u['activities']:
   a=json.loads((BUNDLE_ROOT/rel).read_text());assert a['schema_version']=='1.0';assert a['contesto']['uda']==u['id'];assert a['contesto']['percorso']=='pollicino-quarto-2026'
def test_operational_udas_have_complete_asset_packages():
 operational={'uda-01-informazione','uda-02-compressione-predizione','uda-03-reti-neurali','uda-04-transformer'}
 for u in load_bundle()['content']['units']:
  if u['id'] not in operational:continue
  assert u.get('media'),u['id']
  for rel in u['activities']:
   ap=BUNDLE_ROOT/rel;a=json.loads(ap.read_text());types={x['type'] for x in a.get('assets',[])};assert {'starter','visible_test','hidden_test','teacher_only','fixture'}<=types,rel
   for asset in a['assets']:
    p=Path(asset['path']);assert not p.is_absolute() and '..' not in p.parts;resolved=(ap.parent/p).resolve();resolved.relative_to(ap.parent.resolve());assert resolved.is_file(),f"{rel}: {asset['path']}"
    if asset['type'] in {'hidden_test','teacher_only','runner'}:assert asset.get('visibility')=='teacher'
def test_uda04_explicitly_tests_causality():
 u=next(x for x in load_bundle()['content']['units'] if x['id']=='uda-04-transformer');assert u['media']==['notebooks/uda-04/pollicino-uda04-lab.ipynb'];causal=(BUNDLE_ROOT/'activities/uda-04/l03/tests/test_public.py').read_text();tiny=(BUNDLE_ROOT/'activities/uda-04/l05/tests/test_public.py').read_text();assert 'future_change_does_not_change_prefix' in causal;assert 'test_causality' in tiny
