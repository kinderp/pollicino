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
    assert bundle["version"] == "0.2.0"


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
