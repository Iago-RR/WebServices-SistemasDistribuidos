"""
Módulo de Otimização & Programação Dinâmica (Mochila 0/1 - Knapsack Problem)
Calcula a rota ótima de compras do Mercador da Steam para um orçamento finito (Budget)
e gera dicas táticas durante a rodada comparando a escolha gulosa com a solução ótima.
"""

from typing import Any, Dict, List


def solve_optimal_steam_bundle(
    games: List[Dict[str, Any]], budget: int
) -> Dict[str, Any]:
    """
    Resolve o Problema da Mochila 0/1 (0/1 Knapsack) via Programação Dinâmica:
      DP[i][w] = max(DP[i-1][w], DP[i-1][w - cost_i] + value_i)

    Parâmetros:
      - games: lista de jogos da rodada (cada um com 'discreteCost' e 'merchantValue')
      - budget: orçamento inteiro da rodada em dólares (ex: $25)

    Retorna:
      - optimal_games: subconjunto ótimo de jogos que maximiza o Score do Mercador
      - max_merchant_value: valor máximo atingível
      - total_discrete_cost: custo inteiro consumido pela rota ótima
      - total_exact_price: soma exata em dólares (salePrice) dos jogos da rota ótima
      - total_normal_value: soma dos preços originais sem desconto
      - decision_steps: trilha passo a passo das decisões da Programação Dinâmica
      - hints: dicas progressivas para o jogador durante a rodada
    """
    n = len(games)
    W = max(1, int(budget))

    # Tabela DP (n + 1) x (W + 1)
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        game = games[i - 1]
        cost = int(game["discreteCost"])
        val = int(game["merchantValue"])

        for w in range(W + 1):
            if cost <= w:
                include_val = dp[i - 1][w - cost] + val
                exclude_val = dp[i - 1][w]
                dp[i][w] = max(include_val, exclude_val)
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtracking na tabela DP para reconstruir a Rota Ótima de Compras
    optimal_games: List[Dict[str, Any]] = []
    decision_steps: List[Dict[str, Any]] = []
    w_rem = W

    for i in range(n, 0, -1):
        game = games[i - 1]
        cost = int(game["discreteCost"])
        val = int(game["merchantValue"])

        if dp[i][w_rem] != dp[i - 1][w_rem]:
            optimal_games.append(game)
            decision_steps.append(
                {
                    "step": len(decision_steps) + 1,
                    "action": "INCLUÍDO NA ROTA ÓTIMA",
                    "title": game["title"],
                    "cost": cost,
                    "exactPrice": game["salePrice"],
                    "merchantValue": val,
                    "budgetBefore": w_rem,
                    "budgetAfter": w_rem - cost,
                    "reason": (
                        f"DP[{i}][{w_rem}] ({dp[i][w_rem]}) > DP[{i-1}][{w_rem}] ({dp[i-1][w_rem]}): "
                        f"ganho líquido de +{val} pts por ${cost}."
                    ),
                }
            )
            w_rem -= cost
        else:
            decision_steps.append(
                {
                    "step": len(decision_steps) + 1,
                    "action": "DESCARTADO PELA PD",
                    "title": game["title"],
                    "cost": cost,
                    "exactPrice": game["salePrice"],
                    "merchantValue": val,
                    "budgetBefore": w_rem,
                    "budgetAfter": w_rem,
                    "reason": (
                        f"Custo (${cost}) excede orçamento restante (${w_rem}) ou combinação alternativa rende mais pontos."
                    ),
                }
            )

    optimal_games.reverse()
    decision_steps.reverse()

    total_discrete_cost = sum(int(g["discreteCost"]) for g in optimal_games)
    total_exact_price = round(sum(float(g["salePrice"]) for g in optimal_games), 2)
    total_normal_value = round(sum(float(g["normalPrice"]) for g in optimal_games), 2)
    max_merchant_value = dp[n][W]

    # Análise de Densidade (Valor / Custo) para gerar dicas inteligentes na rodada
    ranked_by_ratio = sorted(
        games,
        key=lambda g: g["merchantValue"] / max(1, g["discreteCost"]),
        reverse=True,
    )

    hints: List[Dict[str, str]] = []
    if ranked_by_ratio:
        best_ratio_game = ranked_by_ratio[0]
        ratio = round(
            best_ratio_game["merchantValue"] / max(1, best_ratio_game["discreteCost"]),
            1,
        )
        hints.append(
            {
                "level": "Dica 1 — Heurística de Densidade (Valor/Custo)",
                "text": (
                    f"O jogo '{best_ratio_game['title']}' possui a maior eficiência marginal da vitrine "
                    f"({ratio} pts por dólar, Metacritic {best_ratio_game['metacriticScore']})."
                ),
            }
        )

    if optimal_games:
        anchor_game = max(optimal_games, key=lambda g: g["merchantValue"])
        hints.append(
            {
                "level": "Dica 2 — Subproblema da Programação Dinâmica",
                "text": (
                    f"Na tabela DP[{n}][{W}], a rota ótima inclui '{anchor_game['title']}' "
                    f"(custo aproximado de ${anchor_game['discreteCost']} e +{anchor_game['merchantValue']} pts de valor)."
                ),
            }
        )

        hints.append(
            {
                "level": "Dica 3 — Estrutura da Cesta Ideal",
                "text": (
                    f"A solução ótima seleciona exatamente {len(optimal_games)} jogo(s), "
                    f"consumindo ${total_discrete_cost} de ${W} disponíveis e alcançando {max_merchant_value} pontos."
                ),
            }
        )

    return {
        "algorithm": "Programação Dinâmica — Mochila 0/1 (0/1 Knapsack)",
        "complexity_time": f"O(N * W) = O({n} * {W}) = {n * W} estados avaliados",
        "complexity_space": f"O(N * W) com matriz {n + 1}x{W + 1}",
        "budget": W,
        "max_merchant_value": max_merchant_value,
        "total_discrete_cost": total_discrete_cost,
        "total_exact_price": total_exact_price,
        "total_normal_value": total_normal_value,
        "total_savings": round(total_normal_value - total_exact_price, 2),
        "optimal_game_ids": [g["gameID"] for g in optimal_games],
        "optimal_games": optimal_games,
        "decision_steps": decision_steps,
        "hints": hints,
    }
