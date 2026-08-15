from __future__ import annotations
import json
from pathlib import Path
REPO_ROOT=Path(__file__).resolve().parents[1]
BUNDLE_ROOT=REPO_ROOT/"course"/"pollicino-quarto-2026"
BUNDLE_PATH=BUNDLE_ROOT/"bundle.json"

def load_bundle(): return json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))

def test_manifest():
 b=load_bundle(); assert b["schema_version"]=="1.0.0"; assert b["id"]=="pollicino-quarto-2026"; assert b["language"]=="it"; assert b["version"]=="0.4.0"

def test_course_shape():
 u=load_bundle()["content"]["units"]; assert len(u)==6; assert [x["order"] for x in u]==list(range(1,7)); assert sum(len(x.get("activities",[])) for x in u)==29

def test_manifest_paths_exist():
 for unit in load_bundle()["content"]["units"]:
  for collection in ("activities","materials","media","handouts"):
   for relative in unit.get(collection,[]):
    p=Path(relative); assert not p.is_absolute(); assert ".." not in p.parts; assert (BUNDLE_ROOT/p).is_file(),relative

def test_parity_and_context():
 for unit in load_bundle()["content"]["units"]:
  a=unit.get("activities",[]); h=unit.get("handouts",[]); m=unit.get("materials",[]); assert a; assert len(a)==len(h)==len(m)
  for relative in a:
   obj=json.loads((BUNDLE_ROOT/relative).read_text(encoding="utf-8")); assert obj["schema_version"]=="1.0"; assert obj["contesto"]["uda"]==unit["id"]; assert obj["contesto"]["percorso"]=="pollicino-quarto-2026"

def test_asset_paths():
 for unit in load_bundle()["content"]["units"]:
  for relative in unit.get("activities",[]):
   ap=BUNDLE_ROOT/relative; obj=json.loads(ap.read_text(encoding="utf-8"))
   for asset in obj.get("assets",[]):
    p=Path(asset["path"]); assert not p.is_absolute(); assert ".." not in p.parts; resolved=(ap.parent/p).resolve(); resolved.relative_to(ap.parent.resolve()); assert resolved.is_file(),f"{relative}: {asset['path']}"

def test_operational_udas():
 expected={"uda-01-informazione":"notebooks/uda-01/pollicino-uda01-lab.ipynb","uda-02-compressione-predizione":"notebooks/uda-02/pollicino-uda02-lab.ipynb"}
 for uid,notebook in expected.items():
  unit=next(x for x in load_bundle()["content"]["units"] if x["id"]==uid); assert unit["media"]==[notebook]
  for relative in unit["activities"]:
   obj=json.loads((BUNDLE_ROOT/relative).read_text(encoding="utf-8")); assets=obj.get("assets",[]); types={a["type"] for a in assets}; assert {"starter","visible_test","hidden_test","teacher_only"}<=types; assert any(a["type"]=="fixture" for a in assets); assert obj.get("linguaggio")=="python"
   for asset in assets:
    if asset["type"] in {"hidden_test","teacher_only","runner"}: assert asset.get("visibility")=="teacher"

def test_uda02_final_reference():
 unit=next(x for x in load_bundle()["content"]["units"] if x["id"]=="uda-02-compressione-predizione"); assert len(unit["activities"])==5; obj=json.loads((BUNDLE_ROOT/unit["activities"][-1]).read_text(encoding="utf-8")); assert any(a["type"]=="example" for a in obj["assets"])
