"""
Módulo A: Cliente da Aplicação REST (Padrão JSON)
Consome a API pública CheapShark (Steam Deals API) sem necessidade de chave de autenticação.
Documentação Oficial: https://apidocs.cheapshark.com/
"""

import json
import random
import time
from typing import Any, Dict, List, Optional
import requests


CHEAPSHARK_BASE_URL = "https://www.cheapshark.com/api/1.0"
CHEAPSHARK_DOCS_URL = "https://apidocs.cheapshark.com/"

# Cache em memória (TTL de 5 minutos) + último resultado válido para proteger contra Rate Limit (HTTP 429)
_REST_CACHE: Dict[str, Dict[str, Any]] = {}
_LAST_SUCCESSFUL_REST_RESULT: Optional[Dict[str, Any]] = None
CACHE_TTL_SECONDS = 300


def fetch_steam_deals(
    page_size: int = 25,
    upper_price: int = 50,
    lower_price: int = 1,
    min_metacritic: int = 65,
    page_number: Optional[int] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Consulta ofertas reais de jogos da Steam na API REST pública CheapShark.
    Inclui cache em memória com TTL e fallback contra Rate Limiting (HTTP 429).
    """
    global _LAST_SUCCESSFUL_REST_RESULT
    if page_number is None:
        page_number = random.randint(0, 8)

    cache_key = f"{page_size}:{upper_price}:{lower_price}:{min_metacritic}:{page_number}"
    now = time.time()
    if use_cache and cache_key in _REST_CACHE:
        cached_entry = _REST_CACHE[cache_key]
        if now - cached_entry["timestamp"] < CACHE_TTL_SECONDS:
            return cached_entry["data"]

    params = {
        "storeID": "1",  # 1 = Steam
        "upperPrice": str(upper_price),
        "lowerPrice": str(lower_price),
        "metacritic": str(min_metacritic),
        "pageSize": str(page_size),
        "pageNumber": str(page_number),
        "onSale": "1",
    }

    endpoint = f"{CHEAPSHARK_BASE_URL}/deals"
    headers = {
        "Accept": "application/json",
        "User-Agent": "IFNMG-SistemasDistribuidos-WebServices/1.0",
    }

    start_time = time.perf_counter()
    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=12)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.raise_for_status()
    except Exception:
        if _LAST_SUCCESSFUL_REST_RESULT is not None:
            return _LAST_SUCCESSFUL_REST_RESULT
        raise

    raw_text = response.text
    payload_bytes = len(response.content)
    raw_items: List[Dict[str, Any]] = response.json()

    # Filtra jogos únicos por título para evitar edições duplicadas na mesma rodada
    seen_titles = set()
    cleaned_games = []
    for item in raw_items:
        title = item.get("title", "").strip()
        if not title or title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())

        sale_price = float(item.get("salePrice", 0.0))
        normal_price = float(item.get("normalPrice", sale_price))
        savings_pct = float(item.get("savings", 0.0))
        metacritic = int(item.get("metacriticScore") or 70)
        steam_rating = int(item.get("steamRatingPercent") or metacritic)
        deal_rating = float(item.get("dealRating") or 7.5)

        # Custo inteiro discretizado para a Mochila 0/1 (mínimo $1)
        discrete_cost = max(1, int(round(sale_price)))

        # Pontuação de valor para o Mercador (combina valor original + qualidade crítica + economia)
        merchant_score = int(
            round((normal_price * 2.2) + (metacritic * 0.6) + (savings_pct * 0.5))
        )

        cleaned_games.append(
            {
                "dealID": item.get("dealID"),
                "gameID": item.get("gameID"),
                "steamAppID": item.get("steamAppID"),
                "title": title,
                "salePrice": round(sale_price, 2),
                "normalPrice": round(normal_price, 2),
                "discreteCost": discrete_cost,
                "savingsPercent": round(savings_pct, 1),
                "metacriticScore": metacritic,
                "steamRatingPercent": steam_rating,
                "steamRatingText": item.get("steamRatingText") or "Positive",
                "dealRating": deal_rating,
                "thumb": item.get("thumb"),
                "merchantValue": merchant_score,
            }
        )

    # Exemplo real do JSON recebido (limitado aos 2 primeiros itens para exibição limpa no painel/relatório)
    sample_json_obj = raw_items[:2] if raw_items else []
    raw_json_sample = json.dumps(sample_json_obj, indent=2, ensure_ascii=False)

    result_payload = {
        "protocol": "REST",
        "format": "JSON",
        "endpoint": response.url,
        "documentation_url": CHEAPSHARK_DOCS_URL,
        "status_code": response.status_code,
        "latency_ms": elapsed_ms,
        "payload_bytes": payload_bytes,
        "total_items_returned": len(raw_items),
        "games": cleaned_games,
        "raw_json_sample": raw_json_sample,
        "raw_json_first_item": raw_items[0] if raw_items else {},
    }
    _REST_CACHE[cache_key] = {"timestamp": now, "data": result_payload}
    _LAST_SUCCESSFUL_REST_RESULT = result_payload
    return result_payload


if __name__ == "__main__":
    print("=" * 70)
    print("TESTE ISOLADO - APLICAÇÃO REST (CheapShark Steam Deals API - JSON)")
    print("=" * 70)
    result = fetch_steam_deals(page_size=6, page_number=0)
    print(f"URL Requisitada : {result['endpoint']}")
    print(f"Status HTTP     : {result['status_code']}")
    print(f"Latência (ms)   : {result['latency_ms']} ms")
    print(f"Tamanho Payload : {result['payload_bytes']} bytes")
    print("\nJogos obtidos:")
    for idx, g in enumerate(result["games"][:5], start=1):
        print(
            f"  {idx}. {g['title']} | Promo: ${g['salePrice']:.2f} "
            f"(Normal: ${g['normalPrice']:.2f}, -{g['savingsPercent']}%) "
            f"| Metacritic: {g['metacriticScore']} | Score Mercador: {g['merchantValue']}"
        )
    print("\nExemplo Real do Texto JSON Recebido (1º item):")
    print(json.dumps(result["raw_json_first_item"], indent=2, ensure_ascii=False))
