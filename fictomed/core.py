from datetime import datetime
from pathlib import Path

import polars as pl

from fictomed.config import load_config
from fictomed.registry import (
    CONFIG_DIR,
    PIPELINE_ALIASES,
    PIPELINE_NAMES,
    PIPELINES,
    resolve_pipeline_name,
)


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
    requested_pipeline_name = pipeline_name
    pipeline_name = resolve_pipeline_name(pipeline_name)
    if pipeline_name not in PIPELINES:
        raise ValueError(
            f"Pipeline inconnu : '{requested_pipeline_name}'. "
            f"Valeurs acceptées : {list(PIPELINE_NAMES)}"
        )
    if pipeline_name != "profile_generation" and (
        prompt_workflow != "one_stage"
        or prompt_set != "default"
        or prompt_dir is not None
    ):
        raise ValueError(
            "Les options prompt_workflow, prompt_set et prompt_dir "
            "sont réservées au pipeline profile_generation"
        )
    if config_file:
        config = load_config(config_file)
    else:
        config = load_config(CONFIG_DIR / "servers.yaml")

    pipeline_configs = config["pipelines"]
    config_name = pipeline_name
    if config_name not in pipeline_configs:
        legacy_name = next(
            (
                alias
                for alias, canonical in PIPELINE_ALIASES.items()
                if canonical == pipeline_name and alias in pipeline_configs
            ),
            None,
        )
        if legacy_name is None:
            raise KeyError(
                f"Configuration absente pour le pipeline '{pipeline_name}'"
            )
        config_name = legacy_name

    pipeline = PIPELINES[pipeline_name](
        config=pipeline_configs[config_name],
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

        if pipeline_name == "profile_generation" and prompt_dir is not None:
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
