"""
Prétraitement et nettoyage des données produits
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "products.csv")


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    """Charge le dataset produits."""
    df = pd.read_csv(path)
    print(f"[Chargement] {len(df)} lignes, {df.shape[1]} colonnes")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les données : valeurs manquantes, types, doublons."""
    df = df.copy()

    # Suppression des doublons
    before = len(df)
    df.drop_duplicates(subset=["product_id"], keep="first", inplace=True)
    print(f"[Doublons supprimés] {before - len(df)}")

    # Valeurs manquantes numériques -> médiane
    num_cols = ["prix", "prix_promo", "rating", "nb_reviews", "quantite_stock", "delai_livraison_j"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col].fillna(df[col].median(), inplace=True)

    # Valeurs manquantes catégorielles -> "Inconnu"
    cat_cols = ["categorie", "marque_vendeur", "pays_shop", "couleur", "taille", "plateforme"]
    for col in cat_cols:
        if col in df.columns:
            df[col].fillna("Inconnu", inplace=True)

    # Clipping des outliers prix (IQR)
    Q1, Q3 = df["prix"].quantile(0.01), df["prix"].quantile(0.99)
    df["prix"] = df["prix"].clip(Q1, Q3)

    # Rating entre 0 et 5
    df["rating"] = df["rating"].clip(0, 5)

    # nb_reviews >= 0
    df["nb_reviews"] = df["nb_reviews"].clip(lower=0)

    print(f"[Nettoyage terminé] {len(df)} lignes conservées")
    return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Crée de nouvelles variables utiles pour le DM."""
    df = df.copy()

    # Ratio prix promo
    df["ratio_remise"] = np.where(
        df["prix"] > 0,
        (df["prix"] - df["prix_promo"]) / df["prix"],
        0
    ).round(3)

    # Catégorie de prix
    df["segment_prix"] = pd.cut(
        df["prix"],
        bins=[0, 20, 50, 100, 200, float("inf")],
        labels=["Très_bas", "Bas", "Moyen", "Haut", "Premium"]
    )

    # Engagement (note * log(avis+1))
    df["engagement"] = (df["rating"] * np.log1p(df["nb_reviews"])).round(3)

    # Score de stock normalisé
    df["score_stock"] = np.where(df["en_stock"] == 1,
                                  np.log1p(df["quantite_stock"]) / 10, 0).round(3)

    # Encodage catégoriel
    for col in ["categorie", "plateforme", "pays_shop", "segment_prix"]:
        if col in df.columns:
            df[f"{col}_enc"] = LabelEncoder().fit_transform(df[col].astype(str))

    print(f"[Feature Engineering] {df.shape[1]} variables")
    return df


def normalize_features(df: pd.DataFrame,
                        features: list = None) -> tuple[pd.DataFrame, MinMaxScaler]:
    """Normalise les variables numériques entre 0 et 1 (MinMax)."""
    if features is None:
        features = ["prix", "rating", "nb_reviews", "quantite_stock",
                    "delai_livraison_j", "engagement"]

    features = [f for f in features if f in df.columns]
    scaler   = MinMaxScaler()
    df_norm  = df.copy()
    df_norm[features] = scaler.fit_transform(df[features])

    print(f"[Normalisation] {len(features)} variables normalisées")
    return df_norm, scaler


def get_features_for_ml(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Retourne X (features) et y (target) prêts pour les modèles ML."""
    feature_cols = [
        "prix", "rating", "nb_reviews", "quantite_stock",
        "delai_livraison_j", "remise_pct", "engagement",
        "categorie_enc", "plateforme_enc", "pays_shop_enc"
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    X = df[feature_cols].fillna(0)
    y = df["top_produit"] if "top_produit" in df.columns else None
    return X, y


if __name__ == "__main__":
    df = load_data()
    df = clean_data(df)
    df = feature_engineering(df)
    X, y = get_features_for_ml(df)
    print(f"\nX shape: {X.shape}")
    print(f"y distribution:\n{y.value_counts()}")
    print(df[["nom", "prix", "rating", "engagement", "segment_prix"]].head(5))
