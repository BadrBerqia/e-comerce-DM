"""
Coordinateur A2A – Orchestration de plusieurs agents de scraping
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Le coordinateur :
  1. Enregistre les agents disponibles (pattern registre)
  2. Lance les agents en parallèle ou séquentiellement
  3. Fusionne et déduplique les résultats
  4. Exporte le dataset consolidé
"""

import pandas as pd
import logging
import concurrent.futures
import os
from .scraping_agent import BaseScrapingAgent, ProduitExtrait

logging.basicConfig(level=logging.INFO, format="%(asctime)s [Coordinator] %(levelname)s: %(message)s")
logger = logging.getLogger("Coordinator")


class AgentCoordinator:
    """
    Coordinateur central du pipeline A2A.
    Orchestre plusieurs agents de scraping hétérogènes.
    """

    def __init__(self, output_dir: str = "data"):
        self.agents: list[BaseScrapingAgent] = []
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def register(self, agent: BaseScrapingAgent) -> "AgentCoordinator":
        """Enregistre un agent dans le coordinateur (pattern builder)."""
        self.agents.append(agent)
        logger.info(f"Agent enregistré : {agent.agent_name}")
        return self   # permet le chaînage

    def run_all_sequential(self, max_products_per_agent: int = 500) -> pd.DataFrame:
        """Lance tous les agents séquentiellement et fusionne les résultats."""
        all_records = []
        for agent in self.agents:
            try:
                produits = agent.run(max_products=max_products_per_agent)
                all_records.extend(agent.to_dict_list())
                logger.info(f"{agent.agent_name} -> {len(produits)} produits collectés")
            except Exception as e:
                logger.error(f"Erreur agent {agent.agent_name}: {e}")

        return self._consolidate(all_records)

    def run_all_parallel(self, max_products_per_agent: int = 500,
                         max_workers: int = 4) -> pd.DataFrame:
        """Lance tous les agents en parallèle (threads I/O)."""
        all_records = []

        def run_agent(agent):
            try:
                agent.run(max_products=max_products_per_agent)
                return agent.to_dict_list()
            except Exception as e:
                logger.error(f"Erreur agent {agent.agent_name}: {e}")
                return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(run_agent, a): a for a in self.agents}
            for future in concurrent.futures.as_completed(futures):
                records = future.result()
                all_records.extend(records)
                logger.info(f"Agent terminé : {len(records)} produits")

        return self._consolidate(all_records)

    def _consolidate(self, records: list[dict]) -> pd.DataFrame:
        """Fusionne, déduplique et nettoie le dataset consolidé."""
        if not records:
            logger.warning("Aucun produit collecté par les agents.")
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # Déduplification par URL et par (nom + shop)
        before = len(df)
        df.drop_duplicates(subset=["url"], keep="first", inplace=True)
        df.drop_duplicates(subset=["nom", "shop_name"], keep="first", inplace=True)
        logger.info(f"Déduplification : {before} -> {len(df)} produits")

        # Types
        df["prix"]       = pd.to_numeric(df["prix"], errors="coerce").fillna(0)
        df["rating"]     = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
        df["nb_reviews"] = pd.to_numeric(df["nb_reviews"], errors="coerce").fillna(0).astype(int)

        # Sauvegarde
        out_path = os.path.join(self.output_dir, "products_consolidated.csv")
        df.to_csv(out_path, index=False, encoding="utf-8")
        logger.info(f"Dataset consolidé sauvegardé : {out_path} ({len(df)} lignes)")
        return df

    def capabilities_report(self) -> list[dict]:
        """Retourne le rapport de capacités de tous les agents enregistrés."""
        return [a.capabilities() for a in self.agents]


# ── Démonstration avec données simulées ──────────────────────────────────────
if __name__ == "__main__":
    from .shopify_agent import ShopifyAgent

    coordinator = AgentCoordinator(output_dir="data")

    # Dans un vrai projet, remplacer par de vraies URLs de stores Shopify publics
    agent1 = ShopifyAgent("https://store.ilovecreatives.com", "ILoveCreatives", "USA")
    agent2 = ShopifyAgent("https://www.gymshark.com",         "Gymshark",       "UK")

    coordinator.register(agent1).register(agent2)

    print("Capacités des agents :")
    for cap in coordinator.capabilities_report():
        print(f"  - {cap['agent_name']} [{cap['plateforme']}] -> {cap['api_endpoint']}")

    # df = coordinator.run_all_sequential(max_products_per_agent=100)
    # print(df.head())
