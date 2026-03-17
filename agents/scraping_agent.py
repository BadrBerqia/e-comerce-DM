"""
Agent A2A (Agent-to-Agent) de base – Scraping e-commerce
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Architecture A2A :
  - Chaque agent est autonome, spécialisé sur une plateforme (Shopify / WooCommerce)
  - Les agents communiquent via un coordinateur central (agent_coordinator.py)
  - Pattern : BaseScrapingAgent -> ShopifyAgent / WooCommerceAgent

Outils utilisés : requests, BeautifulSoup, Playwright (optionnel pour JS dynamique)
"""

import requests
import time
import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")


@dataclass
class ProduitExtrait:
    """Structure de données représentant un produit extrait."""
    product_id:       str   = ""
    nom:              str   = ""
    categorie:        str   = ""
    marque_vendeur:   str   = ""
    prix:             float = 0.0
    prix_promo:       float = 0.0
    remise_pct:       float = 0.0
    devise:           str   = "USD"
    rating:           float = 0.0
    nb_reviews:       int   = 0
    en_stock:         bool  = True
    quantite_stock:   int   = 0
    delai_livraison:  str   = ""
    description:      str   = ""
    couleur:          str   = ""
    taille:           str   = ""
    url:              str   = ""
    plateforme:       str   = ""
    pays_shop:        str   = ""
    shop_name:        str   = ""
    tags:             list  = field(default_factory=list)


class BaseScrapingAgent(ABC):
    """
    Agent de base pour le scraping e-commerce.
    Implémente le pattern A2A : chaque agent déclare ses capacités
    et peut être orchestré par le coordinateur.
    """

    def __init__(self, shop_url: str, agent_name: str, delay: float = 1.5):
        self.shop_url   = shop_url.rstrip("/")
        self.agent_name = agent_name
        self.delay      = delay          # délai entre requêtes (bonnes pratiques)
        self.session    = requests.Session()
        self.logger     = logging.getLogger(agent_name)
        self.produits_extraits: list[ProduitExtrait] = []

        # En-têtes HTTP réalistes
        self.session.headers.update({
            "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    # ── Méthodes abstraites à implémenter par chaque agent spécialisé ─────────

    @abstractmethod
    def get_categories(self) -> list[str]:
        """Retourne la liste des catégories disponibles sur le site."""
        ...

    @abstractmethod
    def scrape_category(self, category_url: str, max_pages: int = 5) -> list[ProduitExtrait]:
        """Scrape tous les produits d'une catégorie."""
        ...

    @abstractmethod
    def scrape_product(self, product_url: str) -> Optional[ProduitExtrait]:
        """Scrape le détail d'un produit."""
        ...

    # ── Méthodes communes ─────────────────────────────────────────────────────

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Télécharge une page HTML et retourne un objet BeautifulSoup."""
        try:
            self.logger.info(f"GET {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            time.sleep(self.delay)
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            self.logger.error(f"Erreur lors du fetch de {url} : {e}")
            return None

    def fetch_json(self, url: str, params: dict = None) -> Optional[dict]:
        """Récupère une réponse JSON (pour les APIs REST)."""
        try:
            self.logger.info(f"API GET {url}")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            time.sleep(self.delay)
            return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            self.logger.error(f"Erreur API {url} : {e}")
            return None

    def run(self, max_products: int = 500) -> list[ProduitExtrait]:
        """Lance le scraping complet du shop."""
        self.logger.info(f"Démarrage de l'agent {self.agent_name} sur {self.shop_url}")
        categories = self.get_categories()
        self.logger.info(f"{len(categories)} catégorie(s) trouvée(s)")

        for cat_url in categories:
            produits = self.scrape_category(cat_url)
            self.produits_extraits.extend(produits)
            if len(self.produits_extraits) >= max_products:
                break

        self.logger.info(f"Extraction terminée : {len(self.produits_extraits)} produits")
        return self.produits_extraits

    def to_dict_list(self) -> list[dict]:
        return [vars(p) for p in self.produits_extraits]

    def capabilities(self) -> dict:
        """Décrit les capacités de cet agent (utile pour A2A / MCP)."""
        return {
            "agent_name":  self.agent_name,
            "plateforme":  "base",
            "methodes":    ["get_categories", "scrape_category", "scrape_product", "run"],
            "shop_url":    self.shop_url,
        }
