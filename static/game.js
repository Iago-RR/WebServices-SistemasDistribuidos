// Script básico de teste para consumir /api/round (10 jogos + Twist) e /api/checkout

let currentRound = {
  budget: 30,
  games: [],
  selectedIds: new Set(),
  hints: [],
  revealedHintsCount: 0,
};

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnNewRound").addEventListener("click", loadNewRound);
  document.getElementById("btnHint").addEventListener("click", revealNextHint);
  document.getElementById("btnCheckout").addEventListener("click", submitCheckout);

  loadNewRound();
});

async function loadNewRound() {
  const budget = parseInt(document.getElementById("budgetSelect").value, 10) || 30;
  const gamesGrid = document.getElementById("gamesGrid");
  document.getElementById("roundResultPanel").style.display = "none";
  gamesGrid.innerHTML = "Buscando 10 jogos da API REST e validando orçamento no SOAP...";

  try {
    const response = await fetch(`/api/round?budget=${budget}`);
    const data = await response.json();

    currentRound.budget = data.budget;
    currentRound.games = data.games || [];
    currentRound.selectedIds = new Set();
    currentRound.hints = (data.dp_optimization && data.dp_optimization.hints) || [];
    currentRound.revealedHintsCount = 0;

    document.getElementById("budgetAmount").textContent = `$${data.budget}`;
    document.getElementById("budgetWordsSoap").textContent = `"${data.budget_in_words_soap} dollars"`;
    document.getElementById("hintsList").innerHTML = "";
    document.getElementById("hintCounter").textContent = `0/${currentRound.hints.length}`;

    if (data.twist) {
      document.getElementById("twistName").textContent = data.twist.name;
      document.getElementById("twistRule").textContent =
        `${data.twist.rule} (${data.twist.affected_games_count} jogos afetados nesta rodada)`;
    }

    renderGamesTable();
    updateCartSummary();
    updateTelemetryPanel(data.telemetry);
  } catch (err) {
    gamesGrid.innerHTML = "Erro: " + err.message;
  }
}

function renderGamesTable() {
  const gamesGrid = document.getElementById("gamesGrid");
  let html = `<table border="1" cellpadding="5" cellspacing="0">
    <tr>
      <th>#</th>
      <th>Imagem</th>
      <th>Título</th>
      <th>Metacritic</th>
      <th>Desconto Steam</th>
      <th>Custo na Mochila</th>
      <th>Pontos (Valor)</th>
      <th>Modificador (Twist)</th>
      <th>Ação</th>
    </tr>`;

  currentRound.games.forEach((game, idx) => {
    const isSelected = currentRound.selectedIds.has(String(game.gameID));
    html += `
      <tr>
        <td>${idx + 1}</td>
        <td><img src="${game.thumb}" width="85" alt="${game.title}"></td>
        <td><b>${game.title}</b></td>
        <td>${game.metacriticScore}</td>
        <td>-${game.savingsPercent}% (De $${game.normalPrice.toFixed(2)} por $${game.salePrice.toFixed(2)})</td>
        <td><b>$${game.discreteCost}</b></td>
        <td><b>+${game.merchantValue} pts</b></td>
        <td>${game.twistTag || "—"}</td>
        <td>
          <button class="btn-select-game" data-game-id="${game.gameID}">
            ${isSelected ? "[X] Na Mochila (Remover)" : "[ ] Colocar na Mochila"}
          </button>
        </td>
      </tr>
    `;
  });

  html += `</table>`;
  gamesGrid.innerHTML = html;

  gamesGrid.querySelectorAll(".btn-select-game").forEach((btn) => {
    btn.addEventListener("click", () => toggleSelectGame(String(btn.dataset.gameId)));
  });
}

function toggleSelectGame(gameID) {
  if (currentRound.selectedIds.has(gameID)) {
    currentRound.selectedIds.delete(gameID);
  } else {
    currentRound.selectedIds.add(gameID);
  }
  renderGamesTable();
  updateCartSummary();
}

function updateCartSummary() {
  let totalCost = 0;
  let totalScore = 0;
  currentRound.games.forEach((g) => {
    if (currentRound.selectedIds.has(String(g.gameID))) {
      totalCost += g.discreteCost;
      totalScore += g.merchantValue;
    }
  });
  const costEl = document.getElementById("cartCost");
  costEl.textContent = `$${totalCost} / $${currentRound.budget}`;
  costEl.style.color = totalCost > currentRound.budget ? "red" : "black";
  document.getElementById("cartCount").textContent = `${currentRound.selectedIds.size} jogo(s)`;
  document.getElementById("cartScore").textContent = `${totalScore} pts`;
}

function revealNextHint() {
  if (currentRound.revealedHintsCount >= currentRound.hints.length) return;
  const hint = currentRound.hints[currentRound.revealedHintsCount];
  currentRound.revealedHintsCount += 1;
  const p = document.createElement("p");
  p.innerHTML = `<b>${hint.level}:</b> ${hint.text}`;
  document.getElementById("hintsList").appendChild(p);
  document.getElementById("hintCounter").textContent =
    `${currentRound.revealedHintsCount}/${currentRound.hints.length}`;
}

async function submitCheckout() {
  const response = await fetch("/api/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      budget: currentRound.budget,
      games: currentRound.games,
      selectedGameIds: Array.from(currentRound.selectedIds),
    }),
  });

  const data = await response.json();
  const receipt = data.soap_guild_receipt;
  document.getElementById("soapLatency").textContent = `${receipt.latency_ms} ms`;
  document.getElementById("soapBytes").textContent = `${receipt.payload_bytes} bytes`;
  document.getElementById("rawSoapXml").textContent = receipt.raw_payload;
  document.getElementById("rawSoapReq").textContent = receipt.raw_request;

  document.getElementById("soapReceiptNumeric").textContent = `$${receipt.amount_numeric.toFixed(2)}`;
  document.getElementById("soapReceiptWords").textContent = receipt.amount_in_dollars_words;
  document.getElementById("soapProximityWords").textContent = receipt.proximity_certification;
  document.getElementById("soapReceiptMeta").textContent =
    `Operações SOAP: ${receipt.operation} | Latência Total: ${receipt.latency_ms} ms`;

  const player = data.player;
  const dp = data.dp_optimization;
  const greedy = dp.greedy_baseline;

  document.getElementById("resPlayerScore").textContent = `${player.total_final_score} pts`;
  document.getElementById("resPlayerDetails").textContent =
    `Custo Mochila: $${player.discrete_cost} (Exato: $${player.exact_total.toFixed(2)})`;

  document.getElementById("resGreedyDetails").textContent =
    `${greedy.greedy_score} pts (Custo: $${greedy.greedy_cost}) — PD supera a escolha gulosa em +${greedy.dp_beats_greedy_by} pts`;

  document.getElementById("resOptimalScore").textContent = `${dp.max_merchant_value} pts`;
  document.getElementById("resOptimalDetails").textContent =
    `Custo Mochila: $${dp.total_discrete_cost} (Exato: $${dp.total_exact_price.toFixed(2)})`;

  document.getElementById("resEfficiency").textContent =
    `${player.proximity_label} (Faltaram ${player.points_missing} pts para o ótimo)`;
  document.getElementById("resComplexity").textContent = dp.complexity_time;

  document.getElementById("optimalRouteGames").textContent = dp.optimal_games
    .map((g) => `${g.title} ($${g.discreteCost} -> +${g.merchantValue} pts)`)
    .join(" | ");

  document.getElementById("dpStepsBody").innerHTML = dp.decision_steps
    .map(
      (s) => `<tr>
        <td>${s.step}</td>
        <td>${s.title}</td>
        <td>${s.action}</td>
        <td>$${s.cost}</td>
        <td>+${s.merchantValue}</td>
        <td>${s.reason}</td>
      </tr>`
    )
    .join("");

  document.getElementById("roundResultPanel").style.display = "block";
}

function updateTelemetryPanel(telemetry) {
  if (!telemetry) return;
  if (telemetry.rest) {
    document.getElementById("restLatency").textContent = `${telemetry.rest.latency_ms} ms`;
    document.getElementById("restBytes").textContent = `${telemetry.rest.payload_bytes} bytes`;
    document.getElementById("rawRestJson").textContent = telemetry.rest.raw_payload;
  }
  if (telemetry.soap) {
    document.getElementById("soapLatency").textContent = `${telemetry.soap.latency_ms} ms`;
    document.getElementById("soapBytes").textContent = `${telemetry.soap.payload_bytes} bytes`;
    document.getElementById("rawSoapXml").textContent = telemetry.soap.raw_payload;
    document.getElementById("rawSoapReq").textContent = telemetry.soap.raw_request;
  }
}
