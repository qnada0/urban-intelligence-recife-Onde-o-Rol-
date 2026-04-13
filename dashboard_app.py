import os
import pandas as pd
import streamlit as st
import requests
import matplotlib.pyplot as plt
import folium
import plotly.express as px
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def create_smart_map(filtered_df, recommendations=None, user_lat=None, user_lon=None):
    # Centro inicial do mapa
    if user_lat is not None and user_lon is not None:
        center_lat, center_lon = user_lat, user_lon
    elif not filtered_df.empty:
        center_lat = filtered_df["latitude"].mean()
        center_lon = filtered_df["longitude"].mean()
    else:
        center_lat, center_lon = -8.0476, -34.8770  # Recife padrão

    mapa = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(mapa)

    # Marca usuário
    if user_lat is not None and user_lon is not None:
        folium.Marker(
            [user_lat, user_lon],
            popup="Sua localização",
            tooltip="Sua localização",
            icon=folium.Icon(color="red", icon="user")
        ).add_to(mapa)

     # Linhas entre usuário e recomendações
    if recommendations and user_lat is not None and user_lon is not None:
        for item in recommendations:
            matching_rows = filtered_df[filtered_df["id"] == item["id"]]

            if not matching_rows.empty:
                row = matching_rows.iloc[0]

                folium.PolyLine(
                    locations=[
                        [user_lat, user_lon],
                        [row["latitude"], row["longitude"]]
                    ],
                    color="green",
                    weight=3,
                    opacity=0.6,
                    tooltip=f"Rota sugerida até {row['name']}"
                ).add_to(mapa)

    # IDs recomendados para destaque
    recommended_ids = set()
    if recommendations: 
        recommended_ids = {item["id"] for item in recommendations}

    category_colors = {
    "gastronomia": "red",
    "lazer": "blue",
    "cultura": "purple"
}

    # Marcadores da base
    for _, row in filtered_df.iterrows():
        place_id = row["id"]
        is_recommended = place_id in recommended_ids

        popup_text = f"""
        <b>{row['name']}</b><br>
        Categoria: {row['category']}<br>
        Subcategoria: {row['subcategory']}<br>
        Bairro: {row['neighborhood']}<br>
        Avaliação: {row['average_rating']}<br>
        Preço: {row['average_price_level']}
        """
        base_color = category_colors.get(row["category"], "gray")

        if is_recommended:
            color = "green"
            icon = "star"
        else:
            color = base_color
            icon = "info-sign"

        folium.Marker(
           [row["latitude"], row["longitude"]],
           popup=popup_text,
           tooltip=f"{row['name']} ⭐ {row['average_rating']}",
           icon=folium.Icon(color=color, icon=icon)
        ).add_to(marker_cluster)

    return mapa

DATABASE_URL = os.getenv("DATABASE_URL")

st.set_page_config(
    page_title="Urban Intelligence Dashboard",
    page_icon="📍",
    layout="wide"
)
st.markdown("""
<style>
/* Fundo geral */
[data-testid="stAppViewContainer"] {
    background-color: #0E1117;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #111827;
}

/* Cards (containers) */
.stContainer {
    background-color: #1F2937;
    padding: 15px;
    border-radius: 12px;
}

/* Títulos */
h1, h2, h3 {
    color: #F9FAFB;
}

/* Texto */
p, span, label {
    color: #D1D5DB;
}

/* Métricas */
[data-testid="stMetricValue"] {
    color: #22C55E;
    font-weight: bold;
}

/* Borda suave */
hr {
    border: 1px solid #374151;
}
</style>
""", unsafe_allow_html=True)

st.title("📍 Urban Intelligence Dashboard")
st.subheader("Análise urbana + recomendações inteligentes")

if "recommendations" not in st.session_state:
    st.session_state.recommendations = []

if "user_latitude_map" not in st.session_state:
    st.session_state.user_latitude_map = None

if "user_longitude_map" not in st.session_state:
    st.session_state.user_longitude_map = None

if "searched" not in st.session_state:
    st.session_state.searched = False

if not DATABASE_URL:
    st.error("DATABASE_URL não encontrada no .env")
    st.stop()

engine = create_engine(DATABASE_URL)

@st.cache_data
def load_places():
    query = "SELECT * FROM places"
    return pd.read_sql(query, engine)

df_places = load_places()

if df_places.empty:
    st.warning("Nenhum dado encontrado na tabela places.")
    st.stop()

# ======================
# FILTROS
# ======================
st.sidebar.header("Filtros")

selected_category = st.sidebar.multiselect(
    "Categoria",
    options=sorted(df_places["category"].dropna().unique()),
    default=sorted(df_places["category"].dropna().unique())
)

selected_neighborhood = st.sidebar.multiselect(
    "Bairro",
    options=sorted(df_places["neighborhood"].dropna().unique()),
    default=sorted(df_places["neighborhood"].dropna().unique())
)

selected_price = st.sidebar.multiselect(
    "Faixa de preço",
    options=sorted(df_places["average_price_level"].dropna().unique()),
    default=sorted(df_places["average_price_level"].dropna().unique())
)

filtered_df = df_places[
    (df_places["category"].isin(selected_category)) &
    (df_places["neighborhood"].isin(selected_neighborhood)) &
    (df_places["average_price_level"].isin(selected_price))
]
filtered_df = filtered_df.copy()

# ======================
# KPIs
# ======================
def card(title, value, icon):
    st.markdown(f"""
    <div style="
        background-color:#1F2937;
        padding:20px;
        border-radius:12px;
        text-align:center;
        box-shadow:0px 4px 12px rgba(0,0,0,0.4);
    ">
        <div style="font-size:20px;">{icon} {title}</div>
        <div style="font-size:32px; font-weight:bold; color:#22C55E;">
            {value}
        </div>
    </div>
    """, unsafe_allow_html=True)


def insight_box(text, bg_color="#1E3A8A", emoji="💡"):
    st.markdown(f"""
    <div style="
        background-color:{bg_color};
        padding:15px;
        border-radius:10px;
        margin-bottom:10px;
        color:white;
        box-shadow:0px 4px 10px rgba(0,0,0,0.3);
    ">
        {emoji} {text}
    </div>
    """, unsafe_allow_html=True)

avg_rating = round(filtered_df["average_rating"].mean(), 2) if not filtered_df["average_rating"].empty else 0
best_rating = round(filtered_df["average_rating"].max(), 2) if not filtered_df["average_rating"].empty else 0
avg_price = round(filtered_df["average_price_level"].mean(), 2) if not filtered_df["average_price_level"].empty else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    card("Total de lugares", len(filtered_df), "📍")

with col2:
    card("Avaliação média", avg_rating, "⭐")

with col3:
    card("Melhor avaliação", best_rating, "🏆")

with col4:
    card("Preço médio", avg_price, "💰")

st.divider()

# ======================
# TABELA DE DADOS
# ======================
st.subheader("📋 Base filtrada")
st.dataframe(
    filtered_df[
        [
            "name",
            "category",
            "subcategory",
            "neighborhood",
            "average_price_level",
            "average_rating"
        ]
    ],
    width="stretch"
)

st.divider()

# ======================
# GRÁFICOS
# ======================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Quantidade por categoria")
    fig1, ax1 = plt.subplots()
    filtered_df["category"].value_counts().plot(kind="bar", ax=ax1)
    ax1.set_xlabel("Categoria")
    ax1.set_ylabel("Quantidade")
    ax1.set_title("Distribuição por categoria")
    plt.xticks(rotation=0)
    st.pyplot(fig1)

with col_right:
    st.subheader("Avaliação média por categoria")
    fig2, ax2 = plt.subplots()
    filtered_df.groupby("category")["average_rating"].mean().plot(kind="bar", ax=ax2)
    ax2.set_xlabel("Categoria")
    ax2.set_ylabel("Avaliação média")
    ax2.set_title("Qualidade média por categoria")
    plt.xticks(rotation=0)
    st.pyplot(fig2)

col_bottom_left, col_bottom_right = st.columns(2)

with col_bottom_left:
    st.subheader("Atividades por bairro")
    fig3, ax3 = plt.subplots()
    filtered_df["neighborhood"].value_counts().plot(kind="bar", ax=ax3)
    ax3.set_xlabel("Bairro")
    ax3.set_ylabel("Quantidade")
    ax3.set_title("Concentração por bairro")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig3)

with col_bottom_right:
    st.subheader("Distribuição por faixa de preço")
    fig4, ax4 = plt.subplots()
    filtered_df["average_price_level"].value_counts().sort_index().plot(kind="bar", ax=ax4)
    ax4.set_xlabel("Preço (1=barato, 3=caro)")
    ax4.set_ylabel("Quantidade")
    ax4.set_title("Faixa de preço")
    plt.xticks(rotation=0)
    st.pyplot(fig4)

st.divider()

st.subheader("📈 Análises estratégicas")

col_extra_left, col_extra_right = st.columns(2)

with col_extra_left:
    st.subheader("Preço vs Avaliação")

    fig5 = px.scatter(
    filtered_df,
    x="average_price_level",
    y="average_rating",
    color="category",
    color_discrete_map={
        "gastronomia": "#F59E0B",
        "lazer": "#3B82F6",
        "cultura": "#8B5CF6"
    },
    hover_data=["name", "neighborhood", "subcategory"],
    text="name",
    title="Preço vs Avaliação"
)
    

    fig5.update_traces(textposition="top center")
    fig5.update_layout(
        xaxis_title="Faixa de preço",
        yaxis_title="Avaliação",
        height=500
    )

    st.plotly_chart(fig5, width="stretch")

with col_extra_right:
    st.subheader("Top bairros por avaliação")

    top_bairros = (
        filtered_df.groupby("neighborhood")["average_rating"]
        .mean()
        .sort_values(ascending=True)
        .tail(10)
        .reset_index()
    )

    fig6 = px.bar(
        top_bairros,
        x="average_rating",
        y="neighborhood",
        orientation="h",
        text="average_rating",
        title="Top bairros por avaliação"
    )

    fig6.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig6.update_traces(marker_color="#6366F1")
    fig6.update_layout(
        xaxis_title="Avaliação média",
        yaxis_title="Bairro",
        height=500
    )

    st.plotly_chart(fig6, width="stretch")



col_dist_left, col_dist_right = st.columns(2)
with col_dist_left:
    st.subheader("Avaliação por lugar")

    rating_by_place = (
        filtered_df[["name", "average_rating"]]
        .sort_values("average_rating", ascending=True)
    )

    fig7 = px.bar(
        rating_by_place,
        x="average_rating",
        y="name",
        orientation="h",
        text="average_rating",
        title="Avaliação por lugar"
    )

    fig7.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig7.update_layout(
        xaxis_title="Avaliação",
        yaxis_title="Lugar",
        height=500
    )

    st.plotly_chart(fig7, width="stretch")

with col_dist_right:
    st.subheader("Distribuição de preços")

    price_dist = (
        filtered_df["average_price_level"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    price_dist.columns = ["average_price_level", "count"]

    fig8 = px.bar(
        price_dist,
        x="average_price_level",
        y="count",
        text="count",
        title="Distribuição de preços"
    )

    fig8.update_layout(
        xaxis_title="Faixa de preço",
        yaxis_title="Quantidade",
        height=500
    )

    st.plotly_chart(fig8, width="stretch")

    st.divider()

st.subheader("💰 Melhor custo-benefício")

filtered_df["cost_benefit"] = (
    filtered_df["average_rating"] / filtered_df["average_price_level"]
)

best_value = filtered_df.sort_values("cost_benefit", ascending=False).head(3)

for i, (_, row) in enumerate(best_value.iterrows(), start=1):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #065F46, #022C22);
        padding:20px;
        border-radius:12px;
        margin-bottom:15px;
        box-shadow:0px 4px 12px rgba(0,0,0,0.6);
    ">
        <h3>🥇 #{i} {row['name']}</h3>
        <p>⭐ {row['average_rating']} | 💰 {row['average_price_level']}</p>
        <p>📊 Score: {round(row['cost_benefit'],2)}</p>
        <p>📍 {row['neighborhood']}</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
  

st.subheader("🧠 Insights inteligentes")

if not filtered_df.empty:
    # Categoria com mais opções
    top_category = filtered_df["category"].value_counts().idxmax()
    top_category_count = filtered_df["category"].value_counts().max()

    # Bairro com melhor avaliação média
    best_neighborhood = (
        filtered_df.groupby("neighborhood")["average_rating"]
        .mean()
        .idxmax()
    )

    best_neighborhood_rating = (
        filtered_df.groupby("neighborhood")["average_rating"]
        .mean()
        .max()
    )

    # Faixa de preço mais comum
    most_common_price = (
        filtered_df["average_price_level"]
        .value_counts()
        .idxmax()
    )

    # Lugar com melhor custo-benefício
    best_value_place = filtered_df.sort_values("cost_benefit", ascending=False).iloc[0]

    # Categoria com melhor avaliação média
    best_category = (
        filtered_df.groupby("category")["average_rating"]
        .mean()
        .idxmax()
    )

    best_category_rating = (
        filtered_df.groupby("category")["average_rating"]
        .mean()
        .max()
    )

    st.markdown(f"""
### 📌 Resumo executivo

- **Categoria com mais opções:** {top_category} ({top_category_count} lugares)
- **Bairro com melhor avaliação média:** {best_neighborhood} ({best_neighborhood_rating:.2f})
- **Faixa de preço mais comum:** {most_common_price}
- **Melhor lugar em custo-benefício:** {best_value_place['name']}
- **Categoria com melhor avaliação média:** {best_category} ({best_category_rating:.2f})
""")

    st.markdown("### 🔍 Interpretação dos dados")

    if top_category == "gastronomia":
        insight_box(
            "A base filtrada mostra predominância de experiências gastronômicas, indicando forte presença desse tipo de atividade na região analisada.",
            bg_color="#1E3A8A",
            emoji="🍽️"
        )
    elif top_category == "lazer":
        insight_box(
            "Os dados indicam maior concentração de opções de lazer, sugerindo uma oferta mais ampla de atividades recreativas.",
            bg_color="#0F766E",
            emoji="🎯"
        )
    elif top_category == "cultura":
        insight_box(
            "A predominância de opções culturais sugere uma base mais voltada a experiências de valor histórico, artístico ou educativo.",
            bg_color="#6D28D9",
            emoji="🎭"
        )

    if most_common_price == 1:
        insight_box(
            "A maior parte das opções analisadas está em uma faixa de preço acessível, o que pode favorecer adesão e frequência de uso.",
            bg_color="#065F46",
            emoji="💸"
        )
    elif most_common_price == 2:
        insight_box(
            "A base apresenta predominância de opções com preço intermediário, equilibrando acessibilidade e valor percebido.",
            bg_color="#1E3A8A",
            emoji="⚖️"
        )
    elif most_common_price == 3:
        insight_box(
            "A maior parte das experiências está em faixa de preço mais elevada, o que pode impactar acessibilidade para alguns perfis.",
            bg_color="#92400E",
            emoji="💰"
        )

    st.markdown("### ⚖️ Qualidade x acessibilidade")

    category_cost_benefit = (
        filtered_df.groupby("category")["cost_benefit"]
        .mean()
        .sort_values(ascending=False)
    )

    best_balance_category = category_cost_benefit.idxmax()
    best_balance_score = category_cost_benefit.max()

    st.write(
        f"A categoria com melhor equilíbrio entre avaliação e preço é **{best_balance_category}**, "
        f"com score médio de custo-benefício **{best_balance_score:.2f}**."
    )
else:
    st.info("Sem dados suficientes para gerar insights inteligentes.")



st.divider()
st.subheader("🏆 Ranking de lugares")

top_places = filtered_df.sort_values("average_rating", ascending=False).head(5)

for i, (_, row) in enumerate(top_places.iterrows(), start=1):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1F2937, #111827);
        padding:20px;
        border-radius:12px;
        margin-bottom:15px;
        box-shadow:0px 4px 12px rgba(0,0,0,0.5);
    ">
        <h3>🏅 #{i} {row['name']}</h3>
        <p>⭐ {row['average_rating']} | 💰 {row['average_price_level']}</p>
        <p>📍 {row['neighborhood']}</p>
        <p>📂 {row['category']} • {row['subcategory']}</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

st.subheader("🗺️ Mapa inteligente das experiências")

mapa_base = create_smart_map(filtered_df)
st_folium(mapa_base, width=1200, height=500)

st.divider()


# ======================
# INSIGHTS AUTOMÁTICOS
# ======================

st.divider()
st.subheader("🎯 Recomendação personalizada")

with st.form("recommendation_form"):
    preferred_category = st.selectbox(
        "Categoria desejada",
        options=sorted(df_places["category"].dropna().unique())
    )

    subcategories = sorted(
        df_places[df_places["category"] == preferred_category]["subcategory"].dropna().unique()
    )

    preferred_subcategory = st.selectbox(
        "Subcategoria desejada",
        options=subcategories if subcategories else [""]
    )

    budget_preference = st.selectbox(
        "Faixa de preço",
        options=[1, 2, 3],
        format_func=lambda x: {1: "1 - Baixo", 2: "2 - Médio", 3: "3 - Alto"}[x]
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        user_latitude = st.number_input("Latitude", value=-8.0476, format="%.4f")

    with col_b:
        user_longitude = st.number_input("Longitude", value=-34.8770, format="%.4f")

    with col_c:
        city = st.text_input("Cidade", value="Recife")

    submitted = st.form_submit_button("Buscar recomendações")


if submitted:
    st.session_state.user_latitude_map = user_latitude
    st.session_state.user_longitude_map = user_longitude
    st.session_state.searched = True

    payload = {
        "preferred_category": preferred_category,
        "preferred_subcategory": preferred_subcategory,
        "budget_preference": budget_preference,
        "user_latitude": user_latitude,
        "user_longitude": user_longitude,
        "city": city
    }

    try:
        response = requests.post(
            "http://127.0.0.1:8000/recommendations/",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            st.session_state.recommendations = response.json()
            
            if not st.session_state.recommendations:
                st.warning("Nenhuma recomendação encontrada.")
        else:
            st.error(f"Erro na API: {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar à API. Verifique se o FastAPI está rodando em http://127.0.0.1:8000")
    except Exception as e:
        st.error(f"Erro ao buscar recomendações: {e}")

if st.session_state.searched and st.session_state.recommendations:
    st.success("Recomendações encontradas!")

    for item in st.session_state.recommendations:
        with st.container():
            st.markdown(f"## 📍 {item['name']}")

            col1, col2, col3 = st.columns(3)

            col1.metric("⭐ Avaliação", item["rating"])
            col2.metric("💰 Preço", item["price_level"])
            col3.metric("🧠 Score", round(item["score"], 2))

            st.write(f"Categoria: {item['category']} | Subcategoria: {item['subcategory']}")

            if "neighborhood" in item:
                st.write(f"📍 Bairro: {item['neighborhood']}")

            if "distance_km" in item:
                st.write(f"📏 Distância: {item['distance_km']} km")

            if "match_level" in item:
                st.write(f"🎯 Compatibilidade: {item['match_level']}")

            if "reason" in item:
                st.info(item["reason"])

            st.divider()

    st.subheader("🧠 Mapa com recomendações destacadas")

    mapa_recomendacoes = create_smart_map(
        filtered_df=df_places,
        recommendations=st.session_state.recommendations,
        user_lat=st.session_state.user_latitude_map,
        user_lon=st.session_state.user_longitude_map
    )

    st_folium(mapa_recomendacoes, width=1200, height=550)

