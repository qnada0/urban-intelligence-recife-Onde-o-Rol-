"""
fetch_places_new.py
Coleta dados reais via Google Places API (New) e grava no PostgreSQL.

Meta: ~562 lugares únicos em Recife.
Estratégia: 16 bairros × 3 grupos de categoria = 48 chamadas.
             Cada chamada traz até 20 resultados.
             Deduplicação por place_id do Google.

Campos coletados: id, name, category, subcategory, neighborhood,
                  average_price_level, average_rating,
                  latitude, longitude, photo_url

Como rodar:
    python fetch_places_new.py

Requisitos no .env:
    GOOGLE_MAPS_API_KEY=sua_chave
    DATABASE_URL=postgresql://...
"""

import os
import time
import requests
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

API_KEY      = os.getenv("GOOGLE_MAPS_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY não encontrada no .env")

URL = "https://places.googleapis.com/v1/places:searchNearby"

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": ",".join([
        "places.id",
        "places.displayName",
        "places.location",
        "places.rating",
        "places.priceLevel",
        "places.primaryType",
        "places.types",
        "places.formattedAddress",
        "places.photos",          # ← fotos reais
    ]),
}

# ─── 16 bairros com coordenadas centrais ────────────────────────────────────
# Os 8 originais mais 8 novos para chegar em ~562 lugares únicos.
NEIGHBORHOODS = {
    # ── Originais ──
    "Boa Viagem":    (-8.1180, -34.9010),
    "Casa Forte":    (-8.0156, -34.9133),
    "Graças":        (-8.0469, -34.9028),
    "Jaqueira":      (-8.0357, -34.9087),
    "Pina":          (-8.0871, -34.8830),
    "Recife Antigo": (-8.0631, -34.8711),
    "Santo Antônio": (-8.0631, -34.8744),
    "Várzea":        (-8.0500, -34.9500),
    # ── Novos ──
    "Boa Vista":     (-8.0597, -34.8791),
    "Madalena":      (-8.0478, -34.9178),
    "Aflitos":       (-8.0308, -34.9028),
    "Derby":         (-8.0552, -34.8971),
    "Torre":         (-8.0628, -34.9178),
    "Imbiribeira":   (-8.1050, -34.9128),
    "Espinheiro":    (-8.0269, -34.9028),
    "Parnamirim":    (-8.0883, -34.9228),
}

RADIUS_METERS = 1600   # raio por bairro

# ─── Tipos do Google agrupados por categoria do projeto ─────────────────────
TYPE_GROUPS = {
    "gastronomia": ["restaurant", "cafe", "bar"],
    "lazer":       ["park", "shopping_mall", "night_club"],
    "cultura":     ["museum", "tourist_attraction", "art_gallery"],
}

PRICE_MAP = {
    "PRICE_LEVEL_FREE":           1,
    "PRICE_LEVEL_INEXPENSIVE":    1,
    "PRICE_LEVEL_MODERATE":       2,
    "PRICE_LEVEL_EXPENSIVE":      3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


def build_photo_url(photo_name: str) -> str | None:
    """Monta URL direta da foto via Places Media endpoint."""
    if not photo_name:
        return None
    return (
        f"https://places.googleapis.com/v1/{photo_name}"
        f"/media?maxWidthPx=480&key={API_KEY}"
    )


def search_nearby(types: list, lat: float, lng: float) -> list:
    payload = {
        "includedTypes": types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": RADIUS_METERS,
            }
        },
    }
    r = requests.post(URL, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("places", [])


def normalize(place: dict, category: str, neighborhood: str) -> dict:
    photos    = place.get("photos", [])
    photo_url = build_photo_url(photos[0]["name"]) if photos else None

    return {
        "place_id":            place.get("id"),
        "name":                place.get("displayName", {}).get("text"),
        "category":            category,
        "subcategory":         place.get("primaryType", category),
        "neighborhood":        neighborhood,
        "average_price_level": PRICE_MAP.get(place.get("priceLevel"), 2),
        "average_rating":      place.get("rating"),
        "latitude":            place.get("location", {}).get("latitude"),
        "longitude":           place.get("location", {}).get("longitude"),
        "photo_url":           photo_url,
    }


def main():
    rows = []
    total_calls = len(NEIGHBORHOODS) * len(TYPE_GROUPS)
    call_count  = 0

    for bairro, (lat, lng) in NEIGHBORHOODS.items():
        for category, types in TYPE_GROUPS.items():
            call_count += 1
            print(f"[{call_count:02d}/{total_calls}] {bairro} — {category}...", end=" ", flush=True)
            try:
                results = search_nearby(types, lat, lng)
                for place in results:
                    rows.append(normalize(place, category, bairro))
                print(f"{len(results)} resultados")
            except requests.HTTPError as e:
                print(f"ERRO HTTP: {e}")
            except Exception as e:
                print(f"FALHA: {e}")
            time.sleep(0.35)   # pausa entre chamadas

    # ─── Limpeza ────────────────────────────────────────────────────────────
    df = pd.DataFrame(rows)

    if df.empty:
        print("\n❌ Nenhum dado retornado.")
        print("Verifique: API Key, billing ativado e 'Places API (New)' habilitada.")
        return

    # remove sem coordenadas ou nome
    df = df.dropna(subset=["name", "latitude", "longitude"])

    # deduplica pelo ID real do Google (aparece em bairros vizinhos)
    df = df.drop_duplicates(subset=["place_id"]).copy()

    # preenche avaliações ausentes com a média da categoria
    df["average_rating"] = df.groupby("category")["average_rating"].transform(
        lambda s: s.fillna(round(s.mean(), 1) if s.notna().any() else 4.0)
    )

    # ID sequencial
    df = df.drop(columns=["place_id"]).reset_index(drop=True)
    df.insert(0, "id", range(1, len(df) + 1))

    # ─── Salva CSV ──────────────────────────────────────────────────────────
    df.to_csv("places_recife_real.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV salvo: places_recife_real.csv")

    # ─── Resumo ─────────────────────────────────────────────────────────────
    print(f"\n{'─'*45}")
    print(f"  Total de lugares únicos : {len(df)}")
    print(f"  Com foto                : {df['photo_url'].notna().sum()}")
    print(f"  Sem foto                : {df['photo_url'].isna().sum()}")
    print(f"\n  Por categoria:")
    print(df["category"].value_counts().to_string())
    print(f"\n  Por bairro:")
    print(df["neighborhood"].value_counts().to_string())
    print(f"{'─'*45}")

    # ─── Grava no PostgreSQL ────────────────────────────────────────────────
    if not DATABASE_URL:
        print("\n⚠️  DATABASE_URL não encontrada — apenas CSV gerado.")
        return

    engine = create_engine(DATABASE_URL)
    df.to_sql("places", engine, if_exists="replace", index=False)
    print(f"\n✅ Tabela 'places' atualizada no PostgreSQL com {len(df)} registros.")
    print("   Reinicie o Streamlit para ver os novos dados (streamlit cache clear).")


if __name__ == "__main__":
    main()
