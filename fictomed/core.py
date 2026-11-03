from datetime import datetime
from pathlib import Path

import polars as pl

from fictomed.config import load_config
from fictomed.registry import CONFIG_DIR, PIPELINES


def generate(
    pipeline_name: str,
    n_sejours: int = 1000,
    n_ccam: int = 1,
    n_das: int = 5,
    ghm5_pattern: str | None = None,
    config_file: str | None = None,
    prompt_workflow: str = "one_stage",
    prompt_set: str = "default",
    prompt_dir: str | Path | None = None,
) -> pl.DataFrame:
    """Orchestrate an end-to-end synthetic medical-report generation run."""
    if pipeline_name not in PIPELINES:
        raise ValueError(
            f"Pipeline inconnu : '{pipeline_name}'. "
            f"Valeurs acceptées : {list(PIPELINES.keys())}"
        )
    if config_file:
        config = load_config(config_file)
    else:
        config = load_config(CONFIG_DIR / "servers.yaml")

    pipeline = PIPELINES[pipeline_name](
        config=config["pipelines"][pipeline_name],
        prompt_workflow=prompt_workflow,
        prompt_set=prompt_set,
        prompt_dir=prompt_dir,
    )

    pipeline.check_data()
    data = pipeline.load_data()

    df = pipeline.get_fictive(
        data,
        n_sejours=n_sejours,
        n_ccam=n_ccam,
        n_das=n_das,
        ghm5_pattern=ghm5_pattern,
    )
    df = pipeline.get_scenario(df)

    output_dir = pipeline.config.get("data", {}).get("output")
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / (
            f"{pipeline_name}_scenarios_{df.height}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        )

        df.write_parquet(output_path)
        print(f"Scénarios sauvegardés dans {output_path}")

        if pipeline_name == "aphp" and prompt_dir is not None:
            from fictomed.sites.aphp.prompt_sets import (
                resolve_prompt_set,
                snapshot_external_prompt_set,
            )

            resolved_prompt_set = resolve_prompt_set(
                prompt_set=prompt_set,
                prompt_dir=prompt_dir,
                workflow=prompt_workflow,
            )
            snapshot_path = snapshot_external_prompt_set(
                resolved_prompt_set,
                output_dir,
            )
            if snapshot_path is not None:
                print(f"Jeu de prompts sauvegardé dans {snapshot_path}")

    return df
