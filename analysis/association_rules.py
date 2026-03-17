"""
Règles d'association – Découverte de patterns entre produits
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Algorithme : FP-Growth (via mlxtend)
Métriques  : Support, Confidence, Lift
"""

import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import fpgrowth, association_rules
from mlxtend.preprocessing import TransactionEncoder
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_transaction_matrix(df: pd.DataFrame,
                               group_by: str = "marque_vendeur",
                               item_col: str = "categorie") -> pd.DataFrame:
    """
    Construit la matrice de transactions binaires pour l'algorithme FP-Growth.

    Logique : chaque "transaction" = un shop, les "items" = catégories vendues.
    Cela permet de découvrir quelles catégories sont souvent vendues ensemble.
    """
    # Grouper par shop -> liste de catégories
    transactions = df.groupby(group_by)[item_col].apply(list).tolist()

    te   = TransactionEncoder()
    te_array = te.fit_transform(transactions)
    df_matrix = pd.DataFrame(te_array, columns=te.columns_)

    print(f"[Transactions] {len(transactions)} transactions x {len(te.columns_)} items")
    return df_matrix, te.columns_


def build_product_transactions(df: pd.DataFrame,
                                 n_transactions: int = 1000) -> pd.DataFrame:
    """
    Simule des transactions d'achat basées sur les catégories et sous-catégories.
    Pour les règles de type : {Electronics} -> {Accessories}
    """
    np.random.seed(42)
    transactions = []
    categories   = df["categorie"].unique().tolist()

    for _ in range(n_transactions):
        # Panier simulé : 2-5 produits avec des corrélations réalistes
        n_items = np.random.randint(2, 6)
        basket  = list(np.random.choice(categories, n_items, replace=False))
        transactions.append(basket)

    te       = TransactionEncoder()
    te_array = te.fit_transform(transactions)
    return pd.DataFrame(te_array, columns=te.columns_), te.columns_


def run_fpgrowth(df_matrix: pd.DataFrame,
                  min_support: float = 0.1,
                  min_confidence: float = 0.5,
                  min_lift: float = 1.0) -> pd.DataFrame:
    """
    Exécute FP-Growth et génère les règles d'association.

    Parameters
    ----------
    min_support    : support minimum (ex: 0.1 = présent dans 10% des transactions)
    min_confidence : confiance minimum
    min_lift       : lift minimum (>1 = association positive)
    """
    # Workaround bug mlxtend 0.24 / numpy : utiliser des colonnes entières puis remap
    label_map  = {i: col for i, col in enumerate(df_matrix.columns)}
    df_int     = df_matrix.copy()
    df_int.columns = range(len(df_matrix.columns))

    # Itemsets fréquents
    frequent_items = fpgrowth(df_int, min_support=min_support, use_colnames=True)
    frequent_items.sort_values("support", ascending=False, inplace=True)

    # Remap indices -> labels lisibles
    frequent_items["itemsets"] = frequent_items["itemsets"].apply(
        lambda s: frozenset(label_map[i] for i in s)
    )
    print(f"\n[FP-Growth] {len(frequent_items)} itemsets frequents (support >= {min_support})")
    print(frequent_items.head(10).to_string(index=False))

    if len(frequent_items) == 0:
        print("[Attention] Aucun itemset fréquent trouvé. Réduire min_support.")
        return pd.DataFrame()

    # Règles d'association – implémentation manuelle (contourne bug mlxtend/numpy str)
    support_dict = {row["itemsets"]: row["support"]
                    for _, row in frequent_items.iterrows()}
    rows = []
    for _, row in frequent_items.iterrows():
        itemset = row["itemsets"]
        if len(itemset) < 2:
            continue
        items = list(itemset)
        for i in range(len(items)):
            ant = frozenset(items[:i] + items[i+1:])
            con = frozenset([items[i]])
            sup_ant = support_dict.get(ant, 0)
            if sup_ant == 0:
                continue
            conf = row["support"] / sup_ant
            if conf < min_confidence:
                continue
            sup_con = support_dict.get(con, 0)
            lift = conf / sup_con if sup_con > 0 else 0
            if lift < min_lift:
                continue
            rows.append({
                "antecedents": ", ".join(sorted(ant)),
                "consequents": ", ".join(sorted(con)),
                "support":     round(row["support"], 4),
                "confidence":  round(conf, 4),
                "lift":        round(lift, 4),
            })

    if not rows:
        return pd.DataFrame()
    rules = pd.DataFrame(rows).sort_values("lift", ascending=False)

    print(f"\n[Règles d'association] {len(rules)} règles (conf >= {min_confidence}, lift >= {min_lift})")
    display_cols = ["antecedents", "consequents", "support", "confidence", "lift"]
    print(rules[display_cols].head(20).to_string(index=False))

    return rules


def visualize_rules(rules: pd.DataFrame) -> None:
    """Visualise les règles d'association (scatter support vs confidence, coloré par lift)."""
    if rules.empty:
        return

    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(rules["support"], rules["confidence"],
                          c=rules["lift"], cmap="YlOrRd", s=50, alpha=0.7)
    plt.colorbar(scatter, label="Lift")
    plt.xlabel("Support")
    plt.ylabel("Confidence")
    plt.title("Règles d'Association – Support vs Confidence (couleur = Lift)")

    # Annoter les meilleures règles
    top5 = rules.nlargest(5, "lift")
    for _, row in top5.iterrows():
        label = f"{row['antecedents']} -> {row['consequents']}"
        plt.annotate(label, (row["support"], row["confidence"]),
                     fontsize=7, ha="left", alpha=0.8)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "association_rules.png")
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[Viz] Sauvegardé : {path}")


def top_rules_report(rules: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Retourne les N meilleures règles par lift."""
    if rules.empty:
        return rules
    top = rules.nlargest(n, "lift")
    print(f"\n[Top {n} règles par Lift]")
    print(top[["antecedents", "consequents", "support", "confidence", "lift"]].to_string(index=False))
    return top


def run_association_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Pipeline complet d'analyse par règles d'association."""
    print("\n" + "="*60)
    print("RÈGLES D'ASSOCIATION (FP-Growth)")
    print("="*60)

    # 1. Transactions simulées (catégories dans même panier)
    df_matrix, items = build_product_transactions(df, n_transactions=2000)

    # 2. FP-Growth
    rules = run_fpgrowth(df_matrix, min_support=0.05, min_confidence=0.3, min_lift=0.5)

    if not rules.empty:
        # 3. Visualisation
        visualize_rules(rules)

        # 4. Top règles
        top = top_rules_report(rules, n=10)

        # 5. Export
        rules.to_csv(os.path.join(OUTPUT_DIR, "..", "data", "association_rules.csv"),
                     index=False)
        print("\nRègles exportées.")

    return rules


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from analysis.preprocessing import load_data, clean_data, feature_engineering

    df    = feature_engineering(clean_data(load_data()))
    rules = run_association_analysis(df)
