"""
Génère rapport.pdf — rapport académique formaté pour le projet Smart eCommerce DM.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.colors import HexColor

# ── Couleurs projet ────────────────────────────────────────────────────────────
PURPLE     = HexColor("#667eea")
DARK_BLUE  = HexColor("#1a1a2e")
ACCENT     = HexColor("#764ba2")
LIGHT_GRAY = HexColor("#f5f5f5")
MED_GRAY   = HexColor("#cccccc")
TEXT_DARK  = HexColor("#2c2c2c")
GREEN_OK   = HexColor("#27ae60")
RED_ERR    = HexColor("#e74c3c")

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "rapport.pdf")
SS_DIR = os.path.join(BASE, "screenshots")

# ── Styles ─────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

cover_title = S("CoverTitle", fontSize=26, textColor=colors.white,
                fontName="Helvetica-Bold", alignment=TA_CENTER, leading=34)
cover_sub   = S("CoverSub",   fontSize=13, textColor=HexColor("#ddd"),
                fontName="Helvetica", alignment=TA_CENTER, leading=20)
cover_meta  = S("CoverMeta",  fontSize=11, textColor=HexColor("#bbb"),
                fontName="Helvetica", alignment=TA_CENTER, leading=18)

h1 = S("H1Custom", fontSize=16, textColor=PURPLE, fontName="Helvetica-Bold",
        spaceBefore=18, spaceAfter=8, leading=20,
        borderPad=4, leftIndent=0)
h2 = S("H2Custom", fontSize=13, textColor=DARK_BLUE, fontName="Helvetica-Bold",
        spaceBefore=12, spaceAfter=6, leading=17)
h3 = S("H3Custom", fontSize=11, textColor=ACCENT, fontName="Helvetica-BoldOblique",
        spaceBefore=8, spaceAfter=4, leading=15)

body = S("BodyCustom", fontSize=10, textColor=TEXT_DARK, fontName="Helvetica",
          leading=15, spaceAfter=6, alignment=TA_JUSTIFY)
bullet = S("BulletCustom", fontSize=10, textColor=TEXT_DARK, fontName="Helvetica",
            leading=14, spaceAfter=3, leftIndent=20, bulletIndent=10)
code_style = S("CodeCustom", fontSize=8.5, textColor=HexColor("#1a1a2e"),
               fontName="Courier", leading=12, spaceAfter=2,
               leftIndent=20, backColor=LIGHT_GRAY)
caption = S("Caption", fontSize=8, textColor=HexColor("#666"),
             fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=8)
footer_style = S("Footer", fontSize=8, textColor=HexColor("#999"),
                  fontName="Helvetica", alignment=TA_CENTER)
toc_h1 = S("TOCH1", fontSize=11, fontName="Helvetica-Bold",
             textColor=DARK_BLUE, leading=16, spaceAfter=2)
toc_h2 = S("TOCH2", fontSize=10, fontName="Helvetica",
             textColor=TEXT_DARK, leading=14, leftIndent=20, spaceAfter=1)

# ── Helpers ────────────────────────────────────────────────────────────────────
def hr(color=PURPLE, thickness=1.5):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=6, spaceBefore=6)

def section_header(num, title):
    return [
        hr(),
        Paragraph(f"{num}. {title.upper()}", h1),
        hr(MED_GRAY, 0.5),
    ]

def sub_header(num, title):
    return Paragraph(f"<b>{num}</b>  {title}", h2)

def body_p(text):
    return Paragraph(text, body)

def bul(text):
    return Paragraph(f"• {text}", bullet)

def table_style_default(col_widths, header_color=PURPLE):
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1,  0), header_color),
        ("TEXTCOLOR",   (0, 0), (-1,  0), colors.white),
        ("FONTNAME",    (0, 0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1,  0), 9),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID",        (0, 0), (-1, -1), 0.4, MED_GRAY),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
    ])

def screenshot(fname, caption_text, width=16*cm):
    path = os.path.join(SS_DIR, fname)
    if not os.path.exists(path):
        return []
    img = Image(path, width=width, height=width*0.58)
    return [img, Paragraph(caption_text, caption), Spacer(1, 6)]

# ── Page numbering ──────────────────────────────────────────────────────────────
class NumberedDoc(SimpleDocTemplate):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
    def handle_pageEnd(self):
        pass  # override so we can add footer in onPage

def add_page_number(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    if page > 2:   # skip cover + TOC
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#999999"))
        w, _ = A4
        canvas.drawCentredString(w / 2, 1.2*cm,
            f"Smart eCommerce Intelligence Pipeline — FST Tanger LSI2 — 2025/2026")
        canvas.drawRightString(w - 2*cm, 1.2*cm, f"Page {page}")
        canvas.setStrokeColor(MED_GRAY)
        canvas.setLineWidth(0.4)
        canvas.line(2*cm, 1.5*cm, w - 2*cm, 1.5*cm)
    canvas.restoreState()

# ══════════════════════════════════════════════════════════════════════════════
# CONTENU DU DOCUMENT
# ══════════════════════════════════════════════════════════════════════════════
def build_story():
    story = []
    W, H = A4

    # ─────────────────── PAGE DE COUVERTURE ───────────────────────────────────
    from reportlab.platypus import Frame
    # Fond violet via un grand tableau plein-page
    cover_bg = Table(
        [[""]],
        colWidths=[W - 4*cm],
        rowHeights=[H - 6*cm],
        style=TableStyle([
            ("BACKGROUND", (0,0), (0,0), DARK_BLUE),
            ("ROUNDEDCORNERS", [8]),
        ])
    )

    cover_data = [
        Spacer(1, 2.5*cm),
        Paragraph("FACULTE DES SCIENCES ET TECHNIQUES DE TANGER", cover_meta),
        Paragraph("Filiere LSI2 — Module Data Mining &amp; SID — 2025/2026", cover_meta),
        Spacer(1, 0.8*cm),
        HRFlowable(width="60%", thickness=1, color=PURPLE, spaceAfter=12, spaceBefore=4),
        Paragraph("RAPPORT ACADEMIQUE", ParagraphStyle("ct2", fontSize=12,
                  textColor=HexColor("#aaa"), fontName="Helvetica",
                  alignment=TA_CENTER, leading=18)),
        Spacer(1, 0.4*cm),
        Paragraph("Smart eCommerce<br/>Intelligence Pipeline", cover_title),
        Spacer(1, 0.3*cm),
        Paragraph("Analyse Multi-Agents A2A / LLM", cover_sub),
        Spacer(1, 0.6*cm),
        HRFlowable(width="60%", thickness=1, color=PURPLE, spaceAfter=12, spaceBefore=4),
        Spacer(1, 1*cm),
        Paragraph("Auteur :  <b>Berqia Badr</b>", cover_meta),
        Paragraph("Depot GitHub :  github.com/BadrBerqia/e-comerce-DM", cover_meta),
        Spacer(1, 0.4*cm),
        Paragraph("Mars 2026", cover_meta),
    ]

    # Fond pleine page via canvas trick → on utilise un tableau coloré
    cov_table = Table(
        [[Paragraph(
            "<font color='white'>&nbsp;</font>",
            ParagraphStyle("_", fontSize=1)
        )]],
        colWidths=[W - 4*cm], rowHeights=[H - 5*cm],
        style=TableStyle([("BACKGROUND", (0,0), (0,0), DARK_BLUE)])
    )

    story += cover_data
    story.append(PageBreak())

    # ─────────────────── TABLE DES MATIERES ───────────────────────────────────
    story.append(Paragraph("TABLE DES MATIERES", h1))
    story.append(hr())
    toc_items = [
        ("1.", "Introduction et Contexte"),
        ("2.", "Objectifs du Projet"),
        ("3.", "Architecture Generale du Systeme"),
        ("4.", "Collecte des Donnees — Scraping Shopify"),
        ("   4.1", "Source des donnees"),
        ("   4.2", "Processus de collecte"),
        ("   4.3", "Caracteristiques du dataset reel"),
        ("5.", "Preprocessing & Feature Engineering"),
        ("   5.1", "Nettoyage"),
        ("   5.2", "Feature Engineering (30 variables)"),
        ("6.", "Analyses Data Mining"),
        ("   6.1", "Selection Top-K (scoring multicritere)"),
        ("   6.2", "Clustering KMeans (segmentation produits)"),
        ("   6.3", "Classification Supervisee (RF + XGBoost)"),
        ("   6.4", "Regles d'Association FP-Growth"),
        ("7.", "Pipeline Multi-Agents (A2A)"),
        ("8.", "Integration LLM / Claude (Anthropic)"),
        ("9.", "Dashboard BI Streamlit"),
        ("10.", "Resultats et Evaluation"),
        ("11.", "Conclusion et Perspectives"),
        ("12.", "Bibliographie"),
    ]
    for num, title in toc_items:
        lvl = toc_h2 if num.startswith("   ") else toc_h1
        story.append(Paragraph(f"{num.strip()}&nbsp;&nbsp;&nbsp;{title}", lvl))
    story.append(PageBreak())

    # ─────────────────── 1. INTRODUCTION ──────────────────────────────────────
    story += section_header("1", "Introduction et Contexte")
    story.append(body_p(
        "L'explosion du commerce electronique mondial a genere des volumes de donnees "
        "produits considerables. Les plateformes comme <b>Shopify</b>, WooCommerce, Amazon "
        "ou Zalando hebergent des millions de references dont l'analyse manuelle est "
        "impossible. Il devient donc strategique d'automatiser la selection, le scoring "
        "et la comprehension de ces catalogues via des techniques avancees de "
        "<b>Data Mining</b> et d'<b>Intelligence Artificielle</b>."
    ))
    story.append(body_p(
        "Ce projet s'inscrit dans le cadre du module <b>DM &amp; SID</b> de la filiere LSI2. "
        "Il propose un pipeline complet, de la collecte automatisee de donnees reelles "
        "jusqu'a leur visualisation interactive, en passant par plusieurs couches "
        "d'analyse machine learning et une integration de grand modele de langage (LLM)."
    ))
    story.append(body_p(
        "Le systeme s'appuie sur une architecture <b>multi-agents (Agent-to-Agent, A2A)</b> "
        "ou chaque composant specialise — collecte, preprocessing, classification, "
        "clustering, regles d'association, LLM — communique via un coordinateur central."
    ))
    story.append(Spacer(1, 8))

    # ─────────────────── 2. OBJECTIFS ─────────────────────────────────────────
    story += section_header("2", "Objectifs du Projet")
    objectives = [
        ("OBJ-1", "Collecter automatiquement des donnees produits reelles depuis des boutiques Shopify publiques via leur API JSON."),
        ("OBJ-2", "Construire un pipeline de preprocessing robuste (nettoyage, feature engineering, normalisation)."),
        ("OBJ-3", "Identifier les produits \"Top\" via un algorithme de scoring multicritere (Top-K Selection)."),
        ("OBJ-4", "Segmenter les produits en clusters homogenes (KMeans, DBSCAN)."),
        ("OBJ-5", "Classifier automatiquement un produit comme top_produit via des algorithmes supervises (RF, XGBoost)."),
        ("OBJ-6", "Extraire des regles d'association entre categories de produits (FP-Growth)."),
        ("OBJ-7", "Integrer un LLM (Claude Anthropic) pour generer des syntheses et recommandations en langage naturel."),
        ("OBJ-8", "Exposer tous les resultats dans un dashboard BI interactif (Streamlit)."),
        ("OBJ-9", "Versionner et deployer le code via GitHub."),
    ]
    tbl = Table(
        [["Code", "Description"]] +
        [[Paragraph(f"<b>{c}</b>", ParagraphStyle("_", fontSize=9,
           fontName="Helvetica-Bold", textColor=PURPLE, alignment=TA_CENTER)),
          Paragraph(d, ParagraphStyle("_", fontSize=9, fontName="Helvetica",
           textColor=TEXT_DARK, alignment=TA_JUSTIFY))]
         for c, d in objectives],
        colWidths=[2.2*cm, 14.3*cm],
        style=table_style_default([2.2*cm, 14.3*cm])
    )
    story.append(tbl)
    story.append(Spacer(1, 8))

    # ─────────────────── 3. ARCHITECTURE ──────────────────────────────────────
    story += section_header("3", "Architecture Generale du Systeme")
    story.append(body_p(
        "Le systeme est organise en <b>6 couches fonctionnelles</b> independantes et "
        "communicantes via le coordinateur d'agents :"
    ))
    arch_rows = [
        ["Couche", "Composant", "Role"],
        ["1 — Collecte",      "agents/ (Shopify, WooCommerce, Scraping)",   "Acquisition des donnees produits depuis les sources en ligne"],
        ["2 — Preprocessing", "analysis/preprocessing.py",                  "Nettoyage, feature engineering, normalisation (30 variables)"],
        ["3 — Analyses DM",   "analysis/ (topk, clustering, classification, rules)", "Top-K, KMeans, RF+XGBoost, FP-Growth"],
        ["4 — LLM",           "llm/llm_enrichment.py",                      "Synthese marche, Q&A, recommandations via Claude Anthropic"],
        ["5 — Dashboard",     "dashboard/app.py (Streamlit + Plotly)",       "BI interactif multi-onglets, filtres dynamiques, carte mondiale"],
        ["6 — Pipeline",      "pipeline/kubeflow_pipeline.py",              "DAG Kubeflow pour orchestration cloud (GCP Vertex AI)"],
    ]
    t = Table(arch_rows,
              colWidths=[3.5*cm, 5.5*cm, 7.5*cm],
              style=table_style_default([3.5*cm, 5.5*cm, 7.5*cm]))
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(sub_header("", "Technologies utilisees"))
    tech = [
        ["Python 3.14", "Langage principal", "pandas / numpy", "Manipulation donnees"],
        ["scikit-learn 1.8", "ML classique (RF, KMeans, PCA)", "XGBoost 3.2", "Gradient boosting"],
        ["mlxtend 0.24", "FP-Growth, regles d'association", "Streamlit", "Dashboard web interactif"],
        ["Plotly Express", "Visualisations interactives", "Requests + BS4", "Scraping HTTP"],
        ["Anthropic SDK", "Integration Claude LLM", "Git / GitHub", "Versioning & collaboration"],
    ]
    t2 = Table(tech, colWidths=[3.5*cm, 5*cm, 3.5*cm, 4.5*cm],
               style=TableStyle([
                   ("BACKGROUND",  (0, 0), (-1, -1), LIGHT_GRAY),
                   ("BACKGROUND",  (0, 0), (0, -1), HexColor("#e8e0f5")),
                   ("BACKGROUND",  (2, 0), (2, -1), HexColor("#e8e0f5")),
                   ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
                   ("FONTNAME",    (2, 0), (2, -1), "Helvetica-Bold"),
                   ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
                   ("GRID",        (0, 0), (-1, -1), 0.4, MED_GRAY),
                   ("TOPPADDING",  (0, 0), (-1, -1), 4),
                   ("BOTTOMPADDING",(0,0), (-1, -1), 4),
                   ("LEFTPADDING", (0, 0), (-1, -1), 6),
               ]))
    story.append(t2)
    story.append(PageBreak())

    # ─────────────────── 4. COLLECTE SHOPIFY ──────────────────────────────────
    story += section_header("4", "Collecte des Donnees — Scraping Shopify")
    story.append(sub_header("4.1", "Source des donnees"))
    story.append(body_p(
        "Les donnees ont ete collectees depuis des boutiques Shopify reelles en exploitant "
        "l'endpoint public non authentifie <b>/products.json</b>. Cet endpoint retourne "
        "jusqu'a 250 produits par page au format JSON structure, incluant : nom, prix, "
        "variants, images, tags, description HTML et stock estimatif."
    ))
    story.append(body_p("<b>Boutiques Shopify scrapees :</b>"))
    shops = [
        ["Boutique", "Domaine", "Pays"],
        ["Allbirds",    "Chaussures eco-responsables", "USA"],
        ["Birdies",     "Chaussures femme",            "USA"],
        ["Brooklinen",  "Linge de maison haut de gamme","USA"],
        ["ColourPop",   "Cosmetiques",                 "USA"],
        ["Cotopaxi",    "Equipement outdoor",          "USA"],
        ["FashionNova", "Mode feminine",               "USA"],
        ["GymShark",    "Vetements sport",             "CAN"],
        ["HarneySons",  "The & infusions premium",     "USA"],
        ["JeffreStar",  "Beaute",                      "USA"],
        ["PuraVida",    "Bijoux",                      "USA"],
        ["TeeTee",      "Vetements",                   "CAN"],
    ]
    t = Table(shops, colWidths=[3.8*cm, 7.5*cm, 2.5*cm],
              style=table_style_default([3.8*cm, 7.5*cm, 2.5*cm]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(sub_header("4.2", "Processus de collecte"))
    steps = [
        "Envoi de requetes GET avec pagination (?page=N&limit=250)",
        "Parse du JSON et extraction des champs pertinents",
        "Normalisation des prix (USD par defaut, CAN --> USD via taux 0.74)",
        "Detection de la categorie a partir des tags et du handle produit",
        "Estimation du stock via le premier variant disponible",
        "Ajout de metadonnees (pays, plateforme, date scraping)",
    ]
    for i, s in enumerate(steps, 1):
        story.append(Paragraph(f"  {i}.  {s}", bullet))
    story.append(Spacer(1, 10))

    story.append(sub_header("4.3", "Caracteristiques du dataset reel collecte"))
    kpis = [
        ["Indicateur", "Valeur"],
        ["Nombre de produits",      "3 681"],
        ["Nombre de boutiques",     "11"],
        ["Categories",              "5 (Fashion, Beauty, Food, Home, Sport)"],
        ["Pays couverts",           "2 (USA, Canada)"],
        ["Plateforme",              "Shopify (100%)"],
        ["Prix moyen",              "$58.35 USD"],
        ["Note moyenne",            "4.14 / 5.0"],
        ["Taux de disponibilite",   "91.2% (en stock)"],
        ["Total avis clients",      "718 927"],
    ]
    t = Table(kpis, colWidths=[6*cm, 10.5*cm],
              style=table_style_default([6*cm, 10.5*cm], header_color=ACCENT))
    story.append(t)

    story.append(Spacer(1, 10))
    story += screenshot("01_vue_globale.png",
                        "Figure 1 — Dashboard Vue Globale : KPIs reels du catalogue Shopify scrappe")
    story.append(PageBreak())

    # ─────────────────── 5. PREPROCESSING ────────────────────────────────────
    story += section_header("5", "Preprocessing & Feature Engineering")
    story.append(sub_header("5.1", "Nettoyage"))
    cleaning = [
        ("Doublons",         "0 detectes apres deduplication agent sur le couple (nom, prix)"),
        ("Valeurs manquantes","rating absent -> mediane categorie ; prix absent -> mediane globale"),
        ("Types",            "prix str -> float ; dates str -> datetime"),
        ("Devises",          "CAD --> USD via taux fixe 0.74"),
        ("Filtrage",         "Suppression produits hors plage : prix < 0 ou > 5 000 USD"),
    ]
    t = Table(cleaning, colWidths=[3.5*cm, 13*cm],
              style=TableStyle([
                  ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
                  ("FONTSIZE",    (0, 0), (-1, -1), 9),
                  ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, LIGHT_GRAY]),
                  ("GRID",        (0, 0), (-1, -1), 0.3, MED_GRAY),
                  ("TOPPADDING",  (0, 0), (-1, -1), 4),
                  ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                  ("LEFTPADDING", (0, 0), (-1, -1), 6),
              ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(sub_header("5.2", "Feature Engineering (30 variables)"))
    story.append(body_p(
        "30 variables ont ete construites a partir des 22 colonnes brutes, "
        "reparties en trois familles :"
    ))
    fe_groups = [
        ["Famille", "Variables construites"],
        ["Temporelles",          "anciennete_jours, en_promo (bool), remise_pct (%)"],
        ["Performance normalisee","rating_norm [0,1], reviews_norm log-scale [0,1], prix_norm [0,1] / categorie, stock_norm [0,1]"],
        ["Derivees",             "score_base (pondere), categorie_enc (LabelEncoder), plateforme_enc (OHE), freshness_score, jours_depuis_promo"],
    ]
    t = Table(fe_groups, colWidths=[4*cm, 12.5*cm],
              style=table_style_default([4*cm, 12.5*cm], header_color=DARK_BLUE))
    story.append(t)
    story.append(PageBreak())

    # ─────────────────── 6. ANALYSES DM ───────────────────────────────────────
    story += section_header("6", "Analyses Data Mining")

    # 6.1 TOP-K
    story.append(sub_header("6.1", "Selection Top-K (analysis/topk_selection.py)"))
    story.append(body_p(
        "Chaque produit recoit un <b>score multicritere</b> pondere combinant "
        "note client, volume d'avis, rapport qualite/prix, disponibilite stock "
        "et fraicheur produit :"
    ))
    formula = [
        ["score  =  w_r x rating_norm  +  w_v x reviews_norm  +  w_p x (1 - prix_norm)"],
        ["           +  w_s x stock_norm  +  w_f x freshness_score  +  bonus_promo"],
    ]
    t = Table(formula, colWidths=[16.5*cm],
              style=TableStyle([
                  ("BACKGROUND", (0,0), (0,-1), HexColor("#f0eeff")),
                  ("FONTNAME",   (0,0), (0,-1), "Courier"),
                  ("FONTSIZE",   (0,0), (0,-1), 9),
                  ("LEFTPADDING",(0,0), (0,-1), 16),
                  ("TOPPADDING", (0,0), (0,-1), 6),
                  ("BOTTOMPADDING",(0,0),(0,-1), 6),
                  ("BOX",        (0,0), (0,-1), 1, PURPLE),
              ]))
    story.append(t)
    story.append(Spacer(1, 6))
    poids = [
        ["Poids", "Critere", "Valeur"],
        ["w_r", "Note client (rating)",     "0.35"],
        ["w_v", "Volume d'avis (reviews)",  "0.30"],
        ["w_p", "Rapport qualite/prix",     "0.15"],
        ["w_s", "Disponibilite stock",      "0.10"],
        ["w_f", "Fraicheur produit",        "0.10"],
        ["bonus_promo", "Remise active",    "+0.05"],
    ]
    t = Table(poids, colWidths=[2.5*cm, 8*cm, 3*cm],
              style=table_style_default([2.5*cm, 8*cm, 3*cm], header_color=ACCENT))
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(body_p("<b>Top-10 produits identifies (donnees Shopify reelles) :</b>"))
    top10 = [
        ["#", "Produit", "Categorie", "Prix $", "Note", "Avis", "Score"],
        ["1",  "Harper Statement Starfish Charm",          "Fashion", "14.00", "5.0", "1 754", "0.9573"],
        ["2",  "Allbirds Laces - Natural Grey Heather",    "Fashion",  "8.00", "5.0", "1 290", "0.9442"],
        ["3",  "Beaded Flower Hoop Earrings",              "Fashion", "14.00", "4.8", "1 902", "0.9249"],
        ["4",  "Men's Strider Explore - Natural Black",    "Fashion", "65.00", "4.8", "2 349", "0.9152"],
        ["5",  "Fluffing Cute",                            "Beauty",  "10.00", "4.9",   "991", "0.9120"],
        ["6",  "Sunset to Starlight Bundle",               "Beauty", "108.00", "4.9", "1 746", "0.9016"],
        ["7",  "Holiday Tea, Tagalong Tin of 5 Sachets",   "Food",     "6.00", "5.0",   "461", "0.8930"],
        ["8",  "Harney & Sons Watermelon Juice",           "Food",    "29.99", "5.0",   "542", "0.8917"],
        ["9",  "High Pile Fleece Crew - Women's",          "Fashion", "77.00", "5.0",   "751", "0.8895"],
        ["10", "Harding Shirt",                            "Fashion", "88.00", "4.7", "2 262", "0.8859"],
    ]
    ts = table_style_default([1*cm, 6.2*cm, 2*cm, 1.6*cm, 1.2*cm, 1.5*cm, 1.7*cm])
    ts.add("TEXTCOLOR", (6, 1), (6, -1), GREEN_OK)
    ts.add("FONTNAME",  (6, 1), (6, -1), "Helvetica-Bold")
    t = Table(top10, colWidths=[1*cm, 6.2*cm, 2*cm, 1.6*cm, 1.2*cm, 1.5*cm, 1.7*cm], style=ts)
    story.append(t)
    story.append(body_p(
        "Observation : la categorie <b>Fashion</b> domine le Top-20 (7/10 produits). "
        "Les produits les mieux notes combinent note >= 4.7 ET volume d'avis >= 400."
    ))
    story += screenshot("02_top20.png",
                        "Figure 2 — Onglet Top-20 : classement interactif + score Top-K")
    story.append(Spacer(1, 6))

    # 6.2 CLUSTERING
    story.append(KeepTogether([
        sub_header("6.2", "Clustering KMeans (analysis/clustering.py)"),
        body_p(
            "Algorithme KMeans avec validation par <b>Silhouette Score</b> et "
            "<b>Davies-Bouldin Index</b>. Reduction dimensionnelle PCA 2D pour "
            "visualisation (variance expliquee : 68.5%)."
        ),
    ]))
    scores = [
        ["Metrique", "Valeur", "Interpretation"],
        ["Silhouette Score (k=3)", "0.3503", "> 0.3 = acceptable pour e-commerce"],
        ["Davies-Bouldin (k=3)",   "1.2652", "< 1.5 = acceptable"],
        ["Variance PCA (PC1+PC2)", "68.5%",  "Bonne representativite 2D"],
    ]
    t = Table(scores, colWidths=[5.5*cm, 3*cm, 8*cm],
              style=table_style_default([5.5*cm, 3*cm, 8*cm], header_color=DARK_BLUE))
    story.append(t)
    story.append(Spacer(1, 6))
    clusters = [
        ["Cluster", "Nom", "Prix moy", "Note", "Remise %", "Top prod %"],
        ["0", "Abordables",  "$33.68",  "4.11", "0.97%",  "39%"],
        ["1", "Premium",     "$179.82", "4.14", "4.05%",  "32%"],
        ["2", "En Promo",    "$45.24",  "4.22", "37.91%", "47%"],
    ]
    ts2 = table_style_default([2*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm, 3.5*cm])
    ts2.add("BACKGROUND", (0, 2), (0, 2), HexColor("#e8f5e9"))
    ts2.add("BACKGROUND", (0, 3), (0, 3), HexColor("#e3f2fd"))
    ts2.add("BACKGROUND", (0, 4), (0, 4), HexColor("#fce4ec"))
    t = Table(clusters, colWidths=[2*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm, 3.5*cm], style=ts2)
    story.append(t)
    story += screenshot("04_clustering.png",
                        "Figure 3 — Clustering PCA 2D (k=3, Silhouette=0.35, Variance=68.5%)")

    # 6.3 CLASSIFICATION
    story.append(sub_header("6.3", "Classification Supervisee (analysis/classification.py)"))
    story.append(body_p(
        "Probleme de <b>classification binaire</b> : top_produit in {0, 1}. "
        "Variable cible construite via le score_attractivite (seuil = 0.55). "
        "Split train/test stratifie : 80% / 20%."
    ))
    clf = [
        ["Modele", "Accuracy", "Precision", "Recall", "F1-Score", "AUC-ROC", "CV-F1"],
        ["Random Forest\n(n=200, depth=12)", "98.24%", "97.96%", "97.63%", "97.79%", "99.82%", "97.48%"],
        ["XGBoost\n(n=200, depth=6)", "98.78%", "98.31%", "98.64%", "98.48%", "99.95%", "97.60%"],
    ]
    ts3 = table_style_default([3.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
    ts3.add("TEXTCOLOR", (5, 1), (5, -1), GREEN_OK)
    ts3.add("TEXTCOLOR", (5, 2), (5,  2), HexColor("#1565C0"))
    ts3.add("FONTNAME",  (5, 1), (5, -1), "Helvetica-Bold")
    t = Table(clf, colWidths=[3.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm], style=ts3)
    story.append(t)
    story.append(body_p(
        "<b>Bilan :</b> XGBoost surpasse Random Forest sur toutes les metriques. "
        "Les deux modeles atteignent une <b>AUC &gt; 99%</b>, indiquant une capacite de "
        "discrimination quasi-parfaite entre produits \"top\" et \"non top\"."
    ))
    story.append(Spacer(1, 6))
    story.append(body_p("<b>Top 5 features importantes (Random Forest, Gini impurity) :</b>"))
    feats = [
        ["Rang", "Feature", "Interpretation"],
        ["1", "score_attractivite", "Score composite construit (feature engineeree)"],
        ["2", "nb_reviews_norm",    "Volume d'avis normalise (log-scale)"],
        ["3", "rating_norm",        "Note client normalisee [0,1]"],
        ["4", "anciennete_jours",   "Fraicheur du produit en jours"],
        ["5", "remise_pct",         "Pourcentage de remise applique"],
    ]
    t = Table(feats, colWidths=[1.5*cm, 4.5*cm, 10.5*cm],
              style=table_style_default([1.5*cm, 4.5*cm, 10.5*cm], header_color=ACCENT))
    story.append(t)
    story.append(PageBreak())

    # 6.4 ASSOCIATION RULES
    story.append(sub_header("6.4", "Regles d'Association FP-Growth (analysis/association_rules.py)"))
    story.append(body_p(
        "Extraction d'associations frequentes entre <b>categories de produits</b> "
        "co-achetees dans des paniers simules (2 000 transactions). "
        "Algorithme <b>FP-Growth</b> plus efficace qu'Apriori sur grands datasets."
    ))
    params = [
        ["Parametre", "Valeur", "Signification"],
        ["Support minimum",    "0.05", "Present dans >= 5% des paniers"],
        ["Confiance minimum",  "0.30", "P(B|A) >= 30%"],
        ["Lift minimum",       "1.0",  "Association positive uniquement (lift > 1)"],
        ["Itemsets frequents", "67",   "Combinaisons de categories frequentes"],
        ["Regles extraites",   "163",  "Regles respectant support + confiance + lift"],
    ]
    t = Table(params, colWidths=[4*cm, 2.5*cm, 10*cm],
              style=table_style_default([4*cm, 2.5*cm, 10*cm], header_color=DARK_BLUE))
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(body_p("<b>Top 5 regles par lift :</b>"))
    rules = [
        ["Antecedents", "Consequent", "Support", "Confiance", "Lift"],
        ["Beauty + Fashion + Home + Sport", "Food",    "0.250", "84.5%", "1.207"],
        ["Fashion + Food + Home + Sport",   "Beauty",  "0.250", "83.5%", "1.202"],
        ["Beauty + Food + Home + Sport",    "Fashion", "0.250", "83.2%", "1.178"],
        ["Beauty + Fashion + Food + Home",  "Sport",   "0.250", "82.9%", "1.173"],
        ["Beauty + Fashion + Home",         "Food",    "0.302", "81.4%", "1.163"],
    ]
    ts4 = table_style_default([7*cm, 2.5*cm, 2*cm, 2.5*cm, 2*cm])
    ts4.add("TEXTCOLOR", (4, 1), (4, -1), GREEN_OK)
    ts4.add("FONTNAME",  (4, 1), (4, -1), "Helvetica-Bold")
    t = Table(rules, colWidths=[7*cm, 2.5*cm, 2*cm, 2.5*cm, 2*cm], style=ts4)
    story.append(t)
    story.append(body_p(
        "Interpretation : les paniers contenant 4 categories sur 5 ont une forte "
        "probabilite (lift &gt; 1.2) d'inclure la 5e categorie, revelant une "
        "<b>complementarite transversale</b> dans les comportements d'achat."
    ))
    story.append(PageBreak())

    # ─────────────────── 7. PIPELINE A2A ──────────────────────────────────────
    story += section_header("7", "Pipeline Multi-Agents (A2A)")
    story.append(body_p(
        "L'architecture <b>Agent-to-Agent (A2A)</b> decompose le traitement en agents "
        "autonomes communicant via un coordinateur central. Chaque agent est "
        "independant, peut echouer sans bloquer les autres, et peut etre "
        "parallelise (threading / asyncio)."
    ))
    agents = [
        ["Agent", "Technologie", "Responsabilite"],
        ["AgentCoordinator",   "Python asyncio",      "Orchestration, fusion des donnees, deduplication"],
        ["ShopifyAgent",       "Requests + JSON",     "Scraping API /products.json avec pagination"],
        ["WooCommerceAgent",   "REST API (OAuth)",    "Collecte via API authentifiee consumer_key/secret"],
        ["ScrapingAgent",      "BeautifulSoup4",      "Fallback HTML DOM si l'API retourne 403/429"],
    ]
    t = Table(agents, colWidths=[3.8*cm, 4*cm, 8.7*cm],
              style=table_style_default([3.8*cm, 4*cm, 8.7*cm], header_color=PURPLE))
    story.append(t)
    story.append(Spacer(1, 8))
    avantages = [
        "Separation des responsabilites (principe SRP)",
        "Extensibilite : ajout d'un nouvel agent sans modifier le reste",
        "Resilience : un agent peut echouer sans bloquer le pipeline",
        "Parallelisation native (threading / asyncio)",
        "Testabilite unitaire de chaque agent de maniere isolee",
    ]
    for a in avantages:
        story.append(bul(a))
    story.append(Spacer(1, 8))

    # ─────────────────── 8. LLM ───────────────────────────────────────────────
    story += section_header("8", "Integration LLM / Claude (Anthropic)")
    story.append(body_p(
        "Module <b>llm/llm_enrichment.py</b> — API : <b>Claude 3.5 Sonnet</b> (Anthropic). "
        "Temperature fixee a 0.3 pour privilegier la precision sur la creativite. "
        "800 tokens maximum par appel."
    ))
    llm_feats = [
        ["Fonctionnalite", "Description"],
        ["Synthese du marche",    "Analyse globale du catalogue et tendances par categorie"],
        ["Scoring LLM",           "Note semantique d'un produit via son titre et ses tags"],
        ["Q&A produit",           "Reponse a toute question en langage naturel"],
        ["Recommandations",       "Suggestions de produits similaires ou complementaires"],
    ]
    t = Table(llm_feats, colWidths=[4.5*cm, 12*cm],
              style=table_style_default([4.5*cm, 12*cm], header_color=ACCENT))
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(body_p(
        "<b>Prompt engineering :</b> le LLM recoit en contexte les KPIs du dataset "
        "filtre (nb_produits, top_categorie, prix_moyen_top, rating_moyen_top) "
        "ainsi que le Top-5 des produits courants."
    ))
    story += screenshot("05_ia_llm.png",
                        "Figure 4 — Onglet IA/LLM : integration Claude Anthropic dans le dashboard")
    story.append(PageBreak())

    # ─────────────────── 9. DASHBOARD ─────────────────────────────────────────
    story += section_header("9", "Dashboard BI Streamlit")
    story.append(body_p(
        "Fichier : <b>dashboard/app.py</b> — Acces : http://localhost:8501 "
        "Le dashboard est structure en <b>5 onglets interactifs</b> avec "
        "filtres dynamiques applicables a toutes les vues."
    ))
    tabs = [
        ["Onglet", "Contenu"],
        ["1 - Vue Globale",   "KPIs temps reel, bar chart categories, boxplot prix, heatmap note x plateforme"],
        ["2 - Top-20",        "Tableau classement interactif, bar chart score Top-K, scatter prix vs note"],
        ["3 - Shops & Geo",   "Score moyen par boutique, carte choropleth mondiale (Plotly), tableau recapitulatif"],
        ["4 - Clustering",    "Slider k interactif, scatter PCA 2D, Silhouette temps reel, profil clusters"],
        ["5 - IA / LLM",      "Contexte JSON au LLM, Top-5 produits, selecteur analyse, Q&A libre, reponse Claude"],
    ]
    t = Table(tabs, colWidths=[3.5*cm, 13*cm],
              style=table_style_default([3.5*cm, 13*cm], header_color=DARK_BLUE))
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(body_p("<b>Filtres sidebar dynamiques :</b> Categorie, Shop, Pays, Plateforme, "
                        "Prix min/max (slider), En stock uniquement (toggle)."))
    story += screenshot("03_shops_geo.png",
                        "Figure 5 — Onglet Shops & Geo : carte choropleth + scores par boutique")
    story.append(PageBreak())

    # ─────────────────── 10. RESULTATS ────────────────────────────────────────
    story += section_header("10", "Resultats et Evaluation")

    story.append(sub_header("10.1", "Qualite des donnees collectees"))
    kpi_res = [
        ["Metrique", "Valeur"],
        ["Produits reels collectes",        "3 681"],
        ["Boutiques Shopify couvertes",     "11"],
        ["Taux de remplissage champs cles", "> 95%"],
        ["Doublons detectes",               "0 (deduplication agent)"],
        ["Produits en stock",               "91.2%"],
    ]
    t = Table(kpi_res, colWidths=[7*cm, 9.5*cm],
              style=table_style_default([7*cm, 9.5*cm], header_color=PURPLE))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(sub_header("10.2", "Performance des modeles ML"))
    perf = [
        ["Modele",          "Accuracy", "F1-Score", "AUC-ROC", "CV-F1 (5-fold)"],
        ["Random Forest",   "98.24%",   "97.79%",   "99.82%",  "97.48%"],
        ["XGBoost",         "98.78%",   "98.48%",   "99.95%",  "97.60%"],
    ]
    ts5 = table_style_default([4*cm, 3*cm, 3*cm, 3*cm, 3.5*cm])
    ts5.add("TEXTCOLOR", (3, 1), (3, -1), GREEN_OK)
    ts5.add("FONTNAME",  (3, 1), (3, -1), "Helvetica-Bold")
    t = Table(perf, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3.5*cm], style=ts5)
    story.append(t)
    story.append(body_p(
        "Les deux modeles montrent des performances excellentes et stables (faible "
        "ecart train/CV), sans signe de sur-apprentissage. "
        "<b>XGBoost est retenu comme modele de production.</b>"
    ))
    story.append(Spacer(1, 6))

    story.append(sub_header("10.3", "Clustering"))
    story.append(body_p(
        "Silhouette Score de <b>0.35</b> avec k=3 : segmentation correcte pour des "
        "donnees e-commerce naturellement heterogenes. Les 3 segments (Abordables, "
        "Premium, Promo) sont interpretables et actionnables."
    ))

    story.append(sub_header("10.4", "Regles d'association"))
    story.append(body_p(
        "<b>163 regles</b> extraites, les meilleures atteignant un lift de <b>1.21</b>. "
        "Ces regles confirment la complementarite entre les 5 grandes categories."
    ))

    story.append(sub_header("10.5", "Dashboard"))
    story.append(body_p(
        "Zero erreur console (verifie via Chrome DevTools). "
        "Tous les assets charges en HTTP 200. "
        "Temps de chargement initial : ~4 secondes (rendu Streamlit + calculs ML)."
    ))
    story.append(PageBreak())

    # ─────────────────── 11. CONCLUSION ───────────────────────────────────────
    story += section_header("11", "Conclusion et Perspectives")
    story.append(body_p(
        "Ce projet a permis de mettre en oeuvre un pipeline complet de Data Mining "
        "applique au e-commerce, couvrant toutes les etapes depuis la collecte automatisee "
        "de donnees reelles jusqu'a leur exploitation via un dashboard BI interactif."
    ))
    story.append(body_p("<b>Principaux enseignements :</b>"))
    lessons = [
        "L'API publique Shopify /products.json permet une collecte legale et robuste sans authentification.",
        "Les algorithmes RF et XGBoost atteignent une AUC > 99% sur ce type de donnees produits.",
        "L'architecture multi-agents offre modularite et extensibilite essentielles pour les SID.",
        "L'integration LLM apporte une couche d'interpretabilite inaccessible aux methodes ML classiques.",
    ]
    for l in lessons:
        story.append(bul(l))
    story.append(Spacer(1, 8))
    story.append(body_p("<b>Perspectives d'amelioration :</b>"))
    persp = [
        "Collecte multi-plateformes : Amazon SP-API, WooCommerce REST authentifiee",
        "Deploiement cloud : containerisation Docker, orchestration Kubeflow / GCP Vertex AI",
        "Mise a jour temps reel : pipeline streaming (Kafka + Spark Streaming)",
        "Systeme de recommandation collaboratif (Collaborative Filtering)",
        "NLP avance : analyse de sentiment sur les avis clients (BERT, CamemBERT)",
        "Explicabilite ML : SHAP values pour interpretation fine des predictions XGBoost",
    ]
    for p in persp:
        story.append(bul(p))
    story.append(PageBreak())

    # ─────────────────── 12. BIBLIOGRAPHIE ────────────────────────────────────
    story += section_header("12", "Bibliographie")
    refs = [
        ("[1]",  "Tan, P.N., Steinbach, M., Kumar, V. (2018). Introduction to Data Mining, 2nd Ed. Pearson."),
        ("[2]",  "Han, J., Pei, J., Kamber, M. (2011). Data Mining: Concepts and Techniques, 3rd Ed. Morgan Kaufmann."),
        ("[3]",  "Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32."),
        ("[4]",  "Chen, T., Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. KDD 2016."),
        ("[5]",  "Agrawal, R., Srikant, R. (1994). Fast Algorithms for Mining Association Rules. VLDB, pp. 487-499."),
        ("[6]",  "Han, J., Pei, J., Yin, Y. (2000). Mining Frequent Patterns without Candidate Generation. SIGMOD."),
        ("[7]",  "Rousseeuw, P.J. (1987). Silhouettes: A graphical aid to cluster analysis. J. Comput. Appl. Math., 20."),
        ("[8]",  "Anthropic (2024). Claude API Documentation. https://docs.anthropic.com/"),
        ("[9]",  "Shopify (2024). Products JSON API. https://shopify.dev/docs/api/storefront"),
        ("[10]", "McKinney, W. (2010). Data Structures for Statistical Computing in Python. Proc. SciPy, pp. 56-61."),
        ("[11]", "Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. JMLR, 12, pp. 2825-2830."),
        ("[12]", "Raschka et al. (2020). MLxtend. Journal of Open Source Software, 5(46), 1799."),
    ]
    for num, ref in refs:
        story.append(Paragraph(
            f"<b>{num}</b>&nbsp;&nbsp;{ref}",
            ParagraphStyle("_ref", fontSize=9, fontName="Helvetica",
                           textColor=TEXT_DARK, leading=14, spaceAfter=5,
                           leftIndent=24, firstLineIndent=-24)
        ))

    story.append(Spacer(1, 20))
    story.append(hr(PURPLE, 2))
    story.append(Paragraph(
        "Faculte des Sciences et Techniques de Tanger — Filiere LSI2 — 2025/2026",
        ParagraphStyle("_end", fontSize=10, fontName="Helvetica-Oblique",
                       textColor=HexColor("#666"), alignment=TA_CENTER, spaceAfter=4)
    ))
    story.append(Paragraph(
        "github.com/BadrBerqia/e-comerce-DM",
        ParagraphStyle("_end2", fontSize=9, fontName="Helvetica",
                       textColor=PURPLE, alignment=TA_CENTER)
    ))

    return story


# ── GENERATION DU PDF ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    doc = SimpleDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2.2*cm,
        title="Rapport Academique — Smart eCommerce Intelligence Pipeline",
        author="Berqia Badr",
        subject="Data Mining & Systemes d'Information Distribues — LSI2 FST Tanger",
        creator="ReportLab + Python",
    )

    story = build_story()
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"[OK] rapport.pdf genere -> {OUT}")
    import os
    size_kb = os.path.getsize(OUT) // 1024
    print(f"     Taille : {size_kb} Ko")
