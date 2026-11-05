import warnings
from pathlib import Path

from fictomed.sites.aphp.pipeline import APHPPipeline
from fictomed.sites.brest.pipeline import BrestPipeline

PIPELINES = {
    "pmsi_sampling": BrestPipeline,
    "profile_generation": APHPPipeline,
}

PIPELINE_ALIASES = {
    "brest": "pmsi_sampling",
    "aphp": "profile_generation",
}

PIPELINE_NAMES = (*PIPELINES, *PIPELINE_ALIASES)


def resolve_pipeline_name(name: str) -> str:
    canonical_name = PIPELINE_ALIASES.get(name, name)
    if name in PIPELINE_ALIASES:
        warnings.warn(
            f"Le pipeline '{name}' est déprécié ; utiliser '{canonical_name}'.",
            FutureWarning,
            stacklevel=2,
        )
    return canonical_name


CONFIG_DIR = Path(__file__).resolve().parent / "config"
