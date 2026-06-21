"""
Módulo da página "Explorar Recife".

COMO INTEGRAR no seu dashboard_app.py:

1. Cole este arquivo na mesma pasta do dashboard_app.py.

2. No topo do dashboard_app.py, adicione:
       from explorar_page import render_explorar

3. No st.radio() da sidebar, adicione "explorar" nas opções e no format_func:
       options=["executiva", "explorar", "analise", "recomendacoes", ...]
       format_func=lambda x: {
           ...,
           "explorar": "🔍  Explorar Recife",
           ...
       }[x]

4. No bloco if/elif das páginas, adicione:
       elif page == "explorar":
           render_explorar(df_places)

Pronto — a função abaixo já injeta seu próprio CSS (com classes prefixadas "expl-"
para não colidir com o resto do app) e usa o df_places que você já carrega.
"""

import math
import pandas as pd
import streamlit as st

CAT_ICON = {"gastronomia": "🍽️", "lazer": "🎯", "cultura": "🎭"}
CAT_BG = {
    "gastronomia": "linear-gradient(135deg,#78350f,#3b1a03)",
    "lazer":       "linear-gradient(135deg,#1e3a5f,#0c1e3a)",
    "cultura":     "linear-gradient(135deg,#3b1a6b,#1a0a30)",
}
PRICE = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$"}

def _inject_css():
    # Sempre emite o CSS — o Streamlit reexecuta o script inteiro a cada
    # interação, então não dá pra "injetar uma vez só" como em HTML estático.
    st.markdown("""
<style>
.expl-chip-label{color:#64748b;font-size:11px;font-weight:700;letter-spacing:1.5px;
  text-transform:uppercase;margin:16px 0 8px;}
div[data-testid="column"] .stButton button{
  white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
  min-height:36px!important;}
div[data-testid="column"] .stButton button[kind="secondary"]{
  background:rgba(255,255,255,.05)!important;color:#94a3b8!important;
  border:1px solid rgba(255,255,255,.1)!important;border-radius:999px!important;
  font-size:12.5px!important;font-weight:600!important;padding:6px 10px!important;
  transition:all .15s!important;}
div[data-testid="column"] .stButton button[kind="secondary"]:hover{
  border-color:rgba(255,255,255,.25)!important;color:white!important;}
div[data-testid="column"] .stButton button[kind="primary"]{
  background:linear-gradient(135deg,#059669,#0f766e)!important;color:white!important;
  border:1px solid rgba(34,197,94,.4)!important;border-radius:999px!important;
  font-size:12.5px!important;font-weight:700!important;padding:6px 10px!important;
  box-shadow:0 3px 12px rgba(5,150,105,.35)!important;}
div[data-testid="column"]{
  padding-left:3px!important;padding-right:3px!important;}

@keyframes explCardIn{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
.expl-card{
  border-radius:16px;overflow:hidden;margin-bottom:10px;
  background:linear-gradient(145deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.09);
  box-shadow:0 6px 20px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.06);
  transition:transform .18s,border-color .18s;animation:explCardIn .35s ease both;
}
.expl-card:hover{transform:translateY(-4px);border-color:rgba(255,255,255,.18);}
.expl-photo{height:120px;display:flex;align-items:center;justify-content:center;
  font-size:38px;position:relative;color:white;}
.expl-photo .expl-overlay{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(0,0,0,.1),rgba(0,0,0,.4));}
.expl-photo .expl-price{position:absolute;top:8px;right:8px;background:rgba(0,0,0,.5);
  color:white;font-size:11px;font-weight:700;padding:2px 8px;border-radius:6px;z-index:2;}
.expl-photo .expl-cat{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.5);
  color:#e2e8f0;font-size:10px;font-weight:600;padding:2px 8px;border-radius:6px;
  text-transform:uppercase;letter-spacing:.5px;z-index:2;}
.expl-photo .expl-icon{position:relative;z-index:2;}
.expl-body{padding:12px 14px 14px;}
.expl-name{font-family:'Inter',sans-serif;font-size:14px;font-weight:800;color:white;
  margin-bottom:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.expl-rating{color:#f59e0b;font-size:13px;font-weight:700;margin-bottom:4px;}
.expl-meta{color:#64748b;font-size:12px;}

.expl-detail{background:linear-gradient(145deg,rgba(34,197,94,.08),rgba(255,255,255,.02));
  border:1px solid rgba(34,197,94,.25);border-radius:16px;padding:18px 22px;margin-bottom:18px;
  box-shadow:0 8px 28px rgba(0,0,0,.4);display:flex;gap:18px;align-items:center;}
.expl-detail img{width:100px;height:100px;border-radius:12px;object-fit:cover;flex-shrink:0;}
.expl-detail-title{font-family:'Inter',sans-serif;font-size:19px;font-weight:800;color:white;margin-bottom:6px;}
.expl-page-info{color:#64748b;font-size:13px;text-align:center;margin:14px 0;}
</style>
""", unsafe_allow_html=True)


def _photo_block(row, image_url=None):
    icon = CAT_ICON.get(row["category"], "📍")
    bg = CAT_BG.get(row["category"], "linear-gradient(135deg,#1f2937,#111827)")
    price_val = row.get("average_price_level")
    pl = PRICE.get(int(price_val) if pd.notna(price_val) else 2, "$$")

    if image_url is None:
        image_url = row.get("photo_url")
    has_photo = isinstance(image_url, str) and image_url.strip() != ""

    if has_photo:
        style = f"background-image:url('{image_url}');background-size:cover;background-position:center;"
        icon_html = ""
        overlay = '<div class="expl-overlay"></div>'
    else:
        style = f"background:{bg};"
        icon_html = f'<span class="expl-icon">{icon}</span>'
        overlay = ""

    return f"""
<div class="expl-photo" style="{style}">
  {overlay}
  {icon_html}
  <span class="expl-cat">{row['category']}</span>
  <span class="expl-price">{pl}</span>
</div>"""


def render_explorar(df: pd.DataFrame, get_image_fn=None):
    """
    get_image_fn: função opcional (name, category, subcategory, row) -> url.
    Se você já tem get_place_image() no seu dashboard_app.py, passe ela aqui
    para reaproveitar o fallback de imagens por categoria/subcategoria:
        render_explorar(df_places, get_image_fn=get_place_image)
    """
    _inject_css()

    for key, default in {
        "expl_selected": None, "expl_page": 1,
        "expl_chip_cats": set(), "expl_chip_bairros": set(),
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    st.markdown('<div class="page-label">🔍 EXPLORAR</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Explore <span>Recife</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-desc">Navegue por todos os locais cadastrados, busque e filtre como quiser.</div>', unsafe_allow_html=True)

    st.markdown(f"""
<div style="color:#94a3b8;font-size:13px;margin-bottom:16px;">
  <strong style="color:white;">{len(df)}</strong> locais ·
  <strong style="color:white;">{df['neighborhood'].nunique()}</strong> bairros ·
  <strong style="color:white;">{df['category'].nunique()}</strong> categorias ·
  <strong style="color:white;">{df['average_rating'].mean():.1f} ⭐</strong> de média
</div>""", unsafe_allow_html=True)

    search = st.text_input("🔎 Buscar local pelo nome", placeholder="Ex: Beijupirá, Camarada Camarão...", key="expl_search")

    # ── chips categoria ──
    st.markdown('<div class="expl-chip-label">Categoria</div>', unsafe_allow_html=True)
    cat_counts = df["category"].value_counts()
    cat_list = sorted(df["category"].dropna().unique())
    ccols = st.columns(len(cat_list) + 1)
    with ccols[0]:
        if st.button(f"Todas ({len(df)})", key="expl_cat_all",
                     type="primary" if not st.session_state.expl_chip_cats else "secondary",
                     use_container_width=True):
            st.session_state.expl_chip_cats = set(); st.rerun()
    for i, cat in enumerate(cat_list, start=1):
        with ccols[i]:
            active = cat in st.session_state.expl_chip_cats
            if st.button(f"{cat.capitalize()} ({cat_counts[cat]})", key=f"expl_cat_{cat}",
                         type="primary" if active else "secondary", use_container_width=True):
                (st.session_state.expl_chip_cats.discard(cat) if active
                 else st.session_state.expl_chip_cats.add(cat))
                st.rerun()

    # ── chips bairro ──
    st.markdown('<div class="expl-chip-label">Bairro</div>', unsafe_allow_html=True)
    b_counts = df["neighborhood"].value_counts()
    b_list = sorted(df["neighborhood"].dropna().unique())

    CHIPS_PER_ROW = 6
    all_bairro_items = [("__all__", f"Todos ({len(df)})")] + \
        [(b, f"{b} ({b_counts[b]})") for b in b_list]

    for row_start in range(0, len(all_bairro_items), CHIPS_PER_ROW):
        row_items = all_bairro_items[row_start:row_start + CHIPS_PER_ROW]
        row_cols = st.columns(CHIPS_PER_ROW)
        for col, (b_key, b_label) in zip(row_cols, row_items):
            with col:
                if b_key == "__all__":
                    active = not st.session_state.expl_chip_bairros
                    if st.button(b_label, key="expl_bairro_all",
                                 type="primary" if active else "secondary",
                                 use_container_width=True):
                        st.session_state.expl_chip_bairros = set(); st.rerun()
                else:
                    active = b_key in st.session_state.expl_chip_bairros
                    if st.button(b_label, key=f"expl_bairro_{b_key}",
                                 type="primary" if active else "secondary",
                                 use_container_width=True):
                        (st.session_state.expl_chip_bairros.discard(b_key) if active
                         else st.session_state.expl_chip_bairros.add(b_key))
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    sel_price = c1.selectbox(
        "Preço máx.",
        options=[1, 2, 3, 4],
        index=3,
        format_func=lambda x: PRICE.get(x, str(x)),
        key="expl_price"
    )
    sel_rating = c2.slider("Avaliação mín.", 0.0, 5.0, 0.0, 0.5, key="expl_rating")
    sort_by = c3.selectbox("Ordenar por", ["Mais relevantes", "Melhor avaliados", "Menor preço", "Nome A-Z"],
                            key="expl_sort")

    # ── aplicar filtros ──
    result = df.copy()
    if search:
        result = result[result["name"].str.contains(search, case=False, na=False)]
    if st.session_state.expl_chip_bairros:
        result = result[result["neighborhood"].isin(st.session_state.expl_chip_bairros)]
    if st.session_state.expl_chip_cats:
        result = result[result["category"].isin(st.session_state.expl_chip_cats)]
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

    total = len(result)
    PER_PAGE = 12
    max_page = max(1, math.ceil(total / PER_PAGE)) if total else 1
    if st.session_state.expl_page > max_page:
        st.session_state.expl_page = 1

    st.markdown(f'<div style="color:#94a3b8;font-size:13px;margin:14px 0;">'
                f'<strong style="color:white;">{total}</strong> locais encontrados</div>', unsafe_allow_html=True)

    if total == 0:
        st.info("Nenhum local encontrado com esses filtros. Tente ampliar a busca.")
        return

    # ── painel de detalhe ──
    if st.session_state.expl_selected is not None:
        sel = df[df["id"] == st.session_state.expl_selected]
        if not sel.empty:
            row = sel.iloc[0]
            icon = CAT_ICON.get(row["category"], "📍")
            pl = PRICE.get(int(row["average_price_level"]) if pd.notna(row["average_price_level"]) else 2, "$$")
            photo_url = (get_image_fn(row["name"], row["category"], row.get("subcategory"), row)
                         if get_image_fn else row.get("photo_url"))
            img_html = f'<img src="{photo_url}">' if isinstance(photo_url, str) and photo_url else ""
            st.markdown(f"""
<div class="expl-detail">
  {img_html}
  <div>
    <div class="expl-detail-title">{icon} {row['name']}</div>
    <div style="color:#94a3b8;font-size:13px;line-height:1.7;">
      ⭐ <strong style="color:#fbbf24;">{row['average_rating']}</strong> &nbsp;·&nbsp;
      {pl} &nbsp;·&nbsp; 📍 {row['neighborhood']}<br>
      Categoria: <strong style="color:white;">{row['category']}</strong> ·
      Subcategoria: <strong style="color:white;">{row['subcategory']}</strong>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
            if st.button("✕ Fechar detalhes", key="expl_close_detail"):
                st.session_state.expl_selected = None
                st.rerun()

    # ── grid paginado ──
    start = (st.session_state.expl_page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_data = result.iloc[start:end]

    cols = st.columns(4)
    for i, (_, row) in enumerate(page_data.iterrows()):
        with cols[i % 4]:
            img_url = get_image_fn(row["name"], row["category"], row.get("subcategory"), row) if get_image_fn else None
            st.markdown(f"""
<div class="expl-card">
  {_photo_block(row, image_url=img_url)}
  <div class="expl-body">
    <div class="expl-name" title="{row['name']}">{row['name']}</div>
    <div class="expl-rating">⭐ {row['average_rating']}</div>
    <div class="expl-meta">📍 {row['neighborhood']}</div>
  </div>
</div>""", unsafe_allow_html=True)
            if st.button("Ver detalhes", key=f"expl_btn_{row['id']}", use_container_width=True):
                st.session_state.expl_selected = row["id"]
                st.rerun()

    # ── paginação ──
    st.markdown("<br>", unsafe_allow_html=True)
    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.button("← Anterior", disabled=st.session_state.expl_page <= 1,
                      use_container_width=True, key="expl_prev"):
            st.session_state.expl_page -= 1; st.rerun()
    with p2:
        st.markdown(f'<div class="expl-page-info">Página {st.session_state.expl_page} de {max_page} '
                    f'&nbsp;·&nbsp; mostrando {start+1}–{min(end,total)} de {total}</div>', unsafe_allow_html=True)
    with p3:
        if st.button("Próxima →", disabled=st.session_state.expl_page >= max_page,
                      use_container_width=True, key="expl_next"):
            st.session_state.expl_page += 1; st.rerun()
