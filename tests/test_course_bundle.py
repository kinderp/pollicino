from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = REPO_ROOT / "course" / "pollicino-quarto-2026"
BUNDLE_PATH = BUNDLE_ROOT / "bundle.json"


def load_bundle() -> dict:
    return json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))


def test_pollicino_bundle_uses_2cornot2c_manifest_version() -> None:
    bundle = load_bundle()
    assert bundle["schema_version"] == "1.0.0"
    assert bundle["id"] == "pollicino-quarto-2026"
    assert bundle["language"] == "it"
    assert bundle["version"] == "0.3.0"


def test_course_has_six_ordered_udas_and_29_lessons() -> None:
    bundle = load_bundle()
    units = bundle["content"]["units"]
    assert len(units) == 6
    assert [unit["order"] for unit in units] == list(range(1, 7))
    assert len({unit["id"] for unit in units}) == 6
    assert sum(len(unit.get("activities", [])) for unit in units) == 29


def test_all_manifest_content_paths_exist_inside_bundle() -> None:
    bundle = load_bundle()
    for unit in bundle["content"]["units"]:
        for collection in ("activities", "materials", "media", "handouts"):
            for relative in unit.get(collection, []):
                path = Path(relative)
                assert not path.is_absolute()
                assert ".." not in path.parts
                assert (BUNDLE_ROOT / path).is_file(), relative


def test_every_populated_uda_keeps_student_teacher_activity_parity() -> None:
    bundle = load_bundle()
    for unit in bundle["content"]["units"]:
        activities = unit.get("activities", [])
        handouts = unit.get("handouts", [])
        materials = unit.get("materials", [])
        assert activities, unit["id"]
        assert len(handouts) == len(activities), unit["id"]
        assert len(materials) == len(activities), unit["id"]
        for relative in activities:
            activity = json.loads((BUNDLE_ROOT / relative).read_text(encoding="utf-8"))
            assert activity["schema_version"] == "1.0"
            assert activity["contesto"]["uda"] == unit["id"]
            assert activity["contesto"]["percorso"] == "pollicino-quarto-2026"


def test_lesson_file_names_are_paired_by_number() -> None:
    bundle = load_bundle()
    for unit in bundle["content"]["units"]:
        activities = unit["activities"]
        materials = unit["materials"]
        handouts = unit["handouts"]
        assert [Path(p).name[:3] for p in activities] == [Path(p).name[:3] for p in materials]
        assert [Path(p).name[:3] for p in activities] == [Path(p).name[:3] for p in handouts]


def test_declared_activity_assets_exist_below_activity_folder() -> None:
    bundle = load_bundle()
    for unit in bundle["content"]["units"]:
        for relative in unit.get("activities", []):
            activity_path = BUNDLE_ROOT / relative
            activity = json.loads(activity_path.read_text(encoding="utf-8"))
            for asset in activity.get("assets", []):
                asset_path = Path(asset["path"])
                assert not asset_path.is_absolute()
                assert ".." not in asset_path.parts
                resolved = (activity_path.parent / asset_path).resolve()
                resolved.relative_to(activity_path.parent.resolve())
                assert resolved.is_file(), f"{relative}: {asset['path']}"


def test_uda01_operational_packages_have_student_and_teacher_assets() -> None:
    bundle = load_bundle()
    uda = next(unit for unit in bundle["content"]["units"] if unit["id"] == "uda-01-informazione")
    assert uda["media"] == ["notebooks/uda-01/pollicino-uda01-lab.ipynb"]
    for relative in uda["activities"]:
        activity = json.loads((BUNDLE_ROOT / relative).read_text(encoding="utf-8"))
        assets = activity.get("assets", [])
        types = {asset["type"] for asset in assets}
        assert "starter" in types
        assert "visible_test" in types
        assert "hidden_test" in types
        assert "teacher_only" in types
        assert any(asset["type"] == "fixture" for asset in assets)
        for asset in assets:
            if asset["type"] in {"hidden_test", "teacher_only", "runner"}:
                assert asset.get("visibility") == "teacher"
