import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

df_places = pd.read_sql("SELECT * FROM places", engine)

# ========================
# Gráfico 1 - Categoria
# ========================
plt.figure()
df_places["category"].value_counts().plot(kind="bar")
plt.title("Distribuição de experiências por categoria")
plt.xlabel("Categoria")
plt.ylabel("Quantidade")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

# ========================
# Gráfico 2 - Avaliação média
# ========================
plt.figure()
df_places.groupby("category")["average_rating"].mean().plot(kind="bar")
plt.title("Qualidade média por categoria")
plt.xlabel("Categoria")
plt.ylabel("Avaliação média")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

# ========================
# Gráfico 3 - Bairros
# ========================
plt.figure()
df_places["neighborhood"].value_counts().plot(kind="bar")
plt.title("Concentração de atividades por bairro")
plt.xlabel("Bairro")
plt.ylabel("Quantidade")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# ========================
# Gráfico 4 - Preço
# ========================
plt.figure()
df_places["average_price_level"].value_counts().sort_index().plot(kind="bar")
plt.title("Distribuição por faixa de preço")
plt.xlabel("Preço (1=barato, 3=caro)")
plt.ylabel("Quantidade")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

df_places["score_simulado"] = df_places["average_rating"] * (1 / df_places["average_price_level"])

plt.figure()
df_places.groupby("category")["score_simulado"].mean().plot(kind="bar")
plt.title("Score de atratividade por categoria")
plt.xlabel("Categoria")
plt.ylabel("Score")
plt.tight_layout()
plt.show()