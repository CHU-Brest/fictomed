from pathlib import Path

import polars as pl
import pytest

from fictomed.base import BasePipeline
from fictomed.sites.aphp import prompt
from fictomed.sites.aphp.prompt_sets import (
    resolve_prompt_set,
    snapshot_external_prompt_set,
)
from fictomed.sites.aphp.scenario import format_aphp_scenario


class _Pipeline(BasePipeline):
    def check_data(self):
        pass

    def load_data(self):
        return {}

    def get_fictive(self, data, **kwargs):
        return pl.DataFrame()

    def get_scenario(self, df):
        return df


def _stub_user_prompt(monkeypatch):
    monkeypatch.setattr(prompt, "make_user_prompt", lambda *_: "USER")


def _external_prompt_set(root: Path, *, two_stage: bool = False) -> Path:
    root.mkdir()
    (root / "manifest.yaml").write_text(
        "name: custom\n"
        'version: "2.1"\n'
        "workflows:\n"
        "  one_stage: true\n"
        f"  two_stage: {str(two_stage).lower()}\n",
        encoding="utf-8",
    )
    one_stage = root / "one_stage"
    one_stage.mkdir()
    (one_stage / "medical_inpatient.txt").write_text(
        "CUSTOM ONE STAGE", encoding="utf-8"
    )
    (root / "prefix.txt").write_text("CUSTOM PREFIX", encoding="utf-8")
    if two_stage:
        for stage in ("summary", "final"):
            stage_dir = root / stage
            stage_dir.mkdir()
            (stage_dir / "medical_inpatient.txt").write_text(
                f"CUSTOM {stage.upper()}", encoding="utf-8"
            )
    return root


def test_default_set_uses_run11_one_stage_prompts(monkeypatch):
    _stub_user_prompt(monkeypatch)
    df = pl.DataFrame({"template_name": ["medical_inpatient.txt"]})

    result = format_aphp_scenario(df, frozenset(), {})

    assert result["prompt_set_name"].to_list() == ["default"]
    assert result["prompt_workflow"].to_list() == ["one_stage"]
    assert result["prefix"].to_list() == ['{"CR": "']
    assert "Ta mission : la tâche inverse" in result["system_prompt"][0]


def test_old_set_preserves_historical_one_stage_columns(monkeypatch):
    _stub_user_prompt(monkeypatch)
    df = pl.DataFrame({"template_name": ["medical_inpatient.txt"]})

    result = format_aphp_scenario(
        df, frozenset(), {}, prompt_set="old", prompt_workflow="one_stage"
    )

    assert result["prompt_set_name"].to_list() == ["old"]
    assert result["prefix_len"][0] > 0
    assert "summary_system_prompt" not in result.columns
    assert "final_system_prompt" not in result.columns


def test_old_set_supports_two_stage(monkeypatch):
    _stub_user_prompt(monkeypatch)
    df = pl.DataFrame({"template_name": ["medical_inpatient.txt"]})

    result = format_aphp_scenario(
        df, frozenset(), {}, prompt_set="old", prompt_workflow="two_stage"
    )

    assert "résumé clinique contrôlé" in result["summary_system_prompt"][0]
    assert "documents médicaux finaux" in result["final_system_prompt"][0]
    assert "system_prompt" not in result.columns
    assert "prefix" not in result.columns


def test_default_set_rejects_two_stage():
    with pytest.raises(ValueError, match="ne prend pas en charge"):
        resolve_prompt_set(prompt_set="default", workflow="two_stage")


def test_external_prompt_set_is_loaded_and_traced(tmp_path, monkeypatch):
    _stub_user_prompt(monkeypatch)
    prompt_dir = _external_prompt_set(tmp_path / "custom")
    df = pl.DataFrame({"template_name": ["medical_inpatient.txt"]})

    result = format_aphp_scenario(
        df,
        frozenset(),
        {},
        prompt_dir=prompt_dir,
        prompt_workflow="one_stage",
    )

    assert result["system_prompt"].to_list() == ["CUSTOM ONE STAGE"]
    assert result["prefix"].to_list() == ["CUSTOM PREFIX"]
    assert result["prompt_set_name"].to_list() == ["custom"]
    assert result["prompt_set_version"].to_list() == ["2.1"]
    assert result["prompt_source"][0].startswith("external:")
    assert len(result["prompt_content_hash"][0]) == 64


def test_external_prompt_set_snapshot_is_content_addressed(tmp_path):
    prompt_dir = _external_prompt_set(tmp_path / "custom")
    selected = resolve_prompt_set(prompt_dir=prompt_dir)

    snapshot = snapshot_external_prompt_set(selected, tmp_path / "output")

    assert snapshot is not None
    assert snapshot.name.endswith(selected.content_hash[:12])
    assert (snapshot / "manifest.yaml").read_bytes() == (
        prompt_dir / "manifest.yaml"
    ).read_bytes()
    assert (snapshot / "one_stage" / "medical_inpatient.txt").read_text(
        encoding="utf-8"
    ) == "CUSTOM ONE STAGE"


def test_prompt_set_and_external_directory_are_mutually_exclusive(tmp_path):
    prompt_dir = _external_prompt_set(tmp_path / "custom")

    with pytest.raises(ValueError, match="ne peuvent pas"):
        resolve_prompt_set(prompt_set="old", prompt_dir=prompt_dir)


def test_every_old_template_exists_in_default_one_stage():
    old = resolve_prompt_set(prompt_set="old")
    default = resolve_prompt_set(prompt_set="default")
    old_names = {path.name for path in (old.root / "one_stage").glob("*.txt")}
    default_names = {
        path.name for path in (default.root / "one_stage").glob("*.txt")
    }

    assert old_names
    assert default_names == old_names


def test_invalid_workflow_is_rejected():
    with pytest.raises(ValueError, match="prompt_workflow"):
        _Pipeline({}, prompt_workflow="invalid")
