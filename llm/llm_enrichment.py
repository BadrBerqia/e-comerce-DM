"""
Module LLM – Enrichissement et Synthèse par Claude (Anthropic)
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Fonctionnalités :
  1. Synthèse de marché automatique
  2. Recommandations stratégiques
  3. Résumé de descriptions produits
  4. Analyse concurrentielle
  5. Interface conversationnelle (chatbot)

Utilisation :
  from llm.llm_enrichment import LLMAnalyzer
  analyzer = LLMAnalyzer(api_key="sk-ant-...")
  result   = analyzer.analyze_market(df, stats, "Synthèse du marché")
"""

import anthropic
import pandas as pd
import json
from typing import Optional


# ── Prompts système ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Tu es un expert en analyse e-commerce et Data Mining.
Tu analyses des données produits issus de plateformes Shopify et WooCommerce.
Tes réponses sont concises, structurées, orientées décision business.
Utilise des bullet points et des sections claires. Réponds en français."""


PROMPT_TEMPLATES = {
    "Synthèse du marché": """
Voici les données d'analyse e-commerce :
{context}

Génère une synthèse exécutive du marché comprenant :
1. **État général du marché** (3-4 phrases)
2. **Produits phares** (top 3 avec justification)
3. **Segments porteurs** (catégories les plus performantes)
4. **Points d'attention** (anomalies ou risques détectés)
""",

    "Recommandations stratégiques": """
Données e-commerce analysées :
{context}

Propose des recommandations stratégiques actionables :
1. **Optimisation catalogue** : quels produits privilégier/retirer ?
2. **Stratégie de prix** : opportunités de repositionnement
3. **Expansion géographique** : marchés à cibler
4. **Actions immédiates** (priorité haute) et **actions moyen terme**
""",

    "Analyse concurrentielle": """
Données des shops et produits :
{context}

Réalise une analyse concurrentielle :
1. **Leaders du marché** : qui domine et pourquoi ?
2. **Positionnement par catégorie** : avantages compétitifs
3. **Opportunités non exploitées** : niches identifiées
4. **Benchmarks prix/qualité** par segment
""",

    "Tendances émergentes": """
Dataset e-commerce :
{context}

Identifie et analyse les tendances émergentes :
1. **Produits en forte croissance** (rating + avis élevés)
2. **Nouvelles catégories** qui montent
3. **Signaux faibles** à surveiller
4. **Prévisions** pour les 3 prochains mois
""",
}


class LLMAnalyzer:
    """
    Classe principale pour l'enrichissement LLM des analyses e-commerce.
    Utilise l'API Claude d'Anthropic.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model  = model

    # ── Méthode principale ────────────────────────────────────────────────────

    def analyze_market(self, df: pd.DataFrame, stats: dict,
                        analysis_type: str = "Synthèse du marché",
                        custom_question: Optional[str] = None) -> str:
        """
        Génère une analyse de marché basée sur les données Top-K.

        Parameters
        ----------
        df              : DataFrame des top produits
        stats           : Statistiques résumées du marché
        analysis_type   : Type d'analyse (voir PROMPT_TEMPLATES)
        custom_question : Question personnalisée optionnelle

        Returns
        -------
        Texte de l'analyse générée par Claude
        """
        context = self._build_context(df, stats)

        if custom_question:
            user_prompt = f"Données e-commerce :\n{context}\n\nQuestion : {custom_question}\n\nRéponds de manière détaillée et actionable."
        else:
            template = PROMPT_TEMPLATES.get(analysis_type,
                                             PROMPT_TEMPLATES["Synthèse du marché"])
            user_prompt = template.format(context=context)

        return self._call_claude(user_prompt)

    def summarize_product(self, product: dict) -> str:
        """Résume la description d'un produit en 2-3 phrases clés."""
        prompt = f"""Produit : {product.get('nom', 'Inconnu')}
Catégorie : {product.get('categorie', '')}
Prix : {product.get('prix', 0)}€
Note : {product.get('rating', 0)}/5 ({product.get('nb_reviews', 0)} avis)
Description : {product.get('description', 'Non disponible')}

Génère un résumé commercial accrocheur en 2-3 phrases maximum."""
        return self._call_claude(prompt)

    def clean_product_titles(self, titles: list[str]) -> list[str]:
        """Normalise et uniformise une liste de titres produits."""
        prompt = f"""Voici une liste de titres de produits e-commerce à normaliser :
{json.dumps(titles, ensure_ascii=False)}

Règles de normalisation :
- Capitalise la première lettre de chaque mot
- Supprime les caractères spéciaux inutiles
- Uniformise les abréviations (USB-C, LED, HD, etc.)
- Garde les titres concis (max 60 caractères)

Retourne UNIQUEMENT un JSON array des titres normalisés, sans commentaire."""

        result = self._call_claude(prompt)
        try:
            # Extraire le JSON de la réponse
            start = result.find("[")
            end   = result.rfind("]") + 1
            return json.loads(result[start:end])
        except Exception:
            return titles   # fallback si parsing échoue

    def generate_marketing_strategy(self, top_products: pd.DataFrame,
                                     target_market: str = "général") -> str:
        """Génère une stratégie marketing pour les top produits."""
        products_info = top_products.head(10)[
            ["nom", "categorie", "prix", "rating", "nb_reviews"]
        ].to_dict(orient="records")

        prompt = f"""Top 10 produits e-commerce (marché: {target_market}) :
{json.dumps(products_info, ensure_ascii=False, indent=2)}

Génère une stratégie marketing complète incluant :
1. Message clé par segment produit
2. Canaux de distribution recommandés
3. Offres promotionnelles suggérées
4. Contenu de communication (accroches publicitaires)
5. KPIs à suivre"""

        return self._call_claude(prompt)

    def competitive_analysis(self, df: pd.DataFrame) -> str:
        """Analyse concurrentielle automatique entre les shops."""
        shop_stats = df.groupby("marque_vendeur").agg(
            nb_produits=("product_id", "count"),
            rating_moyen=("rating", "mean"),
            prix_moyen=("prix", "mean"),
            score_moyen=("topk_score", "mean") if "topk_score" in df.columns else ("rating", "mean"),
            total_avis=("nb_reviews", "sum"),
        ).round(2).reset_index().to_dict(orient="records")

        prompt = f"""Statistiques par shop e-commerce :
{json.dumps(shop_stats, ensure_ascii=False, indent=2)}

Analyse comparative des shops :
1. Leaders et challengers du marché
2. Forces et faiblesses de chaque acteur
3. Recommandations pour améliorer la compétitivité
4. Opportunités de marché non exploitées"""

        return self._call_claude(prompt)

    # ── Chatbot conversationnel ───────────────────────────────────────────────

    def chat(self, question: str, df: pd.DataFrame,
             history: list = None) -> tuple[str, list]:
        """
        Interface conversationnelle pour interroger les données.

        Parameters
        ----------
        question : Question de l'utilisateur
        df       : DataFrame des produits
        history  : Historique de conversation [{"role": ..., "content": ...}]

        Returns
        -------
        (réponse, nouvel_historique)
        """
        history = history or []
        context = self._build_context(df.head(50), {})

        system = f"{SYSTEM_PROMPT}\n\nContexte des données disponibles :\n{context}"

        messages = history + [{"role": "user", "content": question}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages
        )

        answer = response.content[0].text
        new_history = messages + [{"role": "assistant", "content": answer}]
        return answer, new_history

    # ── Méthodes privées ──────────────────────────────────────────────────────

    def _build_context(self, df: pd.DataFrame, stats: dict) -> str:
        """Construit le contexte textuel à envoyer au LLM."""
        lines = []

        # Statistiques globales
        if stats:
            lines.append("=== STATISTIQUES GLOBALES ===")
            for k, v in stats.items():
                lines.append(f"  {k}: {v}")

        # Top 10 produits
        cols = ["nom", "categorie", "prix", "rating", "nb_reviews",
                "marque_vendeur", "pays_shop"]
        cols = [c for c in cols if c in df.columns]
        lines.append("\n=== TOP PRODUITS ===")
        for _, row in df.head(10).iterrows():
            lines.append(
                f"  • {row.get('nom','')} | {row.get('categorie','')} | "
                f"Prix: {row.get('prix',0):.2f} | Note: {row.get('rating',0):.1f}/5 | "
                f"{row.get('nb_reviews',0)} avis | Shop: {row.get('marque_vendeur','')} ({row.get('pays_shop','')})"
            )

        # Distribution par catégorie
        if "categorie" in df.columns:
            cat_dist = df["categorie"].value_counts().head(7)
            lines.append("\n=== DISTRIBUTION CATÉGORIES ===")
            for cat, count in cat_dist.items():
                lines.append(f"  {cat}: {count} produits")

        return "\n".join(lines)

    def _call_claude(self, user_prompt: str) -> str:
        """Appelle l'API Claude et retourne la réponse textuelle."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text


# ── Script de démonstration ───────────────────────────────────────────────────

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    # Charger et préparer les données
    from analysis.preprocessing import load_data, clean_data, feature_engineering
    from analysis.topk_selection import compute_topk_score

    df  = feature_engineering(clean_data(load_data()))
    df  = compute_topk_score(df)
    top = df.head(20)

    stats = {
        "nb_produits_total": len(df),
        "top_categorie":     df.groupby("categorie")["topk_score"].mean().idxmax(),
        "prix_moyen":        round(df["prix"].mean(), 2),
        "rating_moyen":      round(df["rating"].mean(), 2),
    }

    # Récupérer la clé depuis la variable d'environnement
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[LLM] Définir ANTHROPIC_API_KEY pour tester le module LLM.")
        print("[LLM] Example: set ANTHROPIC_API_KEY=sk-ant-...")
    else:
        analyzer = LLMAnalyzer(api_key=api_key)
        result   = analyzer.analyze_market(top, stats, "Synthèse du marché")
        print("\n" + "="*60)
        print("SYNTHÈSE IA")
        print("="*60)
        print(result)
