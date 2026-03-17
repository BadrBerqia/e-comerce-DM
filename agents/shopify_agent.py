"""
Agent A2A Shopify – Extraction via Storefront JSON API
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Shopify expose automatiquement /products.json sur tout store public.
Endpoint: https://<shop>.myshopify.com/products.json?limit=250&page=N
"""

from .scraping_agent import BaseScrapingAgent, ProduitExtrait
from typing import Optional
import re


class ShopifyAgent(BaseScrapingAgent):
    """
    Agent A2A spécialisé Shopify.
    Utilise l'API JSON native de Shopify (pas besoin de clé pour les stores publics).
    """

    def __init__(self, shop_url: str, shop_name: str = "", pays: str = ""):
        super().__init__(shop_url, agent_name=f"ShopifyAgent[{shop_name or shop_url}]")
        self.shop_name = shop_name
        self.pays      = pays

    def capabilities(self) -> dict:
        caps = super().capabilities()
        caps["plateforme"] = "Shopify"
        caps["api_endpoint"] = f"{self.shop_url}/products.json"
        return caps

    # ── Implémentation des méthodes abstraites ────────────────────────────────

    def get_categories(self) -> list[str]:
        """
        Récupère les collections (catégories) via /collections.json.
        Retourne une liste d'URLs de collections.
        """
        data = self.fetch_json(f"{self.shop_url}/collections.json")
        if not data:
            return [f"{self.shop_url}/products.json"]   # fallback: tous les produits

        urls = []
        for col in data.get("collections", []):
            handle = col.get("handle", "")
            if handle:
                urls.append(f"{self.shop_url}/collections/{handle}/products.json")
        return urls if urls else [f"{self.shop_url}/products.json"]

    def scrape_category(self, category_url: str, max_pages: int = 10) -> list[ProduitExtrait]:
        """Scrape tous les produits d'une collection Shopify (pagination automatique)."""
        produits = []
        page     = 1

        while page <= max_pages:
            data = self.fetch_json(category_url, params={"limit": 250, "page": page})
            if not data:
                break

            items = data.get("products", [])
            if not items:
                break

            for item in items:
                p = self._parse_product(item)
                if p:
                    produits.append(p)

            self.logger.info(f"Page {page} -> {len(items)} produits (total: {len(produits)})")
            if len(items) < 250:
                break
            page += 1

        return produits

    def scrape_product(self, product_url: str) -> Optional[ProduitExtrait]:
        """Scrape un produit Shopify individuel via son URL JSON."""
        # Shopify: ajouter .json à l'URL produit
        json_url = product_url.rstrip("/") + ".json"
        data = self.fetch_json(json_url)
        if not data or "product" not in data:
            return None
        return self._parse_product(data["product"])

    # ── Parsing interne ───────────────────────────────────────────────────────

    def _parse_product(self, item: dict) -> Optional[ProduitExtrait]:
        """Transforme un objet JSON Shopify en ProduitExtrait."""
        try:
            variants  = item.get("variants", [{}])
            first_var = variants[0] if variants else {}

            prix      = float(first_var.get("price", 0) or 0)
            cmp_price = float(first_var.get("compare_at_price") or prix or 0)
            remise    = round((cmp_price - prix) / cmp_price * 100, 1) if cmp_price > prix else 0.0

            # Tags -> liste
            tags_raw  = item.get("tags", "")
            tags      = [t.strip() for t in tags_raw.split(",")] if tags_raw else []

            # Variantes couleur / taille
            opts      = {o["name"].lower(): o.get("values", []) for o in item.get("options", [])}
            couleur   = opts.get("color", opts.get("colour", [""]))[0] if "color" in opts or "colour" in opts else ""
            taille    = opts.get("size", [""])[0] if "size" in opts else ""

            # Stock (aggrégé sur toutes variantes)
            stock     = sum(int(v.get("inventory_quantity", 0) or 0) for v in variants)
            en_stock  = any(v.get("available", False) for v in variants)

            return ProduitExtrait(
                product_id      = str(item.get("id", "")),
                nom             = item.get("title", ""),
                categorie       = item.get("product_type", "Autre"),
                marque_vendeur  = self.shop_name,
                prix            = prix,
                prix_promo      = prix,
                remise_pct      = remise,
                devise          = "USD",
                rating          = 0.0,      # Shopify ne fournit pas les notes nativement
                nb_reviews      = 0,
                en_stock        = en_stock,
                quantite_stock  = max(stock, 0),
                delai_livraison = "",
                description     = self._strip_html(item.get("body_html", "")),
                couleur         = couleur,
                taille          = taille,
                url             = f"{self.shop_url}/products/{item.get('handle', '')}",
                plateforme      = "Shopify",
                pays_shop       = self.pays,
                shop_name       = self.shop_name,
                tags            = tags,
            )
        except Exception as e:
            self.logger.warning(f"Impossible de parser le produit {item.get('id')}: {e}")
            return None

    @staticmethod
    def _strip_html(html: str) -> str:
        """Supprime les balises HTML d'une description."""
        return re.sub(r"<[^>]+>", " ", html).strip() if html else ""


# ── Exemple d'utilisation ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import pandas as pd

    # Store de démo Shopify public
    agent = ShopifyAgent(
        shop_url  = "https://store.ilovecreatives.com",
        shop_name = "ILoveCreatives",
        pays      = "USA"
    )

    produits = agent.run(max_products=100)
    df = pd.DataFrame(agent.to_dict_list())
    print(df.head())
    df.to_csv("shopify_scraped.csv", index=False)
    print(f"Sauvegardé : {len(df)} produits")
