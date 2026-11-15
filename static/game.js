// Script básico de teste para consumir /api/round e /api/checkout

let currentRound = {
  budget: 30,
  games: [],
  selectedIds: new Set(),
  hints: [],
  revealedHintsCount: 0,
  pricesRevealed: false,
};

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnNewRound").addEventListener("click", loadNewRound);
  document.getElementById("btnHint").addEventListener("click", revealNextHint);
  document.getElementById("btnTogglePrices").addEventListener("click", togglePricesVisibility);
  document.getElementById("btnCheckout").addEventListener("click", submitCheckout);

  loadNewRound();
});

async function loadNewRound() {
  const budget = parseInt(document.getElementById("budgetSelect").value, 10) || 30;
  const gamesGrid = document.getElementById("gamesGrid");
  document.getElementById("roundResultPanel").style.display = "none";
  gamesGrid.innerHTML = "Buscando dados da API REST e SOAP...";

  try {
    const response = await fetch(`/api/round?budget=${budget}`);
    const data = await response.json();

    currentRound.budget = data.budget;
    currentRound.games = data.games || [];
    currentRound.selectedIds = new Set();
    currentRound.hints = (data.dp_optimization && data.dp_optimization.hints) || [];
    currentRound.revealedHintsCount = 0;
    currentRound.pricesRevealed = false;

    document.getElementById("budgetAmount").textContent = `$${data.budget}`;
    document.getElementById("budgetWordsSoap").textContent = data.budget_in_words_soap;
    document.getElementById("hintsList").innerHTML = "";
    document.getElementById("hintCounter").textContent = `0/${currentRound.hints.length}`;

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
      <th>Imagem</th>
      <th>Título</th>
      <th>Metacritic</th>
      <th>Pontos</th>
      <th>Preço</th>
      <th>Chute ($)</th>
      <th>Ação</th>
    </tr>`;

  currentRound.games.forEach((game) => {
    const isSelected = currentRound.selectedIds.has(String(game.gameID));
    const priceText = currentRound.pricesRevealed
      ? `$${game.salePrice.toFixed(2)} (Custo: $${game.discreteCost})`
      : `Oculto (Normal: $${game.normalPrice.toFixed(2)})`;

    html += `
      <tr>
        <td><img src="${game.thumb}" width="90" alt="${game.title}"></td>
        <td>${game.title}</td>
        <td>${game.metacriticScore}</td>
        <td>+${game.merchantValue}</td>
        <td>${priceText}</td>
        <td><input type="number" step="0.01" class="price-guess-input" data-game-id="${game.gameID}" style="width:70px;"></td>
        <td>
          <button class="btn-select-game" data-game-id="${game.gameID}">
            ${isSelected ? "[X] Remover" : "[ ] Selecionar"}
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
  document.getElementById("cartCost").textContent = `$${totalCost} / $${currentRound.budget}`;
  document.getElementById("cartCount").textContent = `${currentRound.selectedIds.size} itens`;
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

function togglePricesVisibility() {
  currentRound.pricesRevealed = !currentRound.pricesRevealed;
  renderGamesTable();
}

async function submitCheckout() {
  const priceGuesses = {};
  document.querySelectorAll(".price-guess-input").forEach((input) => {
    if (input.value.trim() !== "") {
      priceGuesses[input.dataset.gameId] = input.value.trim();
    }
  });

  const response = await fetch("/api/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      budget: currentRound.budget,
      games: currentRound.games,
      selectedGameIds: Array.from(currentRound.selectedIds),
      priceGuesses,
    }),
  });

  const data = await response.json();
  currentRound.pricesRevealed = true;
  renderGamesTable();

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
  document.getElementById("resPlayerScore").textContent = `${player.total_final_score} pts`;
  document.getElementById("resPlayerDetails").textContent = `Mochila: ${player.merchant_score} pts | Gasto: $${player.exact_total.toFixed(2)}`;
  document.getElementById("resOptimalScore").textContent = `${dp.max_merchant_value} pts`;
  document.getElementById("resOptimalDetails").textContent = `Custo: $${dp.total_exact_price.toFixed(2)}`;
  document.getElementById("resEfficiency").textContent =
    `${player.proximity_label} (Faltaram ${player.points_missing} pts para o ótimo)`;
  document.getElementById("resComplexity").textContent = dp.complexity_time;

  document.getElementById("optimalRouteGames").textContent = dp.optimal_games
    .map((g) => `${g.title} ($${g.salePrice})`)
    .join(", ");

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
