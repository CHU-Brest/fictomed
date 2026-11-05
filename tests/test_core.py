import polars as pl
import pytest

import fictomed.core as core
from fictomed.core import generate
from fictomed.registry import PIPELINES, resolve_pipeline_name


class DummyPipeline:
    def __init__(self, config, **kwargs):
        self.config = config

    def check_data(self):
        pass

    def load_data(self):
        return {}

    def get_fictive(self, data, **kwargs):
        return pl.DataFrame({"generation_id": ["1"]})

    def get_scenario(self, df):
        return df


@pytest.mark.parametrize(
    "options",
    [
        {"prompt_workflow": "two_stage"},
        {"prompt_set": "old"},
        {"prompt_dir": "/tmp/prompts"},
    ],
)
def test_prompt_options_are_restricted_to_profile_generation(options):
    with pytest.raises(ValueError, match="profile_generation"):
        generate("pmsi_sampling", **options)


def test_registry_uses_descriptive_pipeline_names():
    assert set(PIPELINES) == {"pmsi_sampling", "profile_generation"}


@pytest.mark.parametrize(
    ("legacy_name", "canonical_name"),
    [
        ("brest", "pmsi_sampling"),
        ("aphp", "profile_generation"),
    ],
)
def test_legacy_pipeline_names_are_deprecated_aliases(
    legacy_name, canonical_name
):
    with pytest.warns(FutureWarning, match=canonical_name):
        assert resolve_pipeline_name(legacy_name) == canonical_name


def test_legacy_pipeline_name_accepts_legacy_config_key(monkeypatch):
    monkeypatch.setattr(
        core,
        "PIPELINES",
        {"profile_generation": DummyPipeline},
    )
    monkeypatch.setattr(
        core,
        "load_config",
        lambda _: {"pipelines": {"aphp": {"data": {}}}},
    )

    with pytest.warns(FutureWarning, match="profile_generation"):
        result = core.generate("aphp", config_file="servers.yaml")

    assert result["generation_id"].to_list() == ["1"]
