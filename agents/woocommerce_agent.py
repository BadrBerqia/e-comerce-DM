"""
Agent A2A WooCommerce – Extraction via REST API WooCommerce v3
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Endpoint: https://<site>/wp-json/wc/v3/products
Authentification : Consumer Key + Consumer Secret (Basic Auth)
"""

import base64
from .scraping_agent import BaseScrapingAgent, ProduitExtrait
from typing import Optional
import re


class WooCommerceAgent(BaseScrapingAgent):
    """
    Agent A2A spécialisé WooCommerce.
    Utilise l'API REST WooCommerce v3.
    Nécessite des clés API (consumer_key, consumer_secret).
    """

    def __init__(self, shop_url: str, consumer_key: str, consumer_secret: str,
                 shop_name: str = "", pays: str = ""):
        super().__init__(shop_url, agent_name=f"WooAgent[{shop_name or shop_url}]")
        self.consumer_key    = consumer_key
        self.consumer_secret = consumer_secret
        self.shop_name       = shop_name
        self.pays            = pays
        self.api_base        = f"{self.shop_url}/wp-json/wc/v3"

        # Authentification Basic HTTP
        credentials = f"{consumer_key}:{consumer_secret}"
        encoded     = base64.b64encode(credentials.encode()).decode()
        self.session.headers["Authorization"] = f"Basic {encoded}"

    def capabilities(self) -> dict:
        caps = super().capabilities()
        caps["plateforme"]   = "WooCommerce"
        caps["api_endpoint"] = f"{self.api_base}/products"
        caps["auth"]         = "Basic Auth (consumer_key:consumer_secret)"
        return caps

    # ── Implémentation ────────────────────────────────────────────────────────

    def get_categories(self) -> list[str]:
        """Récupère les catégories WooCommerce via /product_categories."""
        data = self.fetch_json(f"{self.api_base}/products/categories",
                               params={"per_page": 100, "hide_empty": True})
        if not data:
            return [f"{self.api_base}/products"]

        return [str(cat["id"]) for cat in data if cat.get("count", 0) > 0]

    def scrape_category(self, category_id: str, max_pages: int = 10) -> list[ProduitExtrait]:
        """Scrape les produits d'une catégorie WooCommerce."""
        produits = []
        page     = 1

        while page <= max_pages:
            data = self.fetch_json(
                f"{self.api_base}/products",
                params={
                    "category": category_id,
                    "per_page": 100,
                    "page":     page,
                    "status":   "publish",
                    "orderby":  "popularity",
                }
            )
            if not data:
                break

            for item in data:
                p = self._parse_product(item)
                if p:
                    produits.append(p)

            self.logger.info(f"Catégorie {category_id} | Page {page} -> {len(data)} produits")
            if len(data) < 100:
                break
            page += 1

        return produits

    def scrape_product(self, product_id: str) -> Optional[ProduitExtrait]:
        """Scrape un produit WooCommerce par son ID."""
        data = self.fetch_json(f"{self.api_base}/products/{product_id}")
        return self._parse_product(data) if data else None

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _parse_product(self, item: dict) -> Optional[ProduitExtrait]:
        try:
            prix       = float(item.get("regular_price") or item.get("price") or 0)
            sale_price = float(item.get("sale_price") or prix)
            remise     = round((prix - sale_price) / prix * 100, 1) if prix > sale_price else 0.0

            cats       = item.get("categories", [])
            categorie  = cats[0]["name"] if cats else "Autre"

            tags       = [t["name"] for t in item.get("tags", [])]

            # Attributs (couleur, taille)
            attrs      = {a["name"].lower(): a.get("options", []) for a in item.get("attributes", [])}
            couleur    = attrs.get("color", attrs.get("couleur", [""]))[0] if ("color" in attrs or "couleur" in attrs) else ""
            taille     = attrs.get("size", attrs.get("taille", [""]))[0] if ("size" in attrs or "taille" in attrs) else ""

            stock_qty  = int(item.get("stock_quantity") or 0)
            en_stock   = item.get("in_stock", stock_qty > 0)

            # Note et avis
            rating     = float(item.get("average_rating", 0) or 0)
            nb_reviews = int(item.get("rating_count", 0) or 0)

            return ProduitExtrait(
                product_id      = str(item.get("id", "")),
                nom             = item.get("name", ""),
                categorie       = categorie,
                marque_vendeur  = self.shop_name,
                prix            = prix,
                prix_promo      = sale_price,
                remise_pct      = remise,
                devise          = "EUR",
                rating          = rating,
                nb_reviews      = nb_reviews,
                en_stock        = en_stock,
                quantite_stock  = stock_qty,
                delai_livraison = "",
                description     = self._strip_html(item.get("description", "")),
                couleur         = couleur,
                taille          = taille,
                url             = item.get("permalink", ""),
                plateforme      = "WooCommerce",
                pays_shop       = self.pays,
                shop_name       = self.shop_name,
                tags            = tags,
            )
        except Exception as e:
            self.logger.warning(f"Parsing impossible pour produit {item.get('id')}: {e}")
            return None

    @staticmethod
    def _strip_html(html: str) -> str:
        return re.sub(r"<[^>]+>", " ", html).strip() if html else ""


# ── Exemple d'utilisation ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import pandas as pd

    agent = WooCommerceAgent(
        shop_url        = "https://demo.woothemes.com",
        consumer_key    = "ck_VOTRE_CLE",
        consumer_secret = "cs_VOTRE_SECRET",
        shop_name       = "WooDemo",
        pays            = "FR"
    )

    produits = agent.run(max_products=200)
    df = pd.DataFrame(agent.to_dict_list())
    print(df.head())
