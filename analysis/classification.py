"""
Classification supervisée – Prédiction des Top Produits
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Modèles implémentés :
  1. Random Forest
  2. XGBoost
Évaluation : train/test split + validation croisée + métriques complètes
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, confusion_matrix, classification_report,
                              roc_auc_score, roc_curve)
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import os, warnings
warnings.filterwarnings("ignore")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FEATURE_COLS = ["prix", "rating", "nb_reviews", "quantite_stock",
                "delai_livraison_j", "remise_pct", "en_stock",
                "categorie_enc", "plateforme_enc", "pays_shop_enc"]


def prepare_features(df: pd.DataFrame) -> tuple:
    """Prépare X et y pour la classification."""
    # Encodage si pas déjà fait
    df = df.copy()
    for col in ["categorie", "plateforme", "pays_shop"]:
        enc_col = f"{col}_enc"
        if enc_col not in df.columns and col in df.columns:
            df[enc_col] = LabelEncoder().fit_transform(df[col].astype(str))

    feats = [f for f in FEATURE_COLS if f in df.columns]
    X = df[feats].fillna(0)
    y = df["top_produit"]
    return X, y, feats


def evaluate_model(model, X_test, y_test, model_name: str) -> dict:
    """Calcule et affiche toutes les métriques d'évaluation."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    auc  = roc_auc_score(y_test, y_prob) if y_prob is not None else None

    print(f"\n{'='*50}")
    print(f"Modèle : {model_name}")
    print(f"{'='*50}")
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1-Score  : {f1:.4f}")
    if auc:
        print(f"  AUC-ROC   : {auc:.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Non-Top','Top'])}")

    # Matrice de confusion
    _plot_confusion_matrix(confusion_matrix(y_test, y_pred), model_name)

    # Courbe ROC
    if y_prob is not None:
        _plot_roc(y_test, y_prob, auc, model_name)

    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, "auc": auc}


def _plot_confusion_matrix(cm: np.ndarray, model_name: str) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")
    plt.colorbar(im, ax=ax)
    ax.set(xticks=[0,1], yticks=[0,1],
           xticklabels=["Non-Top","Top"], yticklabels=["Non-Top","Top"],
           xlabel="Prédit", ylabel="Réel",
           title=f"Matrice de Confusion – {model_name}")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max()/2 else "black", fontsize=14)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, f"confusion_{model_name.replace(' ','_')}.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"  -> Matrice sauvegardée : {path}")


def _plot_roc(y_test, y_prob, auc, model_name: str) -> None:
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, lw=2, label=f"AUC = {auc:.4f}")
    plt.plot([0,1], [0,1], "k--", lw=1)
    plt.xlabel("Taux Faux Positifs")
    plt.ylabel("Taux Vrais Positifs")
    plt.title(f"Courbe ROC – {model_name}")
    plt.legend()
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, f"roc_{model_name.replace(' ','_')}.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"  -> ROC sauvegardée : {path}")


# ─────────────────────────────────────────────
# 1. Random Forest
# ─────────────────────────────────────────────

def train_random_forest(df: pd.DataFrame,
                         test_size: float = 0.2,
                         n_estimators: int = 200) -> tuple:
    """Entraîne et évalue un RandomForestClassifier."""
    X, y, feats = prepare_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    rf = RandomForestClassifier(n_estimators=n_estimators, random_state=42,
                                 class_weight="balanced", n_jobs=-1)
    rf.fit(X_train, y_train)

    metrics = evaluate_model(rf, X_test, y_test, "Random Forest")

    # Validation croisée
    cv    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_f1 = cross_val_score(rf, X, y, cv=cv, scoring="f1")
    print(f"  CV F1-Score (5-fold) : {cv_f1.mean():.4f} +- {cv_f1.std():.4f}")
    metrics["cv_f1_mean"] = cv_f1.mean()

    # Importance des variables
    _plot_feature_importance(rf.feature_importances_, feats, "Random Forest")

    return rf, metrics


# ─────────────────────────────────────────────
# 2. XGBoost
# ─────────────────────────────────────────────

def train_xgboost(df: pd.DataFrame,
                   test_size: float = 0.2) -> tuple:
    """Entraîne et évalue un XGBoostClassifier."""
    X, y, feats = prepare_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    scale_pos = (y == 0).sum() / (y == 1).sum()   # gestion déséquilibre classes
    xgb_clf = xgb.XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        scale_pos_weight=scale_pos, random_state=42,
        eval_metric="logloss", verbosity=0, use_label_encoder=False
    )
    xgb_clf.fit(X_train, y_train,
                eval_set=[(X_test, y_test)],
                verbose=False)

    metrics = evaluate_model(xgb_clf, X_test, y_test, "XGBoost")

    # Validation croisée
    cv    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_f1 = cross_val_score(xgb_clf, X, y, cv=cv, scoring="f1")
    print(f"  CV F1-Score (5-fold) : {cv_f1.mean():.4f} +- {cv_f1.std():.4f}")
    metrics["cv_f1_mean"] = cv_f1.mean()

    _plot_feature_importance(xgb_clf.feature_importances_, feats, "XGBoost")

    return xgb_clf, metrics


def _plot_feature_importance(importances, feature_names, model_name: str) -> None:
    idx    = np.argsort(importances)[::-1]
    sorted_names  = [feature_names[i] for i in idx]
    sorted_values = importances[idx]

    plt.figure(figsize=(8, 5))
    plt.barh(sorted_names[::-1], sorted_values[::-1], color="steelblue")
    plt.xlabel("Importance")
    plt.title(f"Importance des Variables – {model_name}")
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, f"feature_importance_{model_name.replace(' ','_')}.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"  -> Feature importance sauvegardée : {path}")


# ─────────────────────────────────────────────
# Pipeline complet de classification
# ─────────────────────────────────────────────

def run_full_classification(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 60)
    print("CLASSIFICATION SUPERVISÉE")
    print("=" * 60)
    print(f"Distribution de la cible : {dict(df['top_produit'].value_counts())}")

    rf_model,  rf_metrics  = train_random_forest(df)
    xgb_model, xgb_metrics = train_xgboost(df)

    # Comparaison
    comp = pd.DataFrame([
        {"Modèle": "Random Forest", **rf_metrics},
        {"Modèle": "XGBoost",       **xgb_metrics},
    ])
    print(f"\n[Comparaison des modèles]\n{comp.to_string(index=False)}")
    return {"random_forest": rf_model, "xgboost": xgb_model,
            "metrics": comp}


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from analysis.preprocessing import load_data, clean_data, feature_engineering

    df  = feature_engineering(clean_data(load_data()))
    res = run_full_classification(df)
