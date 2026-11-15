"""
Módulo de Otimização & Programação Dinâmica (Mochila 0/1 - Knapsack Problem)
Inclui:
  1. Eventos Dinâmicos de Mercado ("Twist" da Rodada que altera pesos/valores)
  2. Algoritmo de Programação Dinâmica (Ótimo Global O(N * W))
  3. Comparação com Algoritmo Guloso (Heurística de Custo-Benefício) para demonstrar armadilhas gulosas
  4. Geração de dicas táticas durante a rodada
"""

import random
from typing import Any, Dict, List


ROUND_TWISTS: List[Dict[str, str]] = [
    {
        "id": "metacritic_festival",
        "name": "🏆 Festival Aclamados pela Crítica",
        "rule": "Jogos com Metacritic >= 82 ganham +45 pts de valor, mas pesam +$1 de Taxa Premium na mochila!",
    },
    {
        "id": "flash_sale_frenzy",
        "name": "⚡ Frenesi de Super Descontos (80%+ OFF)",
        "rule": "Jogos com desconto real >= 80% na Steam recebem um bônus de +35% na pontuação do Mercador!",
    },
    {
        "id": "indie_boost",
        "name": "💎 Incentivo Indie (Caçador de Barganhas)",
        "rule": "Jogos leves (custo base até $5) recebem +35 pts extras! Cuidado para não subestimar os baratinhos.",
    },
    {
        "id": "guild_customs_tax",
        "name": "⚖️ Taxa Alfandegária da Guilda (AAA)",
        "rule": "Jogos de grande porte (Preço Normal >= $29.99) custam +$2 na mochila, mas rendem +40 pts extras!",
    },
]


def select_balanced_knapsack_games(
    candidates: List[Dict[str, Any]], budget: int, target_count: int = 10
) -> List[Dict[str, Any]]:
    """
    Seleciona e balanceia os 10 jogos da vitrine usando Amostragem Estratificada por Faixas (Tiers),
    garantindo que:
      1. Nenhum jogo sozinho custe mais que 65% do orçamento (evita jogos de $28 num orçamento de $30).
      2. A vitrine tenha um mix de jogos Leves (3), Médios (4) e Pesados (3).
      3. A soma dos custos dos 10 jogos fique sempre em torno de ~2.1x o orçamento,
         forçando o jogador a escolher cerca de 3 a 5 jogos por rodada.
    """
    if not candidates:
        return []

    pool = list(candidates)
    random.shuffle(pool)
    selected = pool[: min(target_count, len(pool))]

    # Distribuição estratificada de pesos na mochila proporcional ao orçamento (W)
    # 3 jogos Leves (12%-22% de W), 4 jogos Médios (25%-38% de W), 3 jogos Pesados (42%-62% de W)
    tier_ratios = [
        0.13, 0.17, 0.21,          # 3 Leves
        0.26, 0.30, 0.34, 0.38,    # 4 Médios
        0.44, 0.52, 0.60,          # 3 Pesados (máx 60% do orçamento)
    ]

    # Ordena os jogos sorteados pelo salePrice real da Steam para preservar a coerência relativa de preço
    selected.sort(key=lambda g: float(g["salePrice"]))

    balanced: List[Dict[str, Any]] = []
    for idx, game in enumerate(selected):
        item = dict(game)
        ratio = tier_ratios[idx] if idx < len(tier_ratios) else 0.30
        jitter = random.choice([-1, 0, 1])
        min_cost = max(2, int(round(budget * 0.10)))
        max_cost = max(min_cost + 2, int(round(budget * 0.65)))

        # Se o preço real na Steam já estiver bem distribuído, usa ele; caso contrário, ancora na faixa proporcional
        raw_cost = int(item["discreteCost"])
        target_tier_cost = max(min_cost, min(max_cost, int(round(budget * ratio)) + jitter))

        # Combina o preço real com a faixa estratificada para nunca permitir extremos quebrados
        if raw_cost < min_cost or raw_cost > max_cost:
            final_cost = target_tier_cost
        else:
            final_cost = int(round((raw_cost * 0.45) + (target_tier_cost * 0.55)))
            final_cost = max(min_cost, min(max_cost, final_cost))

        item["discreteCost"] = final_cost

        # Ajusta o Valor do Mercador proporcionalmente ao custo + qualidade (Metacritic + Desconto Steam)
        # com variação para criar disputas interessantes entre combinações
        metacritic_bonus = int(round((int(item["metacriticScore"]) - 60) * 1.3))
        savings_bonus = int(round(float(item["savingsPercent"]) * 0.35))
        item["merchantValue"] = max(
            25, int(round(final_cost * 11.5)) + metacritic_bonus + savings_bonus
        )
        balanced.append(item)

    # Embaralha a ordem de exibição na vitrine para não entregar os jogos ordenados por preço
    random.shuffle(balanced)
    return balanced


def apply_round_twist(
    games: List[Dict[str, Any]], twist_id: str = ""
) -> Dict[str, Any]:
    """
    Sorteia e aplica um modificador ("Twist" de mercado) nos 10 jogos da rodada,
    alterando custos discretos e/ou pontuações de valor e criando armadilhas para a intuição gulosa.
    """
    chosen_twist = next(
        (t for t in ROUND_TWISTS if t["id"] == twist_id),
        random.choice(ROUND_TWISTS),
    )
    tid = chosen_twist["id"]

    modified_games: List[Dict[str, Any]] = []
    affected_count = 0

    for g in games:
        item = dict(g)
        base_cost = int(item["discreteCost"])
        base_val = int(item["merchantValue"])
        twist_tag = ""

        if tid == "metacritic_festival" and int(item["metacriticScore"]) >= 82:
            item["discreteCost"] = base_cost + 1
            item["merchantValue"] = base_val + 45
            twist_tag = "🏆 Bônus Crítica (+45 pts, +$1 custo)"
            affected_count += 1

        elif tid == "flash_sale_frenzy" and float(item["savingsPercent"]) >= 80.0:
            bonus = int(round(base_val * 0.35))
            item["merchantValue"] = base_val + bonus
            twist_tag = f"⚡ Super Promo (+{bonus} pts)"
            affected_count += 1

        elif tid == "indie_boost" and base_cost <= 5:
            item["merchantValue"] = base_val + 35
            twist_tag = "💎 Bônus Barganha (+35 pts)"
            affected_count += 1

        elif tid == "guild_customs_tax" and float(item["normalPrice"]) >= 29.99:
            item["discreteCost"] = base_cost + 2
            item["merchantValue"] = base_val + 40
            twist_tag = "⚖️ Taxa AAA (+40 pts, +$2 custo)"
            affected_count += 1

        item["baseDiscreteCost"] = base_cost
        item["baseMerchantValue"] = base_val
        item["twistTag"] = twist_tag
        item["efficiencyRatio"] = round(
            item["merchantValue"] / max(1, item["discreteCost"]), 1
        )
        modified_games.append(item)

    return {
        "twist": {
            **chosen_twist,
            "affected_games_count": affected_count,
        },
        "games": modified_games,
    }


def _solve_greedy_baseline(
    games: List[Dict[str, Any]], budget: int
) -> Dict[str, Any]:
    """
    Simula a estratégia gulosa clássica (escolher sempre o jogo de maior razão Valor/Custo que cabe).
    Serve para mostrar quando a Programação Dinâmica supera a intuição humana/gulosa!
    """
    sorted_by_density = sorted(
        games,
        key=lambda g: (g["merchantValue"] / max(1, g["discreteCost"]), g["merchantValue"]),
        reverse=True,
    )
    rem = budget
    picked = []
    for g in sorted_by_density:
        c = int(g["discreteCost"])
        if c <= rem:
            picked.append(g)
            rem -= c

    greedy_score = sum(int(g["merchantValue"]) for g in picked)
    greedy_cost = sum(int(g["discreteCost"]) for g in picked)
    return {
        "greedy_score": greedy_score,
        "greedy_cost": greedy_cost,
        "greedy_titles": [g["title"] for g in picked],
    }


def solve_optimal_steam_bundle(
    games: List[Dict[str, Any]], budget: int
) -> Dict[str, Any]:
    """
    Resolve o Problema da Mochila 0/1 (0/1 Knapsack) via Programação Dinâmica:
      DP[i][w] = max(DP[i-1][w], DP[i-1][w - cost_i] + value_i)

    Para N = 10 jogos e orçamento W, reconstrói a Rota Ideal de Compras via backtracking
    e compara com a Heurística Gulosa.
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

    # Compara com a escolha gulosa para identificar se havia uma "Armadilha Gulosa" na rodada
    greedy_info = _solve_greedy_baseline(games, W)
    dp_advantage = max_merchant_value - greedy_info["greedy_score"]

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
                "level": "Dica 1 — Maior Eficiência (Pontos por Dólar)",
                "text": (
                    f"O jogo '{best_ratio_game['title']}' entrega {ratio} pts por cada $1 de custo na mochila "
                    f"(Custo: ${best_ratio_game['discreteCost']} | Valor: +{best_ratio_game['merchantValue']} pts)."
                ),
            }
        )

    if dp_advantage > 0:
        hints.append(
            {
                "level": "Dica 2 — Alerta de Armadilha Gulosa!",
                "text": (
                    f"Cuidado! Escolher apenas os jogos de maior custo-benefício isolado deixa dinheiro ocioso e rende "
                    f"{greedy_info['greedy_score']} pts, enquanto a Programação Dinâmica alcança {max_merchant_value} pts (+{dp_advantage} pts)!"
                ),
            }
        )
    elif optimal_games:
        anchor_game = max(optimal_games, key=lambda g: g["merchantValue"])
        hints.append(
            {
                "level": "Dica 2 — Peça-Chave da Solução Ótima",
                "text": (
                    f"Na tabela DP[{n}][{W}], a rota ideal inclui obrigatoriamente '{anchor_game['title']}' "
                    f"(Custo: ${anchor_game['discreteCost']} | +{anchor_game['merchantValue']} pts)."
                ),
            }
        )

    if optimal_games:
        hints.append(
            {
                "level": "Dica 3 — Estrutura da Mochila Perfeita",
                "text": (
                    f"A combinação ótima dos 10 jogos leva exatamente {len(optimal_games)} jogos, "
                    f"gastando ${total_discrete_cost} de ${W} e somando {max_merchant_value} pontos."
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
        "greedy_baseline": {
            **greedy_info,
            "dp_beats_greedy_by": dp_advantage,
        },
        "optimal_game_ids": [g["gameID"] for g in optimal_games],
        "optimal_games": optimal_games,
        "decision_steps": decision_steps,
        "hints": hints,
    }
