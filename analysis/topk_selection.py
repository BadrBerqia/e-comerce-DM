"""
Sélection Top-K produits – Scoring multi-critères pondéré
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Approche :
  - Score composite normalisé pondéré sur plusieurs critères
  - Poids configurables par l'utilisateur
  - Classement global + classement par catégorie + classement par shop
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


# Poids par défaut (somme = 1)
DEFAULT_WEIGHTS = {
    "rating":          0.35,
    "nb_reviews":      0.25,
    "en_stock":        0.15,
    "prix_inverse":    0.15,   # prix bas = meilleur score
    "engagement":      0.10,
}


def compute_topk_score(df: pd.DataFrame,
                        weights: dict = None) -> pd.DataFrame:
    """
    Calcule un score d'attractivité composite pour chaque produit.

    Parameters
    ----------
    df      : DataFrame avec les colonnes requises
    weights : Poids des critères (dict). Si None, utilise DEFAULT_WEIGHTS.

    Returns
    -------
    DataFrame avec la colonne 'topk_score' ajoutée et triée.
    """
    weights = weights or DEFAULT_WEIGHTS
    df      = df.copy()
    scaler  = MinMaxScaler()

    # Normalisation 0-1 des composantes
    df["_rating_n"]    = scaler.fit_transform(df[["rating"]])
    df["_reviews_n"]   = scaler.fit_transform(np.log1p(df[["nb_reviews"]]))
    df["_stock_n"]     = df["en_stock"].astype(float)
    df["_prix_inv_n"]  = 1 - scaler.fit_transform(df[["prix"]])   # inversé

    if "engagement" not in df.columns:
        df["engagement"] = df["rating"] * np.log1p(df["nb_reviews"])
    df["_engage_n"] = scaler.fit_transform(df[["engagement"]])

    # Score pondéré
    df["topk_score"] = (
        weights.get("rating",       0) * df["_rating_n"]    +
        weights.get("nb_reviews",   0) * df["_reviews_n"]   +
        weights.get("en_stock",     0) * df["_stock_n"]      +
        weights.get("prix_inverse", 0) * df["_prix_inv_n"]  +
        weights.get("engagement",   0) * df["_engage_n"]
    ).round(4)

    # Nettoyage colonnes temporaires
    tmp_cols = [c for c in df.columns if c.startswith("_")]
    df.drop(columns=tmp_cols, inplace=True)

    return df.sort_values("topk_score", ascending=False)


def select_top_k(df: pd.DataFrame, k: int = 20,
                 weights: dict = None) -> pd.DataFrame:
    """Retourne les K meilleurs produits globaux."""
    scored = compute_topk_score(df, weights)
    top    = scored.head(k).copy()
    top["rank"] = range(1, len(top) + 1)
    print(f"\n[Top-{k} Global]")
    print(top[["rank", "nom", "categorie", "prix", "rating", "nb_reviews",
               "topk_score"]].to_string(index=False))
    return top


def select_top_k_by_category(df: pd.DataFrame, k: int = 5,
                              weights: dict = None) -> pd.DataFrame:
    """Retourne les K meilleurs produits par catégorie."""
    scored   = compute_topk_score(df, weights)
    results  = []

    for cat in sorted(scored["categorie"].unique()):
        subset = scored[scored["categorie"] == cat].head(k).copy()
        subset["rank_in_category"] = range(1, len(subset) + 1)
        results.append(subset)

    top_cat = pd.concat(results, ignore_index=True)
    print(f"\n[Top-{k} par Catégorie] {len(df['categorie'].unique())} catégories")
    return top_cat


def select_top_k_by_shop(df: pd.DataFrame, k: int = 3,
                          weights: dict = None) -> pd.DataFrame:
    """Retourne le produit phare (top-K) de chaque shop."""
    scored  = compute_topk_score(df, weights)
    results = []

    for shop in sorted(scored["marque_vendeur"].unique()):
        subset = scored[scored["marque_vendeur"] == shop].head(k).copy()
        subset["rank_in_shop"] = range(1, len(subset) + 1)
        results.append(subset)

    return pd.concat(results, ignore_index=True)


def topk_report(df: pd.DataFrame, k: int = 10) -> dict:
    """Génère un rapport complet Top-K (global + catégorie + shop)."""
    global_top  = select_top_k(df, k)
    cat_top     = select_top_k_by_category(df, k=5)
    shop_top    = select_top_k_by_shop(df, k=1)

    # Statistiques descriptives
    stats = {
        "nb_produits_total":    len(df),
        "nb_categories":        df["categorie"].nunique(),
        "nb_shops":             df["marque_vendeur"].nunique(),
        "prix_moyen":           round(df["prix"].mean(), 2),
        "rating_moyen":         round(df["rating"].mean(), 2),
        "pct_en_stock":         round(df["en_stock"].mean() * 100, 1),
        "top_k_score_min":      round(global_top["topk_score"].min(), 4),
        "top_k_score_moyen":    round(global_top["topk_score"].mean(), 4),
    }
    print(f"\n[Rapport Stats]\n{pd.Series(stats).to_string()}")
    return {"global": global_top, "by_category": cat_top, "by_shop": shop_top, "stats": stats}


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from analysis.preprocessing import load_data, clean_data, feature_engineering

    df = feature_engineering(clean_data(load_data()))
    report = topk_report(df, k=10)

    # Export
    report["global"].to_csv("data/top10_global.csv", index=False)
    report["by_category"].to_csv("data/top5_by_category.csv", index=False)
    print("\nFichiers exportés.")
