"""Brest pipeline — weighted PMSI sampling (SNDS source).

This module implements the Brest-specific logic for generating synthetic
medical reports from SNDS PMSI data. It inherits from the common
:class:`~pipelines.pipeline.BasePipeline` and overrides the specific methods
as needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import override

import polars as pl

from fictomed.base import BasePipeline
from fictomed.fictive import generate_fictive_stays
from fictomed.scenario import format_scenarios
from fictomed.sites.brest import constants
from fictomed.sites.brest.fictive import generate_brest_fictive
from fictomed.sites.brest.scenario import format_brest_scenario


class BrestPipeline(BasePipeline):
    """CHU Brest pipeline — weighted PMSI sampling (SNDS source).

    Source data is extracted via ``liabilities/extract_pmsi_tables_SNDS.sas``
    and placed as CSV files in the ``data.input`` directory configured in
    ``servers.yaml``.
    """

    name = "brest"

    SOURCES = constants.SOURCES

    # -- Data loading ------------------------------------------------------

    @override
    def check_data(self) -> None:
        """Convert PMSI CSV files to Parquet if not already present."""
        input_dir = Path(self.config["data"]["input"])
        print("Vérification des données d'entrée pour le pipeline Brest.")

        for name, csv_file in self.SOURCES.items():
            parquet = input_dir / f"{name}.parquet"
            if parquet.exists():
                print("Le fichier Parquet %s existe déjà.", parquet)
                continue
            csv_path = input_dir / csv_file
            if not csv_path.exists():
                raise FileNotFoundError(f"Le fichier CSV {csv_path} est introuvable.")
            print("Conversion du fichier CSV %s en Parquet.", csv_path)
            pl.read_csv(
                csv_path,
                separator=";",
                encoding="latin-1",
                infer_schema_length=10000,
            ).write_parquet(parquet)
            print("Fichier Parquet %s créé avec succès.", parquet)

        print("Les données de génération sont présentes et valides.")

    @override
    def load_data(self) -> dict[str, pl.LazyFrame]:
        """Load all PMSI Parquet files as LazyFrames."""
        input_dir = Path(self.config["data"]["input"])
        return {
            name: pl.scan_parquet(input_dir / f"{name}.parquet")
            for name in self.SOURCES
        }

    # -- Fictitious stay generation ----------------------------------------

    @override
    def get_fictive(
        self,
        data: dict[str, pl.LazyFrame],
        n_sejours: int = 1000,
        n_ccam: int = 3,
        n_das: int = 3,
        ghm5_pattern: str | None = None,
        **kwargs,
    ) -> pl.DataFrame:
        """Generate fictitious stays via weighted PMSI sampling.

        Returns
        -------
        pl.DataFrame
            Columns: generation_id, AGE, SEXE, GHM5, GHM5_CODE, DP, DP_CODE,
            CCAM (list[str]), DAS (list[str]), DMS (int).
        """
        return generate_fictive_stays(
            data,
            n_sejours=n_sejours,
            generate_fn=generate_brest_fictive,
            n_ccam=n_ccam,
            n_das=n_das,
            ghm5_pattern=ghm5_pattern,
        )

    @override
    def get_scenario(self, df: pl.DataFrame) -> pl.DataFrame:
        """Format fictitious stays as text scenarios for the LLM."""
        return format_scenarios(df, scenario_fn=format_brest_scenario)
