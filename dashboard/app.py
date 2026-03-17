"""
Dashboard BI – Smart eCommerce Intelligence
Projet: Smart eCommerce Intelligence - FST Tanger LSI2 DM&SID 2025/2026

Lancement :
  cd Projet_DM
  streamlit run dashboard/app.py

Fonctionnalités :
  - Vue globale KPIs
  - Top-K produits interactif
  - Analyse par catégorie et par shop
  - Clustering & anomalies
  - Module LLM intégré (synthèse et recommandations)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Configuration de la page ─────────────────
st.set_page_config(
    page_title="Smart eCommerce BI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS personnalisé ──────────────────────────
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem; border-radius: 10px; color: white;
    text-align: center; margin: 5px;
}
.section-title {
    font-size: 1.4rem; font-weight: 700;
    color: #2c3e50; border-left: 4px solid #667eea;
    padding-left: 10px; margin: 1rem 0 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# Chargement et cache des données
# ══════════════════════════════════════════════

@st.cache_data
def load_and_process():
    """Charge, nettoie et enrichit les données."""
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "products.csv")

    if not os.path.exists(data_path):
        # Génération à la volée si le fichier n'existe pas
        from data.generate_dataset import generate_dataset
        generate_dataset(3000)

    df = pd.read_csv(data_path)

    # Prétraitement rapide
    df["rating"]     = pd.to_numeric(df["rating"], errors="coerce").fillna(0).clip(0, 5)
    df["nb_reviews"] = pd.to_numeric(df["nb_reviews"], errors="coerce").fillna(0).astype(int)
    df["prix"]       = pd.to_numeric(df["prix"], errors="coerce").fillna(0)
    df["en_stock"]   = df["en_stock"].astype(int)
    df["engagement"] = (df["rating"] * np.log1p(df["nb_reviews"])).round(3)

    # Score Top-K
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    df["_r"] = scaler.fit_transform(df[["rating"]])
    df["_n"] = scaler.fit_transform(np.log1p(df[["nb_reviews"]]))
    df["_s"] = df["en_stock"].astype(float)
    df["_p"] = 1 - scaler.fit_transform(df[["prix"]])
    df["_e"] = scaler.fit_transform(df[["engagement"]])
    df["topk_score"] = (0.35*df["_r"] + 0.25*df["_n"] + 0.15*df["_s"] +
                        0.15*df["_p"] + 0.10*df["_e"]).round(4)
    df.drop(columns=[c for c in df.columns if c.startswith("_")], inplace=True)

    return df


# ══════════════════════════════════════════════
# SIDEBAR – Filtres
# ══════════════════════════════════════════════

def sidebar_filters(df: pd.DataFrame):
    st.sidebar.markdown("""
    <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                padding:12px 10px;border-radius:8px;text-align:center;margin-bottom:8px">
        <span style="color:white;font-size:1.1rem;font-weight:700">🛒 Smart eCommerce</span><br>
        <span style="color:#ddd;font-size:0.75rem">BI Intelligence Dashboard</span>
    </div>""", unsafe_allow_html=True)
    st.sidebar.title("🔍 Filtres")

    cats = st.sidebar.multiselect(
        "Catégorie", sorted(df["categorie"].unique()),
        default=sorted(df["categorie"].unique())
    )
    shops = st.sidebar.multiselect(
        "Shop", sorted(df["marque_vendeur"].unique()),
        default=sorted(df["marque_vendeur"].unique())
    )
    pays = st.sidebar.multiselect(
        "Pays", sorted(df["pays_shop"].unique()),
        default=sorted(df["pays_shop"].unique())
    )
    plat = st.sidebar.multiselect(
        "Plateforme", sorted(df["plateforme"].unique()),
        default=sorted(df["plateforme"].unique())
    )
    prix_range = st.sidebar.slider(
        "Prix (€/$)", float(df["prix"].min()), float(df["prix"].max()),
        (float(df["prix"].min()), float(df["prix"].max()))
    )
    en_stock_only = st.sidebar.checkbox("En stock uniquement", value=False)
    top_k         = st.sidebar.slider("Nombre Top-K", 5, 50, 20)

    filtered = df[
        (df["categorie"].isin(cats)) &
        (df["marque_vendeur"].isin(shops)) &
        (df["pays_shop"].isin(pays)) &
        (df["plateforme"].isin(plat)) &
        (df["prix"].between(*prix_range))
    ]
    if en_stock_only:
        filtered = filtered[filtered["en_stock"] == 1]

    return filtered, top_k


# ══════════════════════════════════════════════
# PAGE 1 – Vue Globale / KPIs
# ══════════════════════════════════════════════

def page_overview(df: pd.DataFrame, top_k: int):
    st.markdown("## 📊 Vue Globale – Indicateurs Clés")

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    kpis = [
        ("Total Produits",     f"{len(df):,}",               "🛍️"),
        ("Prix Moyen",         f"${df['prix'].mean():.2f}",   "💰"),
        ("Note Moyenne",       f"{df['rating'].mean():.2f}/5","⭐"),
        ("En Stock",           f"{df['en_stock'].mean()*100:.1f}%", "📦"),
        ("Total Avis",         f"{df['nb_reviews'].sum():,}", "💬"),
    ]
    for col, (label, val, icon) in zip([col1,col2,col3,col4,col5], kpis):
        col.metric(f"{icon} {label}", val)

    st.markdown("---")

    # Distribution par catégorie
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<p class="section-title">Produits par Catégorie</p>', unsafe_allow_html=True)
        cat_counts = df["categorie"].value_counts().reset_index()
        cat_counts.columns = ["Catégorie", "Nb Produits"]
        fig = px.bar(cat_counts, x="Catégorie", y="Nb Produits",
                     color="Nb Produits", color_continuous_scale="Viridis",
                     title="", height=350)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<p class="section-title">Distribution des Prix par Catégorie</p>', unsafe_allow_html=True)
        fig = px.box(df, x="categorie", y="prix", color="categorie",
                     title="", height=350)
        fig.update_layout(showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    # Heatmap rating x catégorie x plateforme
    st.markdown('<p class="section-title">Note Moyenne par Catégorie & Plateforme</p>', unsafe_allow_html=True)
    heatmap_data = df.groupby(["categorie", "plateforme"])["rating"].mean().unstack().round(2)
    fig = px.imshow(heatmap_data, color_continuous_scale="RdYlGn",
                    text_auto=True, aspect="auto", height=300)
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════
# PAGE 2 – Top-K Produits
# ══════════════════════════════════════════════

def page_topk(df: pd.DataFrame, top_k: int):
    st.markdown(f"## 🏆 Top-{top_k} Produits")

    top = df.sort_values("topk_score", ascending=False).head(top_k).copy()
    top["Rang"] = range(1, len(top) + 1)

    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown('<p class="section-title">Classement Global</p>', unsafe_allow_html=True)
        display_cols = ["Rang", "nom", "categorie", "marque_vendeur", "pays_shop",
                        "prix", "rating", "nb_reviews", "topk_score"]
        st.dataframe(
            top[display_cols].rename(columns={
                "nom": "Produit", "categorie": "Catégorie",
                "marque_vendeur": "Shop", "pays_shop": "Pays",
                "prix": "Prix", "rating": "Note", "nb_reviews": "Avis",
                "topk_score": "Score"
            }),
            use_container_width=True, height=400
        )

    with col_b:
        st.markdown('<p class="section-title">Score Top-K</p>', unsafe_allow_html=True)
        fig = px.bar(top.head(15), x="topk_score", y="nom", orientation="h",
                     color="topk_score", color_continuous_scale="Viridis",
                     height=400, labels={"topk_score": "Score", "nom": ""})
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Scatter interactif
    st.markdown('<p class="section-title">Analyse Multidimensionnelle</p>', unsafe_allow_html=True)
    fig = px.scatter(
        top, x="prix", y="rating", size="nb_reviews",
        color="categorie", hover_name="nom",
        hover_data={"topk_score": True, "marque_vendeur": True, "pays_shop": True},
        size_max=40, height=450,
        title=f"Top-{top_k} : Prix vs Note (taille = nb avis)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Top-K par catégorie
    st.markdown('<p class="section-title">Top-3 par Catégorie</p>', unsafe_allow_html=True)
    top_cat = df.sort_values("topk_score", ascending=False).groupby("categorie").head(3)
    fig = px.bar(top_cat, x="topk_score", y="nom", color="categorie",
                 orientation="h", height=500,
                 labels={"topk_score": "Score", "nom": "Produit"})
    fig.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════
# PAGE 3 – Analyse par Shop & Géographie
# ══════════════════════════════════════════════

def page_shops(df: pd.DataFrame):
    st.markdown("## 🌍 Analyse par Shop & Géographie")

    # Top shops par score moyen
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<p class="section-title">Shops – Score Moyen</p>', unsafe_allow_html=True)
        shop_perf = df.groupby("marque_vendeur").agg(
            score_moyen=("topk_score", "mean"),
            nb_produits=("product_id", "count"),
            rating_moyen=("rating", "mean")
        ).round(3).sort_values("score_moyen", ascending=False).reset_index()

        fig = px.bar(shop_perf, x="marque_vendeur", y="score_moyen",
                     color="rating_moyen", color_continuous_scale="RdYlGn",
                     height=350, labels={"marque_vendeur": "Shop", "score_moyen": "Score Moyen"})
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<p class="section-title">Distribution par Pays</p>', unsafe_allow_html=True)
        pays_data = df.groupby("pays_shop").agg(
            nb_produits=("product_id","count"),
            score_moyen=("topk_score","mean")
        ).reset_index()
        fig = px.choropleth(
            pays_data,
            locations="pays_shop", locationmode="ISO-3",
            color="score_moyen",
            hover_name="pays_shop",
            hover_data={"nb_produits": True, "pays_shop": False},
            color_continuous_scale="Viridis",
            title="Score Moyen par Pays", height=350
        )
        fig.update_layout(geo=dict(showframe=False, showcoastlines=True))
        st.plotly_chart(fig, use_container_width=True)

    # Tableau shops
    st.dataframe(shop_perf.rename(columns={
        "marque_vendeur": "Shop", "score_moyen": "Score Moyen",
        "nb_produits": "Nb Produits", "rating_moyen": "Note Moyenne"
    }), use_container_width=True)


# ══════════════════════════════════════════════
# PAGE 4 – Clustering
# ══════════════════════════════════════════════

def page_clustering(df: pd.DataFrame):
    st.markdown("## 🔵 Analyse de Clustering")

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score

    feats = ["prix", "rating", "nb_reviews", "quantite_stock", "delai_livraison_j"]
    feats = [f for f in feats if f in df.columns]
    X_raw = df[feats].fillna(0)
    X     = StandardScaler().fit_transform(X_raw)

    k = st.slider("Nombre de clusters (k)", 2, 8, 3)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    sil = silhouette_score(X, labels)

    df2 = df.copy()
    df2["Cluster"] = labels.astype(str)

    # PCA 2D
    pca  = PCA(n_components=2, random_state=42)
    X2d  = pca.fit_transform(X)
    df2["PC1"], df2["PC2"] = X2d[:,0], X2d[:,1]

    col_a, col_b = st.columns([3, 1])
    with col_a:
        fig = px.scatter(df2, x="PC1", y="PC2", color="Cluster",
                         hover_name="nom", hover_data=["prix","rating","categorie"],
                         title=f"PCA 2D – k={k} clusters (Silhouette = {sil:.3f})",
                         height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.metric("Silhouette Score", f"{sil:.4f}", help="> 0.5 = bon clustering")
        st.metric("Variance expliquée (PC1+PC2)",
                  f"{sum(pca.explained_variance_ratio_)*100:.1f}%")

        st.markdown("**Profil des clusters**")
        profile = df2.groupby("Cluster")[feats].mean().round(2)
        st.dataframe(profile, height=200)


# ══════════════════════════════════════════════
# PAGE 5 – Module LLM (Synthèse IA)
# ══════════════════════════════════════════════

def page_llm(df: pd.DataFrame, top_k: int):
    st.markdown("## 🤖 Synthèse & Recommandations par IA (LLM)")

    top = df.sort_values("topk_score", ascending=False).head(top_k)

    # Résumé statistique à fournir au LLM
    stats_summary = {
        "nb_produits":    len(df),
        "top_categorie":  df.groupby("categorie")["topk_score"].mean().idxmax(),
        "top_shop":       df.groupby("marque_vendeur")["topk_score"].mean().idxmax(),
        "prix_moyen_top": round(top["prix"].mean(), 2),
        "rating_moyen_top": round(top["rating"].mean(), 2),
    }

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown("**Contexte envoyé au LLM**")
        st.json(stats_summary)

        st.markdown("**Top-5 produits**")
        st.dataframe(
            top.head(5)[["nom","categorie","prix","rating","topk_score"]],
            use_container_width=True, hide_index=True
        )

    with col_b:
        prompt_type = st.selectbox("Type d'analyse", [
            "Synthèse du marché",
            "Recommandations stratégiques",
            "Analyse concurrentielle",
            "Tendances émergentes",
        ])

        custom_question = st.text_input(
            "Question personnalisée (optionnel)",
            placeholder="Ex: Quels produits ont le meilleur rapport qualité-prix ?"
        )

        api_key = st.text_input("Clé API Anthropic (Claude)", type="password",
                                 help="Obtenez votre clé sur console.anthropic.com")

        if st.button("🚀 Générer l'analyse IA", type="primary"):
            if not api_key:
                st.warning("Veuillez entrer votre clé API Anthropic.")
            else:
                with st.spinner("Génération en cours..."):
                    try:
                        from llm.llm_enrichment import LLMAnalyzer
                        analyzer = LLMAnalyzer(api_key=api_key)
                        result   = analyzer.analyze_market(
                            df=top, stats=stats_summary,
                            analysis_type=prompt_type,
                            custom_question=custom_question or None
                        )
                        st.success("Analyse générée !")
                        st.markdown("### 📝 Résultat")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Erreur LLM : {e}")


# ══════════════════════════════════════════════
# MAIN – Navigation
# ══════════════════════════════════════════════

def main():
    df = load_and_process()
    df_filtered, top_k = sidebar_filters(df)

    st.sidebar.markdown("---")
    st.sidebar.caption(f"📊 {len(df_filtered):,} produits filtrés / {len(df):,} total")

    st.title("🛒 Smart eCommerce Intelligence Dashboard")
    st.caption("FST Tanger – LSI2 – Module DM & SID – 2025/2026")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Vue Globale",
        f"🏆 Top-{top_k}",
        "🌍 Shops & Géo",
        "🔵 Clustering",
        "🤖 IA / LLM",
    ])

    with tab1: page_overview(df_filtered, top_k)
    with tab2: page_topk(df_filtered, top_k)
    with tab3: page_shops(df_filtered)
    with tab4: page_clustering(df_filtered)
    with tab5: page_llm(df_filtered, top_k)


if __name__ == "__main__":
    main()
