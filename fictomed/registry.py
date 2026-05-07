from pathlib import Path

from fictomed.sites.brest.pipeline import BrestPipeline

PIPELINES = {
    "brest": BrestPipeline,
}

CONFIG_DIR = Path(__file__).resolve().parent / "config"
