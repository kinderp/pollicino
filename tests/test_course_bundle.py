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


def test_all_manifest_content_paths_exist_inside_bundle() -> None:
    bundle = load_bundle()
    for unit in bundle["content"]["units"]:
        for collection in ("activities", "materials", "media", "handouts"):
            for relative in unit.get(collection, []):
                path = Path(relative)
                assert not path.is_absolute()
                assert ".." not in path.parts
                assert (BUNDLE_ROOT / path).is_file(), relative


def test_uda_01_keeps_student_teacher_activity_parity() -> None:
    bundle = load_bundle()
    unit = next(
        unit
        for unit in bundle["content"]["units"]
        if unit["id"] == "uda-01-informazione"
    )

    assert len(unit["activities"]) == 4
    assert len(unit["handouts"]) == len(unit["activities"])
    assert len(unit["materials"]) == len(unit["activities"])

    for relative in unit["activities"]:
        activity = json.loads((BUNDLE_ROOT / relative).read_text(encoding="utf-8"))
        assert activity["schema_version"] == "1.0"
        assert activity["contesto"]["uda"] == unit["id"]
