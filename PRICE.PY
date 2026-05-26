import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import random

st.set_page_config(
    page_title="🍼 ბავშვის პროდუქტების ფასების ინდექსი",
    page_icon="🍼",
    layout="wide"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main { background-color: #f8f9ff; }
    .stMetric { background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }
    .source-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 13px; font-weight: 600; margin: 2px;
    }
    .psp-badge { background: #e8f4fd; color: #1565c0; }
    .aversi-badge { background: #e8f5e9; color: #2e7d32; }
    .gepha-badge { background: #fff3e0; color: #e65100; }
    h1 { color: #1a1a2e; }
    .last-updated { color: #888; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SCRAPER FUNCTIONS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ka-GE,ka;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CATEGORIES = {
    "საფუჭვლეები": ["pampers", "huggies", "libero", "საფუჭველი", "diaper"],
    "ბავშვის კვება": ["cerelac", "nutrilon", "nan", "similac", "porridge", "ფაფა", "ფორმულა"],
    "ბავშვის კოსმეტიკა": ["johnson", "mustela", "chicco", "bubble", "shampoo", "შამპუნი"],
    "სათამაშოები": ["toy", "სათამაშო", "lego", "puzzle"],
}


def scrape_psp(category_keywords: list[str]) -> list[dict]:
    """Scrape PSP.ge for baby products."""
    results = []
    search_term = category_keywords[0]
    url = f"https://psp.ge/ka/search?q={requests.utils.quote(search_term)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # PSP product cards — adjust selectors if site changes
        cards = soup.select(".product-card, .product-item, [class*='product']")[:12]
        for card in cards:
            name_el = card.select_one("[class*='name'], [class*='title'], h3, h4")
            price_el = card.select_one("[class*='price'], .price")
            if name_el and price_el:
                raw_price = price_el.get_text(strip=True).replace("₾", "").replace(",", ".").strip()
                try:
                    price = float(''.join(c for c in raw_price if c.isdigit() or c == '.'))
                    results.append({
                        "სახელი": name_el.get_text(strip=True)[:60],
                        "ფასი (₾)": price,
                        "წყარო": "PSP",
                        "URL": url,
                    })
                except ValueError:
                    pass
    except Exception:
        pass
    return results


def scrape_aversi(category_keywords: list[str]) -> list[dict]:
    """Scrape Aversi.ge for baby products."""
    results = []
    search_term = category_keywords[0]
    url = f"https://aversi.ge/search?q={requests.utils.quote(search_term)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select(".product-card, .product-item, [class*='product']")[:12]
        for card in cards:
            name_el = card.select_one("[class*='name'], [class*='title'], h3, h4")
            price_el = card.select_one("[class*='price']")
            if name_el and price_el:
                raw_price = price_el.get_text(strip=True).replace("₾", "").replace(",", ".").strip()
                try:
                    price = float(''.join(c for c in raw_price if c.isdigit() or c == '.'))
                    results.append({
                        "სახელი": name_el.get_text(strip=True)[:60],
                        "ფასი (₾)": price,
                        "წყარო": "Aversi",
                        "URL": url,
                    })
                except ValueError:
                    pass
    except Exception:
        pass
    return results


def scrape_gepha(category_keywords: list[str]) -> list[dict]:
    """Scrape GEPHA (GPC) for baby products."""
    results = []
    search_term = category_keywords[0]
    url = f"https://www.gpc.ge/ka/search?keyword={requests.utils.quote(search_term)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select(".product-card, .product-item, [class*='product']")[:12]
        for card in cards:
            name_el = card.select_one("[class*='name'], [class*='title'], h3, h4")
            price_el = card.select_one("[class*='price']")
            if name_el and price_el:
                raw_price = price_el.get_text(strip=True).replace("₾", "").replace(",", ".").strip()
                try:
                    price = float(''.join(c for c in raw_price if c.isdigit() or c == '.'))
                    results.append({
                        "სახელი": name_el.get_text(strip=True)[:60],
                        "ფასი (₾)": price,
                        "წყარო": "GEPHA/GPC",
                        "URL": url,
                    })
                except ValueError:
                    pass
    except Exception:
        pass
    return results


# ============================================================
# DEMO DATA FALLBACK (when scraping blocked / JS-only pages)
# ============================================================
DEMO_DATA = {
    "საფუჭვლეები": [
        {"სახელი": "Pampers Active Baby N4 (46ც)", "ფასი (₾)": 28.50, "წყარო": "PSP"},
        {"სახელი": "Pampers Active Baby N4 (46ც)", "ფასი (₾)": 29.90, "წყარო": "Aversi"},
        {"სახელი": "Pampers Active Baby N4 (46ც)", "ფასი (₾)": 27.80, "წყარო": "GEPHA/GPC"},
        {"სახელი": "Huggies Classic N4 (50ც)", "ფასი (₾)": 25.00, "წყარო": "PSP"},
        {"სახელი": "Huggies Classic N4 (50ც)", "ფასი (₾)": 24.50, "წყარო": "Aversi"},
        {"სახელი": "Huggies Classic N4 (50ც)", "ფასი (₾)": 25.50, "წყარო": "GEPHA/GPC"},
        {"სახელი": "Libero Comfort N3 (52ც)", "ფასი (₾)": 22.90, "წყარო": "PSP"},
        {"სახელი": "Libero Comfort N3 (52ც)", "ფასი (₾)": 23.40, "წყარო": "Aversi"},
    ],
    "ბავშვის კვება": [
        {"სახელი": "Nutrilon Premium 1 (400გ)", "ფასი (₾)": 45.00, "წყარო": "PSP"},
        {"სახელი": "Nutrilon Premium 1 (400გ)", "ფასი (₾)": 46.50, "წყარო": "Aversi"},
        {"სახელი": "Nutrilon Premium 1 (400გ)", "ფასი (₾)": 44.00, "წყარო": "GEPHA/GPC"},
        {"სახელი": "NAN Optipro 2 (800გ)", "ფასი (₾)": 62.00, "წყარო": "PSP"},
        {"სახელი": "NAN Optipro 2 (800გ)", "ფასი (₾)": 63.50, "წყარო": "Aversi"},
        {"სახელი": "Cerelac ბრინჯი (250გ)", "ფასი (₾)": 14.90, "წყარო": "PSP"},
        {"სახელი": "Cerelac ბრინჯი (250გ)", "ფასი (₾)": 15.20, "წყარო": "Aversi"},
        {"სახელი": "Cerelac ბრინჯი (250გ)", "ფასი (₾)": 14.50, "წყარო": "GEPHA/GPC"},
    ],
    "ბავშვის კოსმეტიკა": [
        {"სახელი": "Johnson's Baby შამპუნი (200მლ)", "ფასი (₾)": 12.50, "წყარო": "PSP"},
        {"სახელი": "Johnson's Baby შამპუნი (200მლ)", "ფასი (₾)": 13.00, "წყარო": "Aversi"},
        {"სახელი": "Johnson's Baby შამპუნი (200მლ)", "ფასი (₾)": 12.00, "წყარო": "GEPHA/GPC"},
        {"სახელი": "Mustela Bebe კრემი (50მლ)", "ფასი (₾)": 28.00, "წყარო": "PSP"},
        {"სახელი": "Mustela Bebe კრემი (50მლ)", "ფასი (₾)": 29.50, "წყარო": "Aversi"},
        {"სახელი": "Chicco ბუშტის აბაზანა (500მლ)", "ფასი (₾)": 18.90, "წყარო": "PSP"},
        {"სახელი": "Chicco ბუშტის აბაზანა (500მლ)", "ფასი (₾)": 19.50, "წყარო": "Aversi"},
    ],
}


@st.cache_data(ttl=300)  # cache 5 min
def load_data(use_demo: bool) -> tuple[pd.DataFrame, bool]:
    all_rows = []
    is_demo = use_demo

    if not use_demo:
        progress = st.progress(0, text="PSP-ს სკანირება...")
        for i, (cat, keywords) in enumerate(CATEGORIES.items()):
            progress.progress((i * 3) / (len(CATEGORIES) * 3), text=f"PSP — {cat}")
            all_rows.extend(scrape_psp(keywords))
            time.sleep(random.uniform(0.5, 1.2))

            progress.progress((i * 3 + 1) / (len(CATEGORIES) * 3), text=f"Aversi — {cat}")
            all_rows.extend(scrape_aversi(keywords))
            time.sleep(random.uniform(0.5, 1.2))

            progress.progress((i * 3 + 2) / (len(CATEGORIES) * 3), text=f"GEPHA — {cat}")
            all_rows.extend(scrape_gepha(keywords))
            time.sleep(random.uniform(0.5, 1.2))

        progress.empty()

        if len(all_rows) < 5:
            is_demo = True

    if is_demo:
        for cat, rows in DEMO_DATA.items():
            for r in rows:
                all_rows.append({**r, "კატეგორია": cat})

    df = pd.DataFrame(all_rows)
    if "კატეგორია" not in df.columns:
        df["კატეგორია"] = "სხვა"
    df["განახლდა"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return df, is_demo


# ============================================================
# UI
# ============================================================
st.title("🍼 ბავშვის პროდუქტების ფასების ინდექსი")
st.markdown("**PSP · Aversi · GEPHA** — ფასების შედარება რეალურ დროში")

# Sidebar
with st.sidebar:
    st.header("⚙️ პარამეტრები")
    use_demo = st.toggle("🎭 Demo მონაცემები (სწრაფი ნახვა)", value=True)
    st.caption("გამორთე რეალური სქრეიფინგისთვის — შეიძლება ნელა იმუშაოს")
    st.divider()
    st.markdown("**წყაროები:**")
    st.markdown('<span class="source-badge psp-badge">PSP</span>', unsafe_allow_html=True)
    st.markdown('<span class="source-badge aversi-badge">Aversi</span>', unsafe_allow_html=True)
    st.markdown('<span class="source-badge gepha-badge">GEPHA/GPC</span>', unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 განახლება", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load
with st.spinner("მონაცემები იტვირთება..."):
    df, is_demo = load_data(use_demo)

if is_demo and not use_demo:
    st.warning("⚠️ სკრეიფინგი ვერ მოხერხდა (JS-rendered ან დაბლოკილი). ნაჩვენებია Demo მონაცემები.")
elif is_demo:
    st.info("🎭 Demo მონაცემები — რეალური სქრეიფინგისთვის გამორთე toggle.")

st.caption(f"🕐 განახლდა: {df['განახლდა'].iloc[0] if len(df) > 0 else '—'}")
st.divider()

# ---- KPI ----
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📦 პროდუქტი სულ", len(df))
with col2:
    st.metric("🏪 წყარო", df["წყარო"].nunique())
with col3:
    st.metric("💰 საშ. ფასი", f"₾{df['ფასი (₾)'].mean():.2f}")
with col4:
    cheapest = df.loc[df["ფასი (₾)"].idxmin(), "წყარო"] if len(df) > 0 else "—"
    st.metric("🏆 იაფი წყარო", cheapest)

st.divider()

# ---- CATEGORY FILTER ----
categories = ["ყველა"] + sorted(df["კატეგორია"].unique().tolist())
selected_cat = st.selectbox("📂 კატეგორია", categories)

filtered = df if selected_cat == "ყველა" else df[df["კატეგორია"] == selected_cat]

# ---- CHARTS ----
tab1, tab2, tab3 = st.tabs(["📊 საშუალო ფასი წყაროს მიხედვით", "📈 ფასების სპექტრი", "📋 სრული ცხრილი"])

with tab1:
    avg_by_source_cat = (
        filtered.groupby(["კატეგორია", "წყარო"])["ფასი (₾)"]
        .mean()
        .reset_index()
        .rename(columns={"ფასი (₾)": "საშ. ფასი (₾)"})
    )
    fig = px.bar(
        avg_by_source_cat,
        x="კატეგორია",
        y="საშ. ფასი (₾)",
        color="წყარო",
        barmode="group",
        color_discrete_map={"PSP": "#1565c0", "Aversi": "#2e7d32", "GEPHA/GPC": "#e65100"},
        title="კატეგორიების საშუალო ფასი წყაროს მიხედვით",
        text_auto=".1f",
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Arial",
        yaxis_title="ფასი (₾)",
        legend_title="წყარო",
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig2 = px.box(
        filtered,
        x="წყარო",
        y="ფასი (₾)",
        color="წყარო",
        facet_col="კატეგორია",
        color_discrete_map={"PSP": "#1565c0", "Aversi": "#2e7d32", "GEPHA/GPC": "#e65100"},
        title="ფასების განაწილება კატეგორიისა და წყაროს მიხედვით",
        points="all",
    )
    fig2.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=450,
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.dataframe(
        filtered[["სახელი", "კატეგორია", "ფასი (₾)", "წყარო"]]
        .sort_values("ფასი (₾)")
        .reset_index(drop=True),
        use_container_width=True,
        height=400,
    )
    csv = filtered.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ CSV-ის ჩამოტვირთვა",
        data=csv,
        file_name="baby_price_index.csv",
        mime="text/csv",
    )

# ---- PRICE DIFF TABLE ----
st.divider()
st.subheader("💡 ფასების სხვაობა წყაროებს შორის")

pivot = (
    filtered.groupby(["სახელი", "წყარო"])["ფასი (₾)"]
    .mean()
    .unstack("წყარო")
    .reset_index()
    .dropna(thresh=2)
)
if len(pivot) > 0:
    price_cols = [c for c in ["PSP", "Aversi", "GEPHA/GPC"] if c in pivot.columns]
    if len(price_cols) >= 2:
        pivot["მაქს-მინ სხვაობა (₾)"] = pivot[price_cols].max(axis=1) - pivot[price_cols].min(axis=1)
        pivot["იაფი წყარო"] = pivot[price_cols].idxmin(axis=1)
        pivot = pivot.sort_values("მაქს-მინ სხვაობა (₾)", ascending=False).head(15)

        st.dataframe(
            pivot.style.format({c: "₾{:.2f}" for c in price_cols if c in pivot.columns}
                               | {"მაქს-მინ სხვაობა (₾)": "₾{:.2f}"}),
            use_container_width=True,
            height=350,
        )
    else:
        st.info("შედარებისთვის საჭიროა მინიმუმ 2 წყაროს მონაცემები.")
else:
    st.info("შედარებისთვის საკმარისი მონაცემი არ არის.")
