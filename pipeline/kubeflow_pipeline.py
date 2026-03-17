"""
Pipeline Kubeflow (KFP v2) – Orchestration ML E-commerce
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Ce fichier définit un pipeline ML reproductible avec Kubeflow Pipelines SDK v2.
Chaque étape est un composant Docker indépendant.

Prérequis :
  pip install kfp==2.7.0
  kubectl + minikube ou cluster Kubernetes actif

Lancement :
  python kubeflow_pipeline.py           # compile le pipeline en YAML
  python kubeflow_pipeline.py --run     # compile + soumet au cluster
"""

import kfp
from kfp import dsl
from kfp.dsl import Dataset, Model, Metrics, Input, Output, component
import argparse
import os

# ─────────────────────────────────────────────
# Image Docker de base (à remplacer par votre registre)
# ─────────────────────────────────────────────
BASE_IMAGE = "python:3.11-slim"


# ═══════════════════════════════════════════════
# COMPOSANT 1 – Génération / Chargement des données
# ═══════════════════════════════════════════════

@component(base_image=BASE_IMAGE,
           packages_to_install=["pandas", "numpy"])
def generate_data_component(n_products: int,
                              output_dataset: Output[Dataset]) -> None:
    """Génère le dataset synthétique e-commerce."""
    import pandas as pd
    import numpy as np
    import random, json

    random.seed(42); np.random.seed(42)

    CATEGORIES = {
        "Electronics": ["Wireless Earbuds","Bluetooth Speaker","Smart Watch","USB-C Hub"],
        "Sport":       ["Fitness Tracker","Yoga Mat","Running Shoes","Jump Rope"],
        "Home":        ["LED Desk Lamp","Air Purifier","Coffee Maker","Smart Plug"],
        "Fashion":     ["T-shirt","Sneakers","Sunglasses","Backpack"],
        "Beauty":      ["Face Moisturizer","Serum Vitamin C","Lip Balm","Mascara"],
    }
    SHOPS = ["TechStore","FitShop","BrightHome","FashionHub","BeautyGlow"]
    PAYS  = ["USA","UK","FR","DE","CA","MA"]

    records = []
    for i in range(1, n_products + 1):
        cat   = random.choice(list(CATEGORIES.keys()))
        prod  = random.choice(CATEGORIES[cat])
        prix  = round(random.uniform(10, 300), 2)
        rating= round(max(1.0, min(5.0, random.gauss(4.1, 0.6))), 1)
        nb_rev= min(int(np.random.exponential(400)) + 5, 8000)
        stock = random.randint(0, 200)
        score = (rating/5)*0.4 + min(nb_rev/2000,1)*0.35 + (1 if stock>0 else 0)*0.15
        records.append({
            "product_id": i, "nom": prod, "categorie": cat,
            "marque_vendeur": random.choice(SHOPS), "pays_shop": random.choice(PAYS),
            "prix": prix, "prix_promo": round(prix*0.9,2), "remise_pct": 10,
            "rating": rating, "nb_reviews": nb_rev, "en_stock": int(stock>0),
            "quantite_stock": stock, "delai_livraison_j": random.choice([1,2,3,5,7]),
            "plateforme": random.choice(["Shopify","WooCommerce"]),
            "top_produit": int(score >= 0.55), "score_attractivite": round(score,4),
        })

    df = pd.DataFrame(records)
    df.to_csv(output_dataset.path, index=False)
    print(f"[generate_data] {len(df)} produits générés -> {output_dataset.path}")


# ═══════════════════════════════════════════════
# COMPOSANT 2 – Prétraitement
# ═══════════════════════════════════════════════

@component(base_image=BASE_IMAGE,
           packages_to_install=["pandas", "numpy", "scikit-learn"])
def preprocessing_component(input_dataset: Input[Dataset],
                              output_dataset: Output[Dataset]) -> None:
    """Nettoyage, feature engineering et normalisation."""
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import LabelEncoder

    df = pd.read_csv(input_dataset.path)

    # Nettoyage
    df.drop_duplicates(subset=["product_id"], inplace=True)
    num_cols = ["prix", "rating", "nb_reviews", "quantite_stock", "delai_livraison_j"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median() if col in df else 0)

    # Feature engineering
    df["engagement"]   = (df["rating"] * np.log1p(df["nb_reviews"])).round(3)
    df["ratio_remise"] = ((df["prix"] - df["prix_promo"]) / df["prix"].replace(0,1)).round(3)

    # Encodage
    for col in ["categorie", "plateforme", "pays_shop"]:
        if col in df.columns:
            df[f"{col}_enc"] = LabelEncoder().fit_transform(df[col].astype(str))

    df.to_csv(output_dataset.path, index=False)
    print(f"[preprocessing] {len(df)} lignes, {df.shape[1]} colonnes -> {output_dataset.path}")


# ═══════════════════════════════════════════════
# COMPOSANT 3 – Sélection Top-K
# ═══════════════════════════════════════════════

@component(base_image=BASE_IMAGE,
           packages_to_install=["pandas", "numpy", "scikit-learn"])
def topk_selection_component(input_dataset: Input[Dataset],
                               k: int,
                               output_topk: Output[Dataset],
                               output_metrics: Output[Metrics]) -> None:
    """Calcule le score d'attractivité et sélectionne les Top-K produits."""
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import MinMaxScaler

    df     = pd.read_csv(input_dataset.path)
    scaler = MinMaxScaler()

    df["_r"] = scaler.fit_transform(df[["rating"]])
    df["_n"] = scaler.fit_transform(np.log1p(df[["nb_reviews"]]))
    df["_s"] = df["en_stock"].astype(float)
    df["_p"] = 1 - scaler.fit_transform(df[["prix"]])
    df["_e"] = scaler.fit_transform(df[["engagement"]])

    df["topk_score"] = (0.35*df["_r"] + 0.25*df["_n"] + 0.15*df["_s"] +
                        0.15*df["_p"] + 0.10*df["_e"]).round(4)
    df.drop(columns=[c for c in df.columns if c.startswith("_")], inplace=True)
    df.sort_values("topk_score", ascending=False, inplace=True)

    top = df.head(k).copy()
    top.to_csv(output_topk.path, index=False)

    output_metrics.log_metric("nb_products_analyzed", len(df))
    output_metrics.log_metric("top_k", k)
    output_metrics.log_metric("avg_topk_score", round(top["topk_score"].mean(), 4))
    output_metrics.log_metric("avg_rating_topk", round(top["rating"].mean(), 4))
    print(f"[topk] Top-{k} produits sélectionnés -> {output_topk.path}")


# ═══════════════════════════════════════════════
# COMPOSANT 4 – Entraînement du modèle (XGBoost)
# ═══════════════════════════════════════════════

@component(base_image=BASE_IMAGE,
           packages_to_install=["pandas", "numpy", "scikit-learn", "xgboost"])
def train_model_component(input_dataset: Input[Dataset],
                           output_model: Output[Model],
                           output_metrics: Output[Metrics]) -> None:
    """Entraîne un XGBoostClassifier pour prédire les top produits."""
    import pandas as pd
    import numpy as np
    import pickle
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import f1_score, accuracy_score, roc_auc_score
    from sklearn.preprocessing import LabelEncoder
    import xgboost as xgb

    df = pd.read_csv(input_dataset.path)

    feats = ["prix", "rating", "nb_reviews", "quantite_stock",
             "delai_livraison_j", "remise_pct", "en_stock",
             "categorie_enc", "plateforme_enc", "pays_shop_enc", "engagement"]
    feats = [f for f in feats if f in df.columns]

    X = df[feats].fillna(0)
    y = df["top_produit"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                          random_state=42, stratify=y)
    model = xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05,
                                random_state=42, eval_metric="logloss", verbosity=0,
                                use_label_encoder=False)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    f1  = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    output_metrics.log_metric("accuracy",  round(acc, 4))
    output_metrics.log_metric("f1_score",  round(f1,  4))
    output_metrics.log_metric("auc_roc",   round(auc, 4))

    with open(output_model.path, "wb") as f:
        pickle.dump(model, f)

    print(f"[train_model] Accuracy={acc:.4f} | F1={f1:.4f} | AUC={auc:.4f}")


# ═══════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════

@dsl.pipeline(
    name="smart-ecommerce-pipeline",
    description="Pipeline ML complet : données -> prétraitement -> Top-K -> classification"
)
def smart_ecommerce_pipeline(n_products: int = 3000, top_k: int = 20):
    """
    Pipeline Kubeflow complet pour Smart eCommerce Intelligence.

    Étapes :
      1. generate_data     -> génération du dataset
      2. preprocessing     -> nettoyage + feature engineering
      3. topk_selection    -> scoring et sélection Top-K
      4. train_model       -> entraînement XGBoost
    """
    # Étape 1 : Génération
    step1 = generate_data_component(n_products=n_products)
    step1.set_display_name("1 - Génération Dataset")

    # Étape 2 : Prétraitement
    step2 = preprocessing_component(input_dataset=step1.outputs["output_dataset"])
    step2.set_display_name("2 - Prétraitement")
    step2.after(step1)

    # Étape 3 : Top-K
    step3 = topk_selection_component(
        input_dataset=step2.outputs["output_dataset"], k=top_k
    )
    step3.set_display_name("3 - Sélection Top-K")
    step3.after(step2)

    # Étape 4 : Classification
    step4 = train_model_component(input_dataset=step2.outputs["output_dataset"])
    step4.set_display_name("4 - Entraînement XGBoost")
    step4.after(step2)


# ═══════════════════════════════════════════════
# Compilation et (optionnel) soumission
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile/Run le pipeline Kubeflow")
    parser.add_argument("--run",    action="store_true", help="Soumettre au cluster KFP")
    parser.add_argument("--host",   default="http://localhost:8080", help="URL KFP")
    parser.add_argument("--output", default="pipeline/pipeline.yaml", help="Fichier YAML")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Compilation YAML
    kfp.compiler.Compiler().compile(smart_ecommerce_pipeline, args.output)
    print(f"[KFP] Pipeline compilé -> {args.output}")

    if args.run:
        client = kfp.Client(host=args.host)
        run = client.create_run_from_pipeline_func(
            smart_ecommerce_pipeline,
            arguments={"n_products": 3000, "top_k": 20},
            run_name="Smart eCommerce Run",
            experiment_name="ecommerce-experiments"
        )
        print(f"[KFP] Pipeline soumis : run_id={run.run_id}")
