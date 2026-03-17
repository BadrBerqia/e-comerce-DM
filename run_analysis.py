"""
Script principal – Lance le pipeline d'analyse complet
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Usage :
  python run_analysis.py              # Pipeline complet
  python run_analysis.py --step data  # Étape spécifique
  python run_analysis.py --help
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def step_data():
    print("\n" + "="*60)
    print("ÉTAPE 1 : GÉNÉRATION DU DATASET")
    print("="*60)
    from data.generate_dataset import generate_dataset
    df = generate_dataset(3000)
    return df

def step_preprocessing(df=None):
    print("\n" + "="*60)
    print("ÉTAPE 2 : PRÉTRAITEMENT")
    print("="*60)
    from analysis.preprocessing import load_data, clean_data, feature_engineering
    if df is None:
        df = load_data()
    df = clean_data(df)
    df = feature_engineering(df)
    return df

def step_topk(df):
    print("\n" + "="*60)
    print("ÉTAPE 3 : SÉLECTION TOP-K")
    print("="*60)
    from analysis.topk_selection import topk_report
    report = topk_report(df, k=10)
    return report

def step_clustering(df):
    print("\n" + "="*60)
    print("ÉTAPE 4 : CLUSTERING")
    print("="*60)
    from analysis.clustering import run_full_clustering
    df = run_full_clustering(df)
    return df

def step_classification(df):
    print("\n" + "="*60)
    print("ÉTAPE 5 : CLASSIFICATION")
    print("="*60)
    from analysis.classification import run_full_classification
    return run_full_classification(df)

def step_association(df):
    print("\n" + "="*60)
    print("ÉTAPE 6 : RÈGLES D'ASSOCIATION")
    print("="*60)
    from analysis.association_rules import run_association_analysis
    return run_association_analysis(df)


def main():
    parser = argparse.ArgumentParser(description="Pipeline Smart eCommerce Intelligence")
    parser.add_argument("--step", choices=["data","preprocess","topk","clustering",
                                            "classification","association","all"],
                        default="all", help="Étape à exécuter")
    args = parser.parse_args()

    os.makedirs("outputs", exist_ok=True)

    if args.step in ("data", "all"):
        df = step_data()
    else:
        df = None

    if args.step in ("preprocess", "all"):
        df = step_preprocessing(df)

    if df is None:
        from analysis.preprocessing import load_data, clean_data, feature_engineering
        df = feature_engineering(clean_data(load_data()))

    if args.step in ("topk", "all"):
        step_topk(df)

    if args.step in ("clustering", "all"):
        df = step_clustering(df)

    if args.step in ("classification", "all"):
        step_classification(df)

    if args.step in ("association", "all"):
        step_association(df)

    print("\n" + "="*60)
    print("PIPELINE TERMINÉ")
    print("="*60)
    print(f"  Dataset final   : data/products.csv")
    print(f"  Visualisations  : outputs/")
    print(f"  Dashboard       : streamlit run dashboard/app.py")
    print("="*60)


if __name__ == "__main__":
    main()
