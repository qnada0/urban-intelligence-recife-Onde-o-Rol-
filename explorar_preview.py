import os
import math
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

st.set_page_config(page_title="Explorar Recife · Preview", page_icon="🔍", layout="wide")

# ══════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
html,body,[class*="css"]{font-family:'Inter',sans-serif;}

[data-testid="stAppViewContainer"]{
  background:
    radial-gradient(ellipse 70% 50% at 20% -10%,rgba(29,78,216,.18) 0%,transparent 60%),
    radial-gradient(ellipse 50% 40% at 85% 110%,rgba(5,150,105,.12) 0%,transparent 60%),
    #0b1120 !important;}
[data-testid="block-container"]{background:transparent!important;}
.main .block-container{padding-top:1.2rem!important;}

/* inputs */
.stTextInput>div>div,.stSelectbox>div>div,.stMultiSelect>div>div{
  background:rgba(255,255,255,.06)!important;border-color:rgba(255,255,255,.1)!important;
  border-radius:10px!important;color:white!important;}
.stTextInput label,.stSelectbox label,.stMultiSelect label,.stSlider label{
  color:#94a3b8!important;font-size:12px!important;font-weight:600!important;}

/* page header */
.pg-label{color:#22c55e;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;}
.pg-title{font-family:'Syne',sans-serif;font-size:30px;font-weight:800;color:white;margin-bottom:4px;}
.pg-title span{color:#22c55e;}
.pg-desc{color:#64748b;font-size:14px;margin-bottom:18px;}

/* KPI mini */
.kpi-mini{background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.09);border-radius:14px;padding:16px 18px;
  box-shadow:0 4px 16px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.06);}
.kpi-mini .v{font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:white;line-height:1;}
.kpi-mini .l{color:#64748b;font-size:11px;margin-top:4px;text-transform:uppercase;letter-spacing:.5px;}

/* chips de bairro/categoria */
.chip-row{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:4px;}
div[data-testid="column"] .stButton button[kind="secondary"]{
  background:rgba(255,255,255,.05)!important;color:#94a3b8!important;
  border:1px solid rgba(255,255,255,.1)!important;border-radius:999px!important;
  font-size:13px!important;font-weight:600!important;padding:6px 16px!important;
  transition:all .15s!important;}
div[data-testid="column"] .stButton button[kind="secondary"]:hover{
  border-color:rgba(255,255,255,.25)!important;color:white!important;}
div[data-testid="column"] .stButton button[kind="primary"]{
  background:linear-gradient(135deg,#059669,#0f766e)!important;color:white!important;
  border:1px solid rgba(34,197,94,.4)!important;border-radius:999px!important;
  font-size:13px!important;font-weight:700!important;padding:6px 16px!important;
  box-shadow:0 3px 12px rgba(5,150,105,.35)!important;}
.chip-label{color:#64748b;font-size:11px;font-weight:700;letter-spacing:1.5px;
  text-transform:uppercase;margin:14px 0 8px;}

/* filter bar */
.fb{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  border-radius:14px;padding:14px 18px;margin-bottom:18px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05);}

/* ── PLACE CARD (vertical, foto no topo) ── */
@keyframes cardIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
.place-card{
  border-radius:16px;overflow:hidden;margin-bottom:10px;
  background:linear-gradient(145deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.09);
  box-shadow:0 6px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.06);
  transition:transform .18s,border-color .18s;animation:cardIn .35s ease both;
}
.place-card:hover{transform:translateY(-4px);border-color:rgba(255,255,255,.18);}
.place-photo{height:110px;display:flex;align-items:center;justify-content:center;
  font-size:38px;position:relative;}
.place-photo .price-tag{position:absolute;top:8px;right:8px;background:rgba(0,0,0,.45);
  color:white;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;
  backdrop-filter:blur(4px);}
.place-photo .cat-tag{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.45);
  color:#e2e8f0;font-size:10px;font-weight:600;padding:2px 8px;border-radius:6px;
  text-transform:uppercase;letter-spacing:.5px;backdrop-filter:blur(4px);}
.place-body{padding:12px 14px 14px;}
.place-name{font-family:'Syne',sans-serif;font-size:14px;font-weight:800;color:white;
  margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.place-rating{color:#f59e0b;font-size:13px;font-weight:700;margin-bottom:4px;}
.place-meta{color:#64748b;font-size:12px;display:flex;align-items:center;gap:4px;}

/* detalhe selecionado */
.detail-panel{background:linear-gradient(145deg,rgba(34,197,94,.08),rgba(255,255,255,.02));
  border:1px solid rgba(34,197,94,.25);border-radius:16px;padding:20px 24px;margin-bottom:20px;
  box-shadow:0 8px 28px rgba(0,0,0,.4);}
.detail-title{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:white;margin-bottom:6px;}

/* botão ver detalhes */
div[data-testid="column"] .stButton button{
  background:rgba(255,255,255,.06)!important;color:#cbd5e1!important;
  border:1px solid rgba(255,255,255,.1)!important;border-radius:8px!important;
  font-size:12px!important;font-weight:600!important;padding:6px 0!important;
  transition:all .15s!important;}
div[data-testid="column"] .stButton button:hover{
  background:rgba(34,197,94,.15)!important;border-color:rgba(34,197,94,.4)!important;color:#86efac!important;}

/* pagination */
.page-info{color:#64748b;font-size:13px;text-align:center;margin:14px 0;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  DADOS
# ══════════════════════════════════════════════════════════════
if not DATABASE_URL:
    st.error("DATABASE_URL não encontrada no .env")
    st.stop()

engine = create_engine(DATABASE_URL)

@st.cache_data
def load_places():
    return pd.read_sql("SELECT * FROM places", engine)

df = load_places()
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

CAT_ICON = {"gastronomia": "🍽️", "lazer": "🎯", "cultura": "🎭"}
CAT_BG = {
    "gastronomia": "linear-gradient(135deg,#78350f,#3b1a03)",
    "lazer":       "linear-gradient(135deg,#1e3a5f,#0c1e3a)",
    "cultura":     "linear-gradient(135deg,#3b1a6b,#1a0a30)",
}
PRICE = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}

if "selected_place" not in st.session_state:
    st.session_state.selected_place = None
if "page_num" not in st.session_state:
    st.session_state.page_num = 1
if "chip_bairros" not in st.session_state:
    st.session_state.chip_bairros = set()
if "chip_cats" not in st.session_state:
    st.session_state.chip_cats = set()

# ══════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="pg-label">🔍 EXPLORAR</div>', unsafe_allow_html=True)
st.markdown('<div class="pg-title">Explore <span>Recife</span></div>', unsafe_allow_html=True)
st.markdown('<div class="pg-desc">Navegue por todos os locais cadastrados, busque e filtre como quiser.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  RESUMO RÁPIDO (sem repetir os KPI cards da home)
# ══════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="color:#94a3b8;font-size:13px;margin-bottom:18px;">
  <strong style="color:white;">{len(df)}</strong> locais ·
  <strong style="color:white;">{df['neighborhood'].nunique()}</strong> bairros ·
  <strong style="color:white;">{df['category'].nunique()}</strong> categorias ·
  <strong style="color:white;">{df['average_rating'].mean():.1f} ⭐</strong> de média
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  BUSCA
# ══════════════════════════════════════════════════════════════
search = st.text_input("🔎 Buscar local pelo nome", placeholder="Ex: Beijupirá, Camarada Camarão...")

# ══════════════════════════════════════════════════════════════
#  CHIPS — CATEGORIA
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="chip-label">Categoria</div>', unsafe_allow_html=True)
cat_counts = df["category"].value_counts()
cat_list = sorted(df["category"].dropna().unique())
ccols = st.columns(len(cat_list) + 1)
with ccols[0]:
    if st.button(f"Todas ({len(df)})", key="chip_cat_all",
                 type="primary" if not st.session_state.chip_cats else "secondary",
                 use_container_width=True):
        st.session_state.chip_cats = set()
        st.rerun()
for i, cat in enumerate(cat_list, start=1):
    with ccols[i]:
        active = cat in st.session_state.chip_cats
        if st.button(f"{cat.capitalize()} ({cat_counts[cat]})", key=f"chip_cat_{cat}",
                     type="primary" if active else "secondary", use_container_width=True):
            if active:
                st.session_state.chip_cats.discard(cat)
            else:
                st.session_state.chip_cats.add(cat)
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  CHIPS — BAIRRO
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="chip-label">Bairro</div>', unsafe_allow_html=True)
bairro_counts = df["neighborhood"].value_counts()
bairro_list = sorted(df["neighborhood"].dropna().unique())
bcols = st.columns(len(bairro_list) + 1)
with bcols[0]:
    if st.button(f"Todos ({len(df)})", key="chip_bairro_all",
                 type="primary" if not st.session_state.chip_bairros else "secondary",
                 use_container_width=True):
        st.session_state.chip_bairros = set()
        st.rerun()
for i, b in enumerate(bairro_list, start=1):
    with bcols[i]:
        active = b in st.session_state.chip_bairros
        if st.button(f"{b} ({bairro_counts[b]})", key=f"chip_bairro_{b}",
                     type="primary" if active else "secondary", use_container_width=True):
            if active:
                st.session_state.chip_bairros.discard(b)
            else:
                st.session_state.chip_bairros.add(b)
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  FILTROS SECUNDÁRIOS (subcategoria, preço, avaliação, ordenação)
# ══════════════════════════════════════════════════════════════
st.markdown('<div class="fb">', unsafe_allow_html=True)
c3, c4, c5, c6 = st.columns([1.3, 1, 1, 1.3])

df_sub = df if not st.session_state.chip_cats else df[df["category"].isin(st.session_state.chip_cats)]
sel_subs = c3.multiselect("Subcategoria", sorted(df_sub["subcategory"].dropna().unique()))

sel_price = c4.select_slider("Preço máx.", options=[1, 2, 3, 4], value=4,
                              format_func=lambda x: PRICE.get(x, str(x)))

sel_rating = c5.slider("Avaliação mín.", 0.0, 5.0, 0.0, 0.5)

sort_by = c6.selectbox("Ordenar por", ["Mais relevantes", "Melhor avaliados", "Menor preço", "Nome A-Z"], index=0)
st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  APLICAR FILTROS
# ══════════════════════════════════════════════════════════════
result = df.copy()
if search:
    result = result[result["name"].str.contains(search, case=False, na=False)]
if st.session_state.chip_bairros:
    result = result[result["neighborhood"].isin(st.session_state.chip_bairros)]
if st.session_state.chip_cats:
    result = result[result["category"].isin(st.session_state.chip_cats)]
if sel_subs:
    result = result[result["subcategory"].isin(sel_subs)]
result = result[result["average_price_level"] <= sel_price]
result = result[result["average_rating"] >= sel_rating]

if sort_by == "Melhor avaliados":
    result = result.sort_values("average_rating", ascending=False)
elif sort_by == "Menor preço":
    result = result.sort_values("average_price_level", ascending=True)
elif sort_by == "Nome A-Z":
    result = result.sort_values("name", ascending=True)
else:
    result = result.sort_values("average_rating", ascending=False)

# reseta página se filtro mudar o total
total_results = len(result)
PER_PAGE = 12
max_page = max(1, math.ceil(total_results / PER_PAGE)) if total_results else 1

if st.session_state.page_num > max_page:
    st.session_state.page_num = 1

st.markdown(f'<div style="color:#94a3b8;font-size:13px;margin-bottom:14px;">'
            f'<strong style="color:white;">{total_results}</strong> locais encontrados</div>',
            unsafe_allow_html=True)

if total_results == 0:
    st.info("Nenhum local encontrado com esses filtros. Tente ampliar a busca.")
    st.stop()

# ══════════════════════════════════════════════════════════════
#  DETALHE (se um card foi selecionado)
# ══════════════════════════════════════════════════════════════
if st.session_state.selected_place is not None:
    sel = df[df["id"] == st.session_state.selected_place]
    if not sel.empty:
        row = sel.iloc[0]
        icon = CAT_ICON.get(row["category"], "📍")
        pl = PRICE.get(int(row["average_price_level"]) if row["average_price_level"] else 2, "$$")
        st.markdown(f"""
<div class="detail-panel">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div class="detail-title">{icon} {row['name']}</div>
      <div style="color:#94a3b8;font-size:13px;line-height:1.7;">
        ⭐ <strong style="color:#fbbf24;">{row['average_rating']}</strong> &nbsp;·&nbsp;
        {pl} &nbsp;·&nbsp; 📍 {row['neighborhood']}<br>
        Categoria: <strong style="color:white;">{row['category']}</strong> ·
        Subcategoria: <strong style="color:white;">{row['subcategory']}</strong>
      </div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
        if st.button("✕ Fechar detalhes"):
            st.session_state.selected_place = None
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  GRID DE CARDS (paginado)
# ══════════════════════════════════════════════════════════════
start = (st.session_state.page_num - 1) * PER_PAGE
end = start + PER_PAGE
page_data = result.iloc[start:end]

cols = st.columns(4)
for i, (_, row) in enumerate(page_data.iterrows()):
    col = cols[i % 4]
    icon = CAT_ICON.get(row["category"], "📍")
    bg = CAT_BG.get(row["category"], "linear-gradient(135deg,#1f2937,#111827)")
    pl = PRICE.get(int(row["average_price_level"]) if row["average_price_level"] else 2, "$$")

    with col:
        st.markdown(f"""
<div class="place-card">
  <div class="place-photo" style="background:{bg};">
    {icon}
    <span class="cat-tag">{row['category']}</span>
    <span class="price-tag">{pl}</span>
  </div>
  <div class="place-body">
    <div class="place-name" title="{row['name']}">{row['name']}</div>
    <div class="place-rating">⭐ {row['average_rating']}</div>
    <div class="place-meta">📍 {row['neighborhood']}</div>
  </div>
</div>""", unsafe_allow_html=True)
        if st.button("Ver detalhes", key=f"btn_{row['id']}", use_container_width=True):
            st.session_state.selected_place = row["id"]
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  PAGINAÇÃO
# ══════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
with pcol1:
    if st.button("← Anterior", disabled=st.session_state.page_num <= 1, use_container_width=True):
        st.session_state.page_num -= 1
        st.rerun()
with pcol2:
    st.markdown(f'<div class="page-info">Página {st.session_state.page_num} de {max_page} '
                f'&nbsp;·&nbsp; mostrando {start+1}–{min(end,total_results)} de {total_results}</div>',
                unsafe_allow_html=True)
with pcol3:
    if st.button("Próxima →", disabled=st.session_state.page_num >= max_page, use_container_width=True):
        st.session_state.page_num += 1
        st.rerun()
