"""AP-HP pipeline — ATIH PMSI sampling → clinical scenario → LLM report.

This module implements the AP-HP-specific logic for generating synthetic
medical reports from ATIH PMSI data. It inherits from the common
:class:`~fictomed.pipeline.BasePipeline` and overrides the specific methods
as needed.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, override

import polars as pl


from fictomed.base import BasePipeline
from fictomed.fictive import generate_fictive_stays
from fictomed.scenario import format_scenarios
from fictomed.sites.aphp import loader, managment
from fictomed.sites.aphp import scenario as sc
from fictomed.sites.aphp.fictive import generate_aphp_fictive
from fictomed.sites.aphp.scenario import format_aphp_scenario




class APHPPipeline(BasePipeline):
    """AP-HP pipeline — ATIH/PMSI-based synthetic CRH generation.

    Source data (``scenarios_*.parquet``, ``bn_pmsi_related_diag_*.csv``,
    ``bn_pmsi_procedures_*.csv``) must be placed in the directory set by
    ``config["data"]["input"]`` (see ``config/servers.yaml``).
    """

    name = "aphp"

    # Stash for context objects built during get_fictive, re-used by get_scenario
    _sc_ctx: sc.ScenarioContext | None = None
    _mg_ctx: managment.ManagmentContext | None = None
    _atih_rules: dict[str, dict] | None = None

    # ------------------------------------------------------------------
    # 1 — check_data
    # ------------------------------------------------------------------

    @override
    def check_data(self) -> None:
        """Verify that AP-HP PMSI input and referentials are present."""
        print("Vérification des données d'entrée pour le pipeline AP-HP.")

        input_dir = Path(self.config["data"]["input"])
        if not input_dir.is_dir():
            raise FileNotFoundError(
                f"Le répertoire de données AP-HP est introuvable : {input_dir}"
            )

        print(f"Chargement des fichiers PMSI depuis {input_dir}.")
        loader.load_pmsi(input_dir)
        print("Fichiers PMSI chargés avec succès.")

        referentials_dir = Path(self.config["data"]["referentials"])
        if not referentials_dir.is_dir():
            raise FileNotFoundError(
                f"Le répertoire des référentiels AP-HP est introuvable : {referentials_dir}"
            )

        print(f"Données AP-HP présentes dans {input_dir}.")

    # ------------------------------------------------------------------
    # 2 — load_data
    # ------------------------------------------------------------------

    @override
    def load_data(self) -> dict[str, pl.LazyFrame]:
        """Return all referentials + PMSI extracts as ``LazyFrame`` objects."""
        return loader.load_data(
            self.config["data"]["input"],
            self.config["data"]["referentials"],
        )

    # ------------------------------------------------------------------
    # 3 — get_fictive
    # ------------------------------------------------------------------

    @override
    def get_fictive(
        self,
        data: dict[str, pl.LazyFrame],
        n_sejours: int = 10,
        seed: int | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame:
        """Sample *n_sejours* PMSI profiles and build one scenario dict per stay.

        Parameters
        ----------
        data:
            Dict returned by :meth:`load_data`.
        n_sejours:
            Number of fictitious stays to generate.
        seed:
            Optional integer seed for reproducibility (Python RNG + NumPy).

        Returns
        -------
        pl.DataFrame
            One row per scenario. Contains all clinical fields plus
            ``generation_id``, ``situa``, ``coding_rule``, ``template_name``.
        """
        return generate_fictive_stays(
            data,
            n_sejours=n_sejours,
            generate_fn=generate_aphp_fictive,
            seed=seed,
        )

    # ------------------------------------------------------------------
    # 4 — get_scenario
    # ------------------------------------------------------------------

    @override
    def get_scenario(self, df: pl.DataFrame) -> pl.DataFrame:
        """Add ``scenario`` (user prompt) and ``system_prompt`` columns to *df*.

        Requires :meth:`get_fictive` to have been called first (it stashes the
        context objects on ``self``).
        """
        # Load ATIH rules for scenario formatting
        atih_rules = loader.load_atih_rules()

        # Rebuild context to get cancer codes (this could be optimized)
        data = self.load_data()
        sc_ctx = sc.build_context(data)

        df = format_scenarios(
            df,
            scenario_fn=format_aphp_scenario,
            cancer_codes=sc_ctx.cancer_codes,
            atih_rules=atih_rules,
        )

        return df
    
 

    