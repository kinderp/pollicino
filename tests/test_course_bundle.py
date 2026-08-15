from __future__ import annotations
import json
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[1]; BUNDLE_ROOT=REPO_ROOT/'course'/'pollicino-quarto-2026'; BUNDLE_PATH=BUNDLE_ROOT/'bundle.json'
def load_bundle(): return json.loads(BUNDLE_PATH.read_text(encoding='utf-8'))
def test_manifest_and_course_shape():
 b=load_bundle(); assert b['schema_version']=='1.0.0' and b['version']=='0.8.0'; u=b['content']['units']; assert len(u)==6 and [x['order'] for x in u]==list(range(1,7)) and sum(len(x['activities']) for x in u)==29
def test_manifest_paths_exist_and_stay_inside_bundle():
 for u in load_bundle()['content']['units']:
  for c in ('activities','materials','media','handouts'):
   for r in u.get(c,[]):
    p=Path(r); assert not p.is_absolute() and '..' not in p.parts; q=(BUNDLE_ROOT/p).resolve(); q.relative_to(BUNDLE_ROOT.resolve()); assert q.is_file(),r
def test_teacher_student_activity_parity():
 for u in load_bundle()['content']['units']:
  assert len(u['activities'])==len(u['materials'])==len(u['handouts'])
  for r in u['activities']:
   a=json.loads((BUNDLE_ROOT/r).read_text(encoding='utf-8')); assert a['schema_version']=='1.0' and a['contesto']['uda']==u['id'] and a['contesto']['percorso']=='pollicino-quarto-2026'
def test_all_udas_are_operational_packages():
 for u in load_bundle()['content']['units']:
  assert u.get('media'),u['id']
  for r in u['activities']:
   ap=BUNDLE_ROOT/r; a=json.loads(ap.read_text(encoding='utf-8')); types={x['type'] for x in a.get('assets',[])}; assert {'starter','visible_test','hidden_test','teacher_only','fixture'}<=types,r
   for asset in a['assets']:
    p=Path(asset['path']); assert not p.is_absolute() and '..' not in p.parts; q=(ap.parent/p).resolve(); q.relative_to(ap.parent.resolve()); assert q.is_file(),f"{r}: {asset['path']}"
    if asset['type'] in {'hidden_test','teacher_only','runner'}: assert asset.get('visibility')=='teacher'
def test_uda06_contains_real_codec_and_integrity_checks():
 u=next(x for x in load_bundle()['content']['units'] if x['id']=='uda-06-codec-ricerca'); assert u['media']==['notebooks/uda-06/pollicino-uda06-lab.ipynb']; c=(BUNDLE_ROOT/'activities/uda-06/l02/teacher/solution.py').read_text(); assert all(x in c for x in ('encode_symbols','decode_symbols','sha256','PolHeader')); h=(BUNDLE_ROOT/'activities/uda-06/l05/tests/test_hidden.py').read_text(); assert 'random_binary' in h
