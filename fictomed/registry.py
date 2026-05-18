from pathlib import Path

from fictomed.sites.brest.pipeline import BrestPipeline
from fictomed.sites.aphp.pipeline import APHPPipeline

PIPELINES = {
    "brest": BrestPipeline,
    "aphp": APHPPipeline,
}

CONFIG_DIR = Path(__file__).resolve().parent / "config"
