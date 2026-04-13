import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY não encontrada no arquivo .env")

URL = "https://places.googleapis.com/v1/places:searchNearby"

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    # Pedir só o necessário para reduzir custo
    "X-Goog-FieldMask": ",".join([
        "places.displayName",
        "places.location",
        "places.rating",
        "places.priceLevel",
        "places.primaryType",
        "places.types",
        "places.formattedAddress"
    ])
}

# Centro de Recife
RECIFE_LAT = -8.0476
RECIFE_LNG = -34.8770
RADIUS_METERS = 5000

# Tipos válidos da Places API (New)
PLACE_TYPES = ["restaurant"]

# Mapeamento para o modelo do seu projeto
CATEGORY_MAP = {
    "restaurant": ("gastronomia", "restaurant"),
    "cafe": ("gastronomia", "cafe"),
    "bar": ("gastronomia", "bar"),
    "park": ("lazer", "park"),
    "museum": ("cultura", "museum"),
    "tourist_attraction": ("cultura", "tourist_attraction"),
}

PRICE_MAP = {
    "PRICE_LEVEL_FREE": 1,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 3,
}

def search_nearby(place_type: str) -> list[dict]:
    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": RECIFE_LAT,
                    "longitude": RECIFE_LNG
                },
                "radius": RADIUS_METERS
            }
        }
    }

    response = requests.post(URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json().get("places", [])

def normalize_place(place: dict, requested_type: str) -> dict:
    display_name = place.get("displayName", {}).get("text")
    location = place.get("location", {})
    rating = place.get("rating")
    price_level_raw = place.get("priceLevel")
    primary_type = place.get("primaryType", requested_type)
    formatted_address = place.get("formattedAddress", "")

    category, default_subcategory = CATEGORY_MAP.get(
        requested_type, ("outros", requested_type)
    )

    subcategory = primary_type or default_subcategory

    # Bairro simples por enquanto: Recife
    # Depois dá para enriquecer usando formattedAddress
    neighborhood = "Recife"

    return {
        "name": display_name,
        "category": category,
        "subcategory": subcategory,
        "neighborhood": neighborhood,
        "average_price_level": PRICE_MAP.get(price_level_raw, 2),
        "average_rating": rating if rating is not None else None,
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "source_type": requested_type,
        "formatted_address": formatted_address,
    }

def main() -> None:
    rows: list[dict] = []

    for place_type in PLACE_TYPES:
        print(f"Buscando tipo: {place_type}")
        try:
            results = search_nearby(place_type)
            for place in results:
                rows.append(normalize_place(place, place_type))
            time.sleep(1)  # leve pausa para evitar chamadas em rajada
        except requests.HTTPError as e:
            print(f"Erro ao buscar {place_type}: {e}")
        except Exception as e:
            print(f"Falha inesperada em {place_type}: {e}")

    
    df = pd.DataFrame(rows)

# ===============================
# VALIDAÇÃO DEFENSIVA (NOVO)
# ===============================

    if df.empty:
        print("❌ Nenhum dado foi retornado pela API.")
        print("👉 Verifique: API Key, billing, restrições e APIs habilitadas.")
        return

    required_columns = [
        "name",
        "category",
        "subcategory",
        "neighborhood",
        "average_price_level",
        "average_rating",
        "latitude",
        "longitude",
]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
       print(f"❌ Colunas ausentes no DataFrame: {missing}")
       print("👉 A API provavelmente falhou (ex: erro 403).")
       return

# ===============================
# LIMPEZA (AGORA SEGURA)
# ===============================

    df = df.dropna(subset=["name", "latitude", "longitude", "average_rating"])
    df = df.drop_duplicates(subset=["name", "latitude", "longitude"]).copy()

    # Mantém só colunas compatíveis com sua tabela atual
    df_final = df[
        [
            "name",
            "category",
            "subcategory",
            "neighborhood",
            "average_price_level",
            "average_rating",
            "latitude",
            "longitude",
        ]
    ].copy()

    output_file = "places_recife_real.csv"
    df_final.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"\nColeta concluída. Arquivo salvo em: {output_file}")
    print(f"Total de registros: {len(df_final)}")
    print(df_final.head())

if __name__ == "__main__":
    main()