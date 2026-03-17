"""
Génération du dataset synthétique e-commerce
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026
Description: Génère ~3000 produits réalistes issus de plateformes Shopify/WooCommerce
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────
# Données de référence
# ─────────────────────────────────────────────

CATEGORIES = {
    "Electronics": ["Wireless Earbuds", "Bluetooth Speaker", "Smart Watch", "Laptop Stand",
                    "USB-C Hub", "Mechanical Keyboard", "Gaming Mouse", "Webcam HD",
                    "LED Monitor", "Portable Charger"],
    "Sport": ["Fitness Tracker", "Yoga Mat", "Resistance Bands", "Water Bottle",
              "Running Shoes", "Sports Headphones", "Jump Rope", "Foam Roller",
              "Gym Gloves", "Cycling Helmet"],
    "Home": ["LED Desk Lamp", "Air Purifier", "Coffee Maker", "Smart Plug",
             "Throw Pillow", "Wall Clock", "Scented Candle", "Storage Organizer",
             "Picture Frame", "Bed Sheets"],
    "Fashion": ["T-shirt", "Sneakers", "Sunglasses", "Watch", "Backpack",
                "Cap", "Hoodie", "Jeans", "Leather Belt", "Wallet"],
    "Beauty": ["Face Moisturizer", "Serum Vitamin C", "Lip Balm", "Mascara",
               "Hair Oil", "Face Wash", "Sunscreen SPF50", "Eye Cream",
               "Body Lotion", "Nail Polish"],
    "Books": ["Python Programming", "Machine Learning Guide", "Business Strategy",
              "Self-Development", "Data Science Handbook", "Marketing Essentials",
              "Digital Photography", "Cooking Mastery", "Travel Guide", "Finance 101"],
    "Toys": ["Lego Set", "RC Car", "Board Game", "Puzzle 1000pcs",
             "Action Figure", "Building Blocks", "Drone Mini", "Educational Kit",
             "Plush Toy", "Card Game"]
}

SHOPS = [
    {"name": "TechStore",     "pays": "USA",    "anciennete": 8},
    {"name": "FitShop",       "pays": "GBR",    "anciennete": 5},
    {"name": "BrightHome",    "pays": "CAN",    "anciennete": 6},
    {"name": "FashionHub",    "pays": "FRA",    "anciennete": 4},
    {"name": "BeautyGlow",    "pays": "DEU",    "anciennete": 3},
    {"name": "BookWorld",     "pays": "AUS",    "anciennete": 10},
    {"name": "ToyLand",       "pays": "JPN",    "anciennete": 7},
    {"name": "GadgetZone",    "pays": "ARE",    "anciennete": 2},
    {"name": "SportsPro",     "pays": "ESP",    "anciennete": 5},
    {"name": "HomeDecor",     "pays": "ITA",    "anciennete": 6},
    {"name": "MarocTech",     "pays": "MAR",    "anciennete": 3},
    {"name": "EliteStyle",    "pays": "FRA",    "anciennete": 4},
]

COULEURS   = ["Noir", "Blanc", "Bleu", "Rouge", "Vert", "Gris", "Rose", "Orange"]
TAILLES    = ["XS", "S", "M", "L", "XL", "XXL", "Unique"]
PLATEFORMES = ["Shopify", "WooCommerce"]


def prix_par_categorie(cat):
    """Génère un prix réaliste selon la catégorie."""
    ranges = {
        "Electronics": (15,  350),
        "Sport":        (10,  180),
        "Home":         (8,   200),
        "Fashion":      (12,  250),
        "Beauty":       (6,   120),
        "Books":        (5,   60),
        "Toys":         (8,   150),
    }
    lo, hi = ranges[cat]
    return round(random.uniform(lo, hi), 2)


def generate_dataset(n=3000):
    records = []
    base_date = datetime(2024, 1, 1)

    for i in range(1, n + 1):
        cat  = random.choice(list(CATEGORIES.keys()))
        prod = random.choice(CATEGORIES[cat])
        shop = random.choice(SHOPS)
        plat = random.choice(PLATEFORMES)

        prix        = prix_par_categorie(cat)
        remise_pct  = random.choice([0, 0, 0, 5, 10, 15, 20, 25, 30])
        prix_promo  = round(prix * (1 - remise_pct / 100), 2) if remise_pct > 0 else prix

        # Popularité corrélée au prix et à la catégorie
        base_rating = round(random.gauss(4.1, 0.6), 1)
        rating      = max(1.0, min(5.0, base_rating))
        nb_reviews  = int(np.random.exponential(400)) + 5
        nb_reviews  = min(nb_reviews, 8000)

        stock       = random.randint(0, 200)
        en_stock    = stock > 0

        livraison   = random.choice([1, 2, 3, 5, 7, 10, 14])

        date_mise_en_ligne = base_date + timedelta(days=random.randint(0, 365))
        date_promotion     = None
        if remise_pct > 0:
            date_promotion = date_mise_en_ligne + timedelta(days=random.randint(10, 100))

        couleur  = random.choice(COULEURS)
        taille   = random.choice(TAILLES)

        # Score de succès (variable cible) :
        # combinaison pondérée rating, avis, stock, prix normalisé
        score = (rating / 5) * 0.4 + min(nb_reviews / 2000, 1) * 0.35 + \
                (1 if en_stock else 0) * 0.15 + (1 - min(prix / 350, 1)) * 0.1
        top_produit = 1 if score >= 0.55 else 0

        records.append({
            "product_id":          i,
            "nom":                 prod,
            "categorie":           cat,
            "marque_vendeur":      shop["name"],
            "pays_shop":           shop["pays"],
            "anciennete_shop":     shop["anciennete"],
            "plateforme":          plat,
            "prix":                prix,
            "prix_promo":          prix_promo,
            "remise_pct":          remise_pct,
            "devise":              "USD" if shop["pays"] in ["USA","CAN","AUS"] else
                                   "EUR" if shop["pays"] in ["FRA","DEU","ESP","ITA"] else
                                   "GBP" if shop["pays"] == "GBR" else
                                   "MAD" if shop["pays"] == "MAR" else "AED",
            "rating":              rating,
            "nb_reviews":          nb_reviews,
            "en_stock":            int(en_stock),
            "quantite_stock":      stock,
            "delai_livraison_j":   livraison,
            "couleur":             couleur,
            "taille":              taille,
            "date_mise_en_ligne":  date_mise_en_ligne.strftime("%Y-%m-%d"),
            "date_promotion":      date_promotion.strftime("%Y-%m-%d") if date_promotion else None,
            "top_produit":         top_produit,
            "score_attractivite":  round(score, 4),
        })

    df = pd.DataFrame(records)
    out_path = os.path.join(os.path.dirname(__file__), "products.csv")
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[OK] Dataset genere : {len(df)} produits -> {out_path}")
    print(df.head(3).to_string())
    return df


if __name__ == "__main__":
    generate_dataset(3000)
