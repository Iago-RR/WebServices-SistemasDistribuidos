"""
Servidor Principal — O Mercador da Steam (Steam Price Guesser & Knapsack Optimizer)
Integra:
  1. API REST Pública (CheapShark Steam Deals - JSON)
  2. Web Service SOAP Público (DataAccess NumberConversion - WSDL/XML)
  3. Otimizador de Programação Dinâmica (Mochila 0/1 - Rotas Ideais e Dicas)
"""

import random
from flask import Flask, jsonify, request, send_from_directory
from services.rest_client import fetch_steam_deals
from services.soap_client import (
    convert_amount_to_dollars_soap,
    convert_number_to_words_soap,
)
from services.optimizer import solve_optimal_steam_bundle

app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/round", methods=["GET"])
def create_round():
    """
    Inicia uma nova rodada do jogo:
    1. Consome a API REST (CheapShark) para buscar ofertas reais da Steam em JSON.
    2. Seleciona 6 jogos variados para a vitrine do Mercador.
    3. Executa o algoritmo de Programação Dinâmica (Mochila 0/1) para calcular a rota ótima e dicas.
    4. Consome o Web Service SOAP (NumberToWords) para registrar o orçamento oficial por extenso em XML.
    """
    try:
        requested_budget = request.args.get("budget", type=int)
        budget = requested_budget if requested_budget else random.choice([20, 25, 30, 35, 40])

        rest_data = fetch_steam_deals(
            page_size=28,
            upper_price=max(18, budget - 2),
            lower_price=1,
            min_metacritic=65,
        )

        available_games = [
            g for g in rest_data["games"] if 1 <= g["discreteCost"] <= budget - 2
        ]
        if len(available_games) < 6:
            available_games = rest_data["games"]

        round_games = random.sample(available_games, k=min(6, len(available_games)))

        # Calcula a solução ótima via Programação Dinâmica (Mochila 0/1)
        dp_solution = solve_optimal_steam_bundle(round_games, budget)

        # Consome o Web Service SOAP (WSDL) para converter o orçamento da rodada por extenso
        soap_budget_data = convert_number_to_words_soap(budget)

        return jsonify(
            {
                "status": "ok",
                "budget": budget,
                "budget_in_words_soap": soap_budget_data["result_text"],
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
    1. Avalia os palpites de preço (Steam Price Guesser) e a mochila escolhida pelo jogador.
    2. Consome o Web Service SOAP (NumberToDollars) para emitir o Cheque Oficial em XML.
    3. Compara o resultado do jogador com a Rota Ótima da Programação Dinâmica.
    """
    try:
        payload = request.get_json(force=True) or {}
        round_games = payload.get("games", [])
        selected_ids = set(str(gid) for gid in payload.get("selectedGameIds", []))
        price_guesses = payload.get("priceGuesses", {})
        budget = int(payload.get("budget", 30))

        chosen_games = [
            g for g in round_games if str(g.get("gameID")) in selected_ids
        ]

        player_discrete_cost = sum(int(g["discreteCost"]) for g in chosen_games)
        player_exact_total = round(sum(float(g["salePrice"]) for g in chosen_games), 2)
        player_merchant_score = sum(int(g["merchantValue"]) for g in chosen_games)

        # Avalia os palpites de preço (Price Guesser)
        guess_results = []
        guess_bonus_points = 0
        for game in round_games:
            gid = str(game.get("gameID"))
            actual_price = float(game.get("salePrice", 0.0))
            raw_guess = price_guesses.get(gid)
            if raw_guess is not None and str(raw_guess).strip() != "":
                try:
                    guessed_val = float(raw_guess)
                    diff = abs(actual_price - guessed_val)
                    accuracy_pct = max(
                        0.0, round((1.0 - (diff / max(actual_price, 5.0))) * 100, 1)
                    )
                    bonus = int(round(accuracy_pct * 0.25))
                    guess_bonus_points += bonus
                    guess_results.append(
                        {
                            "gameID": gid,
                            "title": game["title"],
                            "guessedPrice": round(guessed_val, 2),
                            "actualPrice": actual_price,
                            "diff": round(diff, 2),
                            "accuracyPercent": accuracy_pct,
                            "bonusPoints": bonus,
                        }
                    )
                except ValueError:
                    pass

        # recalcula solução ótima da Programação Dinâmica para comparação final
        dp_solution = solve_optimal_steam_bundle(round_games, budget)
        max_optimal_score = max(1, int(dp_solution["max_merchant_value"]))

        over_budget = player_discrete_cost > budget
        efficiency_pct = (
            0.0
            if over_budget
            else round((player_merchant_score / max_optimal_score) * 100, 1)
        )

        # Chama o Web Service SOAP (NumberToDollars) para emitir o cheque oficial da compra
        amount_for_soap = (
            player_exact_total
            if player_exact_total > 0
            else float(dp_solution["total_exact_price"])
        )
        soap_receipt = convert_amount_to_dollars_soap(amount_for_soap)

        return jsonify(
            {
                "status": "ok",
                "player": {
                    "chosen_games": chosen_games,
                    "discrete_cost": player_discrete_cost,
                    "exact_total": player_exact_total,
                    "over_budget": over_budget,
                    "merchant_score": player_merchant_score,
                    "guess_bonus_points": guess_bonus_points,
                    "total_final_score": (
                        0 if over_budget else player_merchant_score + guess_bonus_points
                    ),
                    "efficiency_vs_dp_percent": efficiency_pct,
                    "guess_results": guess_results,
                },
                "soap_guild_receipt": {
                    "amount_numeric": amount_for_soap,
                    "amount_in_dollars_words": soap_receipt["result_text"],
                    "operation": soap_receipt["operation"],
                    "wsdl_url": soap_receipt["wsdl_url"],
                    "latency_ms": soap_receipt["latency_ms"],
                    "payload_bytes": soap_receipt["payload_bytes"],
                    "raw_request": soap_receipt["raw_xml_request"],
                    "raw_payload": soap_receipt["raw_xml_response"],
                },
                "dp_optimization": dp_solution,
            }
        )
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


if __name__ == "__main__":
    print("=" * 72)
    print(" O MERCADOR DA STEAM - REST (JSON) + SOAP (WSDL/XML) + PROG. DINÂMICA")
    print(" Acesse no navegador: http://127.0.0.1:5000")
    print("=" * 72)
    app.run(host="127.0.0.1", port=5000, debug=True)
