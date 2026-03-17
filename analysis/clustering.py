"""
Clustering des produits e-commerce
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Algorithmes implémentés :
  1. KMeans               -> segmentation (premium / discount / populaires)
  2. Clustering hiérarchique (Agglomerative)
  3. DBSCAN               -> détection d'anomalies/outliers
  4. PCA + visualisation  -> projection 2D
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")   # mode non-interactif (serveur)

from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


CLUSTER_FEATURES = ["prix", "rating", "nb_reviews", "quantite_stock",
                     "delai_livraison_j", "remise_pct"]


def prepare_matrix(df: pd.DataFrame, features: list = None) -> np.ndarray:
    """Prépare et standardise la matrice de features pour le clustering."""
    feats = [f for f in (features or CLUSTER_FEATURES) if f in df.columns]
    X = df[feats].fillna(0).values
    X = StandardScaler().fit_transform(X)
    return X


# ─────────────────────────────────────────────
# 1. KMeans
# ─────────────────────────────────────────────

def kmeans_clustering(df: pd.DataFrame, k: int = 3,
                      features: list = None) -> pd.DataFrame:
    """
    Segmente les produits en K clusters avec KMeans.
    Labels typiques (k=3) : 0=discount, 1=populaire, 2=premium
    """
    X   = prepare_matrix(df, features)
    km  = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)

    df = df.copy()
    df["cluster_kmeans"] = labels

    # Évaluation
    sil = silhouette_score(X, labels)
    db  = davies_bouldin_score(X, labels)
    print(f"\n[KMeans k={k}]")
    print(f"  Silhouette Score : {sil:.4f}  (>0.5 = bon)")
    print(f"  Davies-Bouldin   : {db:.4f}   (<1.0 = bon)")

    # Interprétation des clusters
    feats = [f for f in (features or CLUSTER_FEATURES) if f in df.columns]
    summary = df.groupby("cluster_kmeans")[feats + ["top_produit"] if "top_produit" in df.columns else feats].mean().round(2)
    print(f"\n[Profil des clusters]\n{summary}")

    # Nommage automatique des clusters selon le prix moyen
    prix_par_cluster = df.groupby("cluster_kmeans")["prix"].mean()
    sorted_clusters  = prix_par_cluster.sort_values()
    noms = {sorted_clusters.index[0]: "Discount",
            sorted_clusters.index[1]: "Populaire",
            sorted_clusters.index[2]: "Premium"} if k == 3 else {}
    df["cluster_label"] = df["cluster_kmeans"].map(noms).fillna(df["cluster_kmeans"].astype(str))

    return df, km, sil


def elbow_method(df: pd.DataFrame, k_max: int = 10,
                 features: list = None) -> None:
    """Trace la courbe d'inertie pour choisir k optimal."""
    X        = prepare_matrix(df, features)
    inertias = []
    sils     = []
    ks       = range(2, k_max + 1)

    for k in ks:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        inertias.append(km.inertia_)
        sils.append(silhouette_score(X, km.labels_))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(ks, inertias, "bo-")
    axes[0].set(xlabel="k", ylabel="Inertie", title="Méthode Elbow")
    axes[1].plot(ks, sils, "rs-")
    axes[1].set(xlabel="k", ylabel="Silhouette", title="Silhouette Score")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "elbow_method.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[Elbow] Sauvegardé : {path}")


# ─────────────────────────────────────────────
# 2. Clustering hiérarchique
# ─────────────────────────────────────────────

def hierarchical_clustering(df: pd.DataFrame, k: int = 3,
                             features: list = None) -> pd.DataFrame:
    """Clustering agglomératif hiérarchique."""
    X      = prepare_matrix(df, features)
    # Sous-échantillon pour performance (dendrogramme lourd sur 3000 lignes)
    sample = min(500, len(df))
    X_s    = X[:sample]

    agg    = AgglomerativeClustering(n_clusters=k, linkage="ward")
    labels = agg.fit_predict(X_s)

    sil = silhouette_score(X_s, labels)
    print(f"\n[Hiérarchique k={k}] Silhouette : {sil:.4f}")

    df = df.copy()
    df["cluster_hierarch"] = -1
    df.iloc[:sample, df.columns.get_loc("cluster_hierarch")] = labels
    return df


# ─────────────────────────────────────────────
# 3. DBSCAN – Détection d'anomalies
# ─────────────────────────────────────────────

def dbscan_anomalies(df: pd.DataFrame, eps: float = 0.5,
                     min_samples: int = 10,
                     features: list = None) -> pd.DataFrame:
    """
    Détecte les produits atypiques (label = -1 dans DBSCAN).
    Anomalies possibles : prix anormal, rating très faible avec beaucoup d'avis, etc.
    """
    X      = prepare_matrix(df, features)
    db     = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X)

    df = df.copy()
    df["dbscan_label"]   = labels
    df["is_anomalie"]    = (labels == -1).astype(int)

    n_clusters  = len(set(labels)) - (1 if -1 in labels else 0)
    n_anomalies = (labels == -1).sum()
    print(f"\n[DBSCAN eps={eps}, min_samples={min_samples}]")
    print(f"  Clusters trouvés : {n_clusters}")
    print(f"  Anomalies        : {n_anomalies} ({n_anomalies/len(df)*100:.1f}%)")

    anomalies = df[df["is_anomalie"] == 1][["nom", "categorie", "prix", "rating", "nb_reviews"]]
    print(f"\n[Exemples d'anomalies]\n{anomalies.head(10).to_string(index=False)}")
    return df


# ─────────────────────────────────────────────
# 4. PCA + Visualisation 2D
# ─────────────────────────────────────────────

def pca_visualization(df: pd.DataFrame, features: list = None,
                       color_col: str = "cluster_kmeans") -> None:
    """Projette les produits en 2D via PCA et génère un scatter plot coloré."""
    X    = prepare_matrix(df, features)
    pca  = PCA(n_components=2, random_state=42)
    X2d  = pca.fit_transform(X)

    explained = pca.explained_variance_ratio_ * 100
    print(f"\n[PCA] Variance expliquée : PC1={explained[0]:.1f}% | PC2={explained[1]:.1f}%")

    df = df.copy()
    df["PC1"], df["PC2"] = X2d[:, 0], X2d[:, 1]

    plt.figure(figsize=(10, 7))
    if color_col in df.columns:
        for label in sorted(df[color_col].unique()):
            mask = df[color_col] == label
            plt.scatter(df.loc[mask, "PC1"], df.loc[mask, "PC2"],
                        label=str(label), alpha=0.6, s=15)
        plt.legend(title=color_col, bbox_to_anchor=(1.05, 1))
    else:
        plt.scatter(df["PC1"], df["PC2"], alpha=0.4, s=15)

    plt.title(f"Visualisation PCA 2D des produits ({color_col})\n"
              f"Variance expliquée : {sum(explained):.1f}%")
    plt.xlabel(f"PC1 ({explained[0]:.1f}%)")
    plt.ylabel(f"PC2 ({explained[1]:.1f}%)")
    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, f"pca_{color_col}.png")
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[PCA] Sauvegardé : {path}")
    return df


# ─────────────────────────────────────────────
# Pipeline complet de clustering
# ─────────────────────────────────────────────

def run_full_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """Lance tous les algorithmes de clustering et retourne le df enrichi."""
    print("=" * 60)
    print("CLUSTERING COMPLET")
    print("=" * 60)

    elbow_method(df, k_max=8)

    df, km, sil_km = kmeans_clustering(df, k=3)
    df = hierarchical_clustering(df, k=3)
    df = dbscan_anomalies(df, eps=1.0, min_samples=15)
    df = pca_visualization(df, color_col="cluster_label")

    return df


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from analysis.preprocessing import load_data, clean_data, feature_engineering

    df = feature_engineering(clean_data(load_data()))
    df = run_full_clustering(df)
    df.to_csv(os.path.join(os.path.dirname(__file__), "..", "data", "products_clustered.csv"),
              index=False)
    print("\nDataset enrichi sauvegardé.")
