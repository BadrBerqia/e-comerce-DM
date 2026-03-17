# Smart eCommerce Intelligence
### ML & DM Pipelines, A2A Agents, and LLMs
**FST Tanger – Filière LSI2 – Module DM & SID – Année 2025/2026**

---

## Structure du projet

```
Projet_DM/
├── data/
│   ├── generate_dataset.py      # Génération du dataset synthétique (3000 produits)
│   └── products.csv             # Dataset généré
├── agents/
│   ├── scraping_agent.py        # Classe de base A2A
│   ├── shopify_agent.py         # Agent Shopify (API JSON native)
│   ├── woocommerce_agent.py     # Agent WooCommerce (REST API v3)
│   └── agent_coordinator.py    # Coordinateur multi-agents
├── analysis/
│   ├── preprocessing.py         # Nettoyage + Feature Engineering
│   ├── topk_selection.py        # Score composite + Top-K
│   ├── clustering.py            # KMeans, DBSCAN, Hiérarchique, PCA
│   ├── classification.py        # Random Forest + XGBoost
│   └── association_rules.py    # FP-Growth + règles d'association
├── pipeline/
│   └── kubeflow_pipeline.py    # Pipeline KFP v2 (4 étapes)
├── dashboard/
│   └── app.py                   # Dashboard Streamlit BI (5 onglets)
├── llm/
│   └── llm_enrichment.py       # Module Claude API (synthèse + chatbot)
├── outputs/                     # Visualisations générées
├── run_analysis.py              # Script principal
└── requirements.txt
```

---

## Installation

```bash
# 1. Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Installer les dépendances
pip install -r requirements.txt
```

---

## Lancement rapide

### 1. Générer les données + lancer toutes les analyses
```bash
python run_analysis.py
```

### 2. Lancer uniquement une étape
```bash
python run_analysis.py --step data          # Dataset
python run_analysis.py --step clustering    # Clustering
python run_analysis.py --step classification
python run_analysis.py --step association
```

### 3. Lancer le dashboard BI
```bash
streamlit run dashboard/app.py
```
→ Ouvre http://localhost:8501 dans votre navigateur

### 4. Compiler le pipeline Kubeflow
```bash
python pipeline/kubeflow_pipeline.py
# Génère : pipeline/pipeline.yaml
```

---

## Modules détaillés

### Étape 1 – Agents A2A (Scraping)
| Fichier | Description |
|---------|-------------|
| `scraping_agent.py` | Classe abstraite de base |
| `shopify_agent.py` | Utilise `/products.json` Shopify |
| `woocommerce_agent.py` | Utilise `/wp-json/wc/v3/products` |
| `agent_coordinator.py` | Orchestre N agents en parallèle |

### Étape 2 – Analyse ML/DM
| Algorithme | Fichier | Métriques |
|-----------|---------|-----------|
| Top-K scoring | `topk_selection.py` | Score pondéré multi-critères |
| KMeans | `clustering.py` | Silhouette Score, Davies-Bouldin |
| DBSCAN | `clustering.py` | Détection anomalies prix |
| Clustering hiérarchique | `clustering.py` | Silhouette Score |
| PCA | `clustering.py` | Variance expliquée |
| Random Forest | `classification.py` | Accuracy, Precision, Recall, F1, AUC |
| XGBoost | `classification.py` | Accuracy, Precision, Recall, F1, AUC |
| FP-Growth | `association_rules.py` | Support, Confidence, Lift |

### Étape 3 – Kubeflow Pipeline
Le pipeline `kubeflow_pipeline.py` définit 4 composants Docker :
1. `generate_data_component` → génération des données
2. `preprocessing_component` → nettoyage + features
3. `topk_selection_component` → scoring Top-K
4. `train_model_component` → XGBoost + métriques

### Étape 4 – Dashboard Streamlit
5 onglets interactifs :
- **Vue Globale** : KPIs, distributions, heatmaps
- **Top-K** : classement filtrable + scatter plot
- **Shops & Géo** : performances par shop + carte choroplèthe
- **Clustering** : KMeans interactif + PCA 2D
- **IA/LLM** : synthèse Claude + questions personnalisées

### Étape 5 – Module LLM (Claude)
```python
from llm.llm_enrichment import LLMAnalyzer

analyzer = LLMAnalyzer(api_key="sk-ant-...")
result   = analyzer.analyze_market(df, stats, "Synthèse du marché")
# → Texte structuré avec insights business
```

---

## Variables d'environnement

```bash
# Clé API Anthropic (Claude)
set ANTHROPIC_API_KEY=sk-ant-votre-cle     # Windows
export ANTHROPIC_API_KEY=sk-ant-votre-cle  # Linux/Mac
```

---

## Évaluation des modèles

### Modèles supervisés (Random Forest, XGBoost)
- Séparation train/test (80/20)
- Validation croisée 5-fold stratifiée
- Métriques : Accuracy, Precision, Recall, F1-Score, AUC-ROC
- Matrice de confusion + courbe ROC générées automatiquement

### Modèles non supervisés (KMeans, DBSCAN)
- Silhouette Score (>0.5 = bon)
- Davies-Bouldin Index (<1.0 = bon)
- Visualisation PCA 2D

### Règles d'association (FP-Growth)
- Support minimum : 0.05
- Confidence minimum : 0.3
- Lift minimum : 1.0 (association positive)

---

## Model Context Protocol (MCP) – Architecture responsable

Le projet intègre les principes MCP d'Anthropic :

| Composant | Rôle |
|-----------|------|
| **MCP Host** | Application Streamlit (environnement principal) |
| **MCP Client** | Module LLM (`llm_enrichment.py`) |
| **MCP Server** | API Claude, API Shopify/WooCommerce |
| **Logs** | Journalisation de toutes les requêtes agents |
| **Permissions** | Validation des accès (lecture seule, pas d'écriture) |

Principes respectés :
- **Responsabilité** : chaque agent déclare ses intentions via `capabilities()`
- **Isolation** : les agents n'accèdent qu'aux données nécessaires
- **Traçabilité** : logs complets des actions de scraping
- **Éthique** : délai entre requêtes, respect du `robots.txt`

---

## Livrables

- [x] Code agents A2A de scraping + documentation
- [x] Pipeline Kubeflow (Python KFP v2)
- [x] Tableau Top-K + Dashboard BI Streamlit
- [x] Module LLM pour enrichissement et synthèse
- [x] Rapport MCP (voir section ci-dessus)
- [ ] Vidéo de démonstration (optionnel)
