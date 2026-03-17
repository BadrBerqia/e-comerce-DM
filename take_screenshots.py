"""
Capture automatique des screenshots du dashboard Streamlit.
Sauvegarde chaque onglet dans le dossier screenshots/.
"""
import asyncio, os, time
from playwright.async_api import async_playwright

BASE_URL  = "http://localhost:8501"
OUT_DIR   = os.path.join(os.path.dirname(__file__), "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

TABS = [
    ("01_vue_globale",   "📊 Vue Globale"),
    ("02_top20",         "🏆 Top-20"),
    ("03_shops_geo",     "🌍 Shops & Géo"),
    ("04_clustering",    "🔵 Clustering"),
    ("05_ia_llm",        "🤖 IA / LLM"),
]

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx     = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            device_scale_factor=1.5,
        )
        page = await ctx.new_page()

        print(f"[→] Navigation vers {BASE_URL} …")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(4_000)   # laisse Streamlit finir le premier rendu

        for slug, tab_label in TABS:
            out_path = os.path.join(OUT_DIR, f"{slug}.png")
            print(f"[→] Onglet : {tab_label}")

            # Clique sur le bon onglet
            try:
                tab_btn = page.get_by_role("tab", name=tab_label)
                await tab_btn.click()
                await page.wait_for_timeout(2_500)
            except Exception as e:
                print(f"   [!] Impossible de cliquer sur l'onglet : {e}")

            # Screenshot pleine page
            await page.screenshot(path=out_path, full_page=True)
            print(f"   [✓] Sauvegardé : {out_path}")

        # ── Bonus : vue globale avec charts en scrollant ──────────────────────
        print("[→] Vue Globale (scrolled) …")
        try:
            await page.get_by_role("tab", name="📊 Vue Globale").click()
            await page.wait_for_timeout(2_000)
            await page.evaluate("window.scrollTo(0, 600)")
            await page.wait_for_timeout(1_000)
            await page.screenshot(
                path=os.path.join(OUT_DIR, "01b_vue_globale_charts.png"),
                full_page=False,
                clip={"x": 0, "y": 0, "width": 1600, "height": 900},
            )
            print("   [✓] Sauvegardé : 01b_vue_globale_charts.png")
        except Exception as e:
            print(f"   [!] {e}")

        await browser.close()
        print("\n[✓] Tous les screenshots ont été capturés.")


asyncio.run(capture_all())
