"""
Servidor Principal — O Mercador da Steam (Desafio da Mochila 0/1 + Eventos de Mercado)
Integra:
  1. API REST Pública (CheapShark Steam Deals - JSON) -> Vitrine com 10 jogos reais
  2. Web Service SOAP Público (DataAccess NumberConversion - WSDL/XML) -> Cheque + Proximidade
  3. Otimizador de Programação Dinâmica (Mochila 0/1, Eventos de Mercado e Comparação Gulosa)
"""

import random
from flask import Flask, jsonify, request, send_from_directory
from services.rest_client import fetch_steam_deals
from services.soap_client import (
    certify_knapsack_proximity_soap,
    convert_amount_to_dollars_soap,
    convert_number_to_words_soap,
)
from services.optimizer import apply_round_twist, solve_optimal_steam_bundle

app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/round", methods=["GET"])
def create_round():
    """
    Inicia uma nova rodada do jogo:
    1. Consome a API REST (CheapShark) para buscar ofertas reais da Steam em JSON.
    2. Seleciona 10 jogos variados para a vitrine do Mercador.
    3. Sorteia e aplica um "Twist" (Evento de Mercado da Rodada) que altera pesos/valores.
    4. Executa o algoritmo de Programação Dinâmica (Mochila 0/1) para calcular a rota ótima e dicas.
    5. Consome o Web Service SOAP (NumberToWords) para registrar o orçamento oficial por extenso em XML.
    """
    try:
        requested_budget = request.args.get("budget", type=int)
        budget = requested_budget if requested_budget else random.choice([20, 25, 30, 35, 40])

        rest_data = fetch_steam_deals(
            page_size=40,
            upper_price=max(18, budget - 2),
            lower_price=1,
            min_metacritic=65,
        )

        available_games = [
            g for g in rest_data["games"] if 1 <= g["discreteCost"] <= budget - 2
        ]
        if len(available_games) < 10:
            available_games = rest_data["games"]

        sampled_games = random.sample(available_games, k=min(10, len(available_games)))

        # Aplica o "Twist" (Evento de Mercado da Rodada) nos 10 jogos
        twist_result = apply_round_twist(sampled_games)
        round_games = twist_result["games"]
        round_twist = twist_result["twist"]

        # Calcula a solução ótima via Programação Dinâmica (Mochila 0/1)
        dp_solution = solve_optimal_steam_bundle(round_games, budget)

        # Consome o Web Service SOAP (WSDL) para converter o orçamento da rodada por extenso
        soap_budget_data = convert_number_to_words_soap(budget)

        return jsonify(
            {
                "status": "ok",
                "budget": budget,
                "budget_in_words_soap": soap_budget_data["result_text"],
                "twist": round_twist,
                "games": round_games,
                "dp_optimization": dp_solution,
                "telemetry": {
                    "rest": {
                        "protocol": rest_data["protocol"],
                        "format": rest_data["format"],
                        "endpoint": rest_data["endpoint"],
                        "documentation_url": rest_data["documentation_url"],
                        "latency_ms": rest_data["latency_ms"],
                        "payload_bytes": rest_data["payload_bytes"],
                        "raw_payload": rest_data["raw_json_sample"],
                    },
                    "soap": {
                        "protocol": soap_budget_data["protocol"],
                        "format": soap_budget_data["format"],
                        "wsdl_url": soap_budget_data["wsdl_url"],
                        "documentation_url": soap_budget_data["documentation_url"],
                        "operation": soap_budget_data["operation"],
                        "latency_ms": soap_budget_data["latency_ms"],
                        "payload_bytes": soap_budget_data["payload_bytes"],
                        "raw_request": soap_budget_data["raw_xml_request"],
                        "raw_payload": soap_budget_data["raw_xml_response"],
                    },
                },
            }
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/checkout", methods=["POST"])
def checkout_round():
    """
    Finaliza a rodada do jogador:
    1. Avalia a mochila escolhida pelo jogador entre os 10 jogos disponíveis.
    2. Consome o Web Service SOAP (NumberToDollars + NumberToWords) para emitir o Cheque Oficial
       e certificar a porcentagem de proximidade da solução ótima em XML.
    3. Compara o resultado do jogador com a Heurística Gulosa e com o Ótimo da Programação Dinâmica.
    """
    try:
        payload = request.get_json(force=True) or {}
        round_games = payload.get("games", [])
        selected_ids = set(str(gid) for gid in payload.get("selectedGameIds", []))
        budget = int(payload.get("budget", 30))

        chosen_games = [
            g for g in round_games if str(g.get("gameID")) in selected_ids
        ]

        player_discrete_cost = sum(int(g["discreteCost"]) for g in chosen_games)
        player_exact_total = round(sum(float(g["salePrice"]) for g in chosen_games), 2)
        player_merchant_score = sum(int(g["merchantValue"]) for g in chosen_games)

        # Recalcula solução ótima da Programação Dinâmica para comparação final
        dp_solution = solve_optimal_steam_bundle(round_games, budget)
        max_optimal_score = max(1, int(dp_solution["max_merchant_value"]))
        greedy_score = int(dp_solution["greedy_baseline"]["greedy_score"])

        over_budget = player_discrete_cost > budget
        efficiency_pct = (
            0.0
            if over_budget
            else round((player_merchant_score / max_optimal_score) * 100, 1)
        )
        points_missing = max(0, max_optimal_score - player_merchant_score)
        beat_greedy = (not over_budget) and (player_merchant_score > greedy_score)

        if over_budget:
            proximity_label = "0% — Orçamento Estourado (Mochila Inválida)"
        elif efficiency_pct >= 100.0:
            proximity_label = "100% — Solução Ideal Exata (Ótimo Global da Mochila 0/1!)"
        elif efficiency_pct >= 85.0:
            proximity_label = f"{efficiency_pct}% de proximidade — Excelente (Muito próximo da Rota Ideal!)"
        elif efficiency_pct >= 65.0:
            proximity_label = f"{efficiency_pct}% de proximidade — Rota Intermediária (Sub-ótima)"
        else:
            proximity_label = f"{efficiency_pct}% de proximidade — Distante da Solução Ideal"

        # 1) Chama o Web Service SOAP (NumberToDollars) para emitir o cheque oficial da compra
        amount_for_soap = (
            player_exact_total
            if player_exact_total > 0
            else float(dp_solution["total_exact_price"])
        )
        soap_receipt = convert_amount_to_dollars_soap(amount_for_soap)

        # 2) Chama o Web Service SOAP (NumberToWords) para certificar por extenso a % de proximidade da Mochila 0/1
        soap_proximity = certify_knapsack_proximity_soap(efficiency_pct)

        combined_soap_request = (
            f"<!-- 1. Requisição SOAP: NumberToDollars (${amount_for_soap:.2f}) -->\n"
            f"{soap_receipt['raw_xml_request']}\n\n"
            f"<!-- 2. Requisição SOAP: NumberToWords (Proximidade da Mochila: {soap_proximity['proximity_rounded']}%) -->\n"
            f"{soap_proximity['raw_xml_request']}"
        )
        combined_soap_response = (
            f"<!-- 1. Resposta SOAP: NumberToDollars (${amount_for_soap:.2f}) -->\n"
            f"{soap_receipt['raw_xml_response']}\n\n"
            f"<!-- 2. Resposta SOAP: NumberToWords (Proximidade da Mochila: {soap_proximity['proximity_rounded']}%) -->\n"
            f"{soap_proximity['raw_xml_response']}"
        )
        total_soap_latency = round(
            soap_receipt["latency_ms"] + soap_proximity["latency_ms"], 2
        )
        total_soap_bytes = (
            soap_receipt["payload_bytes"] + soap_proximity["payload_bytes"]
        )

        return jsonify(
            {
                "status": "ok",
                "player": {
                    "chosen_games": chosen_games,
                    "discrete_cost": player_discrete_cost,
                    "exact_total": player_exact_total,
                    "over_budget": over_budget,
                    "merchant_score": player_merchant_score,
                    "total_final_score": 0 if over_budget else player_merchant_score,
                    "efficiency_vs_dp_percent": efficiency_pct,
                    "proximity_label": proximity_label,
                    "points_missing": points_missing,
                    "beat_greedy": beat_greedy,
                },
                "soap_guild_receipt": {
                    "amount_numeric": amount_for_soap,
                    "amount_in_dollars_words": soap_receipt["result_text"],
                    "proximity_percent": efficiency_pct,
                    "proximity_in_words_soap": soap_proximity["proximity_in_words"],
                    "proximity_certification": soap_proximity["certification_text"],
                    "operation": "NumberToDollars + NumberToWords (Proximidade PD)",
                    "wsdl_url": soap_receipt["wsdl_url"],
                    "latency_ms": total_soap_latency,
                    "payload_bytes": total_soap_bytes,
                    "raw_request": combined_soap_request,
                    "raw_payload": combined_soap_response,
                },
                "dp_optimization": dp_solution,
            }
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    print("=" * 72)
    print(" O MERCADOR DA STEAM - REST (JSON) + SOAP (WSDL/XML) + MOCHILA 0/1 (10 JOGOS)")
    print(" Acesse no navegador: http://127.0.0.1:5000")
    print("=" * 72)
    app.run(host="127.0.0.1", port=5000, debug=True)
