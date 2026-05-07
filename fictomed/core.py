from fictomed.config import load_config
from fictomed.registry import CONFIG_DIR, PIPELINES


def generate(
    pipeline_name: str,
    n_sejours: int = 1000,
    n_ccam: int = 1,
    n_das: int = 5,
    ghm5_pattern: str | None = None,
) -> None:
    """Orchestrate an end-to-end synthetic medical-report generation run."""
    if pipeline_name not in PIPELINES:
        raise ValueError(
            f"Pipeline inconnu : '{pipeline_name}'. "
            f"Valeurs acceptées : {list(PIPELINES.keys())}"
        )

    config = load_config(CONFIG_DIR / "servers.yaml")

    pipeline = PIPELINES[pipeline_name](
        config=config["pipelines"][pipeline_name],
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
    return df
