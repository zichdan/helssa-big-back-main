# Testing library/framework: pytest (and pytest-style assertions).
# These tests validate the configuration manifest added in the PR diff.
# Focus: schema correctness, internal consistency, edge cases around counts and categories.

import json
import re
from pathlib import Path
import copy
import pytest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "configuration_manifest.json"

@pytest.fixture(scope="module")
def manifest() -> dict:
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def test_top_level_keys_present_and_only_expected(manifest: dict) -> None:
    expected = {"app", "version", "created_at", "updated_at", "items", "categories", "progress"}
    assert set(manifest.keys()) == expected

def test_version_semver(manifest: dict) -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]) is not None

def test_dates_consistency_equal_initially(manifest: dict) -> None:
    assert isinstance(manifest["created_at"], str)
    assert isinstance(manifest["updated_at"], str)
    assert manifest["updated_at"] == manifest["created_at"]

def test_items_is_nonempty_list_and_all_required_fields(manifest: dict) -> None:
    items = manifest["items"]
    assert isinstance(items, list)
    assert len(items) == manifest["progress"]["total_items"]
    for i, item in enumerate(items):
        for key in ("id", "title", "description", "done", "category"):
            assert key in item, f"Missing '{key}' on item index {i}"
        assert isinstance(item["id"], str)
        assert item["id"].strip()
        assert isinstance(item["title"], str)
        assert item["title"].strip()
        assert isinstance(item["description"], str)
        assert item["description"].strip()
        assert isinstance(item["done"], bool)
        assert isinstance(item["category"], str)
        assert item["category"].strip()

def test_item_ids_unique(manifest: dict) -> None:
    ids = [it["id"] for it in manifest["items"]]
    assert len(ids) == len(set(ids)), "Duplicate item IDs detected"

def test_categories_cover_all_items(manifest: dict) -> None:
    cats = set(manifest["categories"].keys())
    used = {it["category"] for it in manifest["items"]}
    assert used.issubset(cats), f"Unknown categories used: {used - cats}"

def test_required_placeholders_allowed_when_present(manifest: dict) -> None:
    allowed_required = {"{{USES_TEXT_PROCESSING}}", "{{USES_SPEECH_PROCESSING}}"}
    for it in manifest["items"]:
        if "required" in it:
            assert it["required"] in allowed_required

def test_progress_computation_consistent(manifest: dict) -> None:
    items = manifest["items"]
    completed = sum(1 for it in items if it["done"] is True)
    total = manifest["progress"]["total_items"]
    assert total == len(items)
    assert manifest["progress"]["completed"] == completed
    expected_pct = int((completed / total) * 100) if total else 0
    assert manifest["progress"]["percentage"] == expected_pct

@pytest.mark.parametrize(("toggle_text", "toggle_speech", "expected_required"), [
    (True, False, {"text_processing_core"}),
    (False, True, {"speech_processing_core"}),
    (True, True, {"text_processing_core", "speech_processing_core"}),
    (False, False, set()),
])
def test_required_feature_toggles_effect_on_required_items(
    manifest: dict,
    *,
    toggle_text: bool,
    toggle_speech: bool,
    expected_required: set,
) -> None:
    # Simulate resolving placeholders → booleans then filtering required components
    data = copy.deepcopy(manifest)
    for it in data["items"]:
        req = it.get("required")
        if req == "{{USES_TEXT_PROCESSING}}":
            it["required"] = bool(toggle_text)
        elif req == "{{USES_SPEECH_PROCESSING}}":
            it["required"] = bool(toggle_speech)

    actually_required = {it["id"] for it in data["items"] if it.get("required") is True}
    assert actually_required == expected_required

def test_localized_category_labels_are_nonempty_strings(manifest: dict) -> None:
    for key, label in manifest["categories"].items():
        assert isinstance(label, str)
        assert label.strip(), f"Empty translation for category '{key}'"

def test_no_extra_top_level_fields(manifest: dict) -> None:
    unexpected = set(manifest.keys()) - {
        "app", "version", "created_at", "updated_at", "items", "categories", "progress"
    }
    assert not unexpected

def test_manifest_is_valid_json_file_on_disk() -> None:
    # Ensure fixture is valid JSON and readable
    raw = FIXTURE_PATH.read_text(encoding="utf-8")
    obj = json.loads(raw)
    assert isinstance(obj, dict)
    assert "items" in obj
    assert isinstance(obj["items"], list)

def test_percentage_edge_cases_zero_total() -> None:
    # Edge case: zero total items implies 0 percentage regardless of completed
    obj = {"progress": {"total_items": 0, "completed": 0, "percentage": 0}, "items": []}
    total = obj["progress"]["total_items"]
    completed = obj["progress"]["completed"]
    expected_pct = int((completed / total) * 100) if total else 0
    assert obj["progress"]["percentage"] == expected_pct

# Note on scope:
# - Follows existing test style using pytest.
# - Serializers/models intentionally not tested per request; this file validates configuration (manifest) invariants.
# - Views/services references from the PR description do not apply to this JSON manifest; tests focus on the diff content.