/**
 * Frontend Pastel + Liquid Glass Iridescente + Glitch RGB (Identidade Visual do Slide)
 * Foco central nos 10 jogos da Mochila 0/1.
 */

let currentRound = {
  budget: 30,
  games: [],
  selectedIds: new Set(),
  hints: [],
  revealedHintsCount: 0,
};

document.addEventListener("DOMContentLoaded", () => {
  const btnNewRound = document.getElementById("btnNewRound");
  const btnHint = document.getElementById("btnHint");
  const btnCheckout = document.getElementById("btnCheckout");
  const btnToggleInspector = document.getElementById("btnToggleInspector");
  const budgetSelect = document.getElementById("budgetSelect");

  btnNewRound.addEventListener("click", loadNewRound);
  budgetSelect.addEventListener("change", loadNewRound);
  btnHint.addEventListener("click", revealNextHint);
  btnCheckout.addEventListener("click", submitCheckout);

  // Gaveta retrátil do Raio-X (REST vs SOAP)
  btnToggleInspector.addEventListener("click", () => {
    const body = document.getElementById("inspectorBody");
    const arrow = document.getElementById("drawerArrow");
    const isHidden = body.classList.toggle("hidden");
    arrow.textContent = isHidden ? "▼" : "▲";
  });

  // Abas do Inspetor
  document.querySelectorAll(".tab-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-pill").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".raw-viewer").forEach((v) => v.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  // Movimento suave da gota de Liquid Glass conforme o mouse
  const droplet = document.getElementById("liquidDroplet");
  if (droplet) {
    window.addEventListener("mousemove", (e) => {
      const x = (e.clientX / window.innerWidth - 0.5) * 24;
      const y = (e.clientY / window.innerHeight - 0.5) * 24;
      droplet.style.transform = `translate(${x}px, ${y}px)`;
    });
  }

  loadNewRound();
});

async function loadNewRound() {
  const budgetSelect = document.getElementById("budgetSelect");
  const budget = parseInt(budgetSelect.value, 10) || 30;
  const gamesGrid = document.getElementById("gamesGrid");
  const resultPanel = document.getElementById("roundResultPanel");

  resultPanel.classList.add("hidden");
  gamesGrid.innerHTML = `<div class="liquid-glass loading-state">Carregando 10 jogos...</div>`;

  try {
    const response = await fetch(`/api/round?budget=${budget}`);
    const data = await response.json();

    if (data.status !== "ok") {
      throw new Error(data.message || "Falha ao carregar rodada.");
    }

    currentRound.budget = data.budget;
    currentRound.games = data.games || [];
    currentRound.selectedIds = new Set();
    currentRound.hints = (data.dp_optimization && data.dp_optimization.hints) || [];
    currentRound.revealedHintsCount = 0;

    document.getElementById("hintsList").innerHTML = "";
    document.getElementById("hintCounter").textContent = `0/${currentRound.hints.length}`;

    if (data.twist) {
      const cleanName = data.twist.name.replace(/^[^\wÀ-ÿ]+\s*/, "");
      document.getElementById("twistName").textContent = cleanName;
      document.getElementById("twistRule").textContent = `— ${data.twist.rule}`;
    }

    renderGamesGrid();
    updateCartSummary();
    updateTelemetryPanel(data.telemetry);
  } catch (err) {
    gamesGrid.innerHTML = `<div class="liquid-glass loading-state">Erro: ${err.message}</div>`;
  }
}

function renderGamesGrid() {
  const gamesGrid = document.getElementById("gamesGrid");
  gamesGrid.innerHTML = "";

  currentRound.games.forEach((game) => {
    const isSelected = currentRound.selectedIds.has(String(game.gameID));
    const card = document.createElement("div");
    card.className = `game-card ${isSelected ? "selected" : ""}`;

    const cleanTwist = game.twistTag
      ? game.twistTag.replace(/^[^\wÀ-ÿ]+\s*/, "")
      : "";
    const twistBadge = cleanTwist
      ? `<div class="twist-chip">${cleanTwist}</div>`
      : "";

    card.innerHTML = `
      <div class="game-thumb-wrap">
        <img src="${game.thumb}" alt="${game.title}" />
        <span class="meta-pill">MC ${game.metacriticScore}</span>
        <span class="score-pill">+${game.merchantValue} pts</span>
      </div>
      <div class="game-body">
        <div class="game-title">${game.title}</div>
        ${twistBadge}
        <div class="game-stats">
          <span>-$${game.savingsPercent}% ($${game.salePrice.toFixed(2)})</span>
          <span class="weight-label">Peso: $${game.discreteCost}</span>
        </div>
        <button class="btn-select-game" data-game-id="${game.gameID}">
          ${isSelected ? "Na Mochila · Remover" : "Adicionar ($" + game.discreteCost + ")"}
        </button>
      </div>
    `;

    const selectBtn = card.querySelector(".btn-select-game");
    selectBtn.addEventListener("click", () => toggleSelectGame(String(game.gameID)));

    gamesGrid.appendChild(card);
  });
}

function toggleSelectGame(gameID) {
  if (currentRound.selectedIds.has(gameID)) {
    currentRound.selectedIds.delete(gameID);
  } else {
    currentRound.selectedIds.add(gameID);
  }
  renderGamesGrid();
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
  costEl.style.color = totalCost > currentRound.budget ? "#ff1e8e" : "#232d65";

  document.getElementById("cartCount").textContent = `${currentRound.selectedIds.size}/10`;
  document.getElementById("cartScore").textContent = `${totalScore} pts`;
}

function revealNextHint() {
  if (currentRound.revealedHintsCount >= currentRound.hints.length) return;
  const hint = currentRound.hints[currentRound.revealedHintsCount];
  currentRound.revealedHintsCount += 1;

  const hintsList = document.getElementById("hintsList");
  const item = document.createElement("div");
  item.className = "hint-item";
  item.innerHTML = `<strong>${hint.level}:</strong> ${hint.text}`;
  hintsList.appendChild(item);

  document.getElementById("hintCounter").textContent =
    `${currentRound.revealedHintsCount}/${currentRound.hints.length}`;
}

async function submitCheckout() {
  try {
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
    if (data.status !== "ok") {
      throw new Error(data.message || "Erro ao finalizar rodada.");
    }

    const receipt = data.soap_guild_receipt;
    document.getElementById("soapLatency").textContent = `${receipt.latency_ms} ms`;
    document.getElementById("soapBytes").textContent = `${receipt.payload_bytes} bytes`;
    document.getElementById("rawSoapXml").textContent = receipt.raw_payload;
    document.getElementById("rawSoapReq").textContent = receipt.raw_request;

    document.getElementById("soapReceiptNumeric").textContent =
      `$${receipt.amount_numeric.toFixed(2)} USD`;
    document.getElementById("soapReceiptWords").textContent =
      `"${receipt.amount_in_dollars_words}"`;
    const proxEl = document.getElementById("soapProximityWords");
    if (proxEl) {
      proxEl.textContent = receipt.proximity_certification;
    }
    document.getElementById("soapReceiptMeta").textContent =
      `${receipt.latency_ms} ms · ${receipt.payload_bytes} bytes`;

    const player = data.player;
    const dp = data.dp_optimization;
    const greedy = dp.greedy_baseline;

    document.getElementById("resPlayerScore").textContent =
      player.over_budget
        ? `Excedeu ($${player.discrete_cost} > $${currentRound.budget})`
        : `${player.total_final_score} pts`;

    document.getElementById("resPlayerDetails").textContent =
      `Peso: $${player.discrete_cost} ($${player.exact_total.toFixed(2)}) · Guloso: ${greedy.greedy_score} pts`;

    document.getElementById("resOptimalScore").textContent = `${dp.max_merchant_value} pts`;
    document.getElementById("resOptimalDetails").textContent =
      `Peso: $${dp.total_discrete_cost} ($${dp.total_exact_price.toFixed(2)}) · +${greedy.dp_beats_greedy_by} pts sobre Guloso`;

    document.getElementById("resEfficiency").textContent = `${player.efficiency_vs_dp_percent}%`;
    document.getElementById("resComplexity").textContent = player.proximity_label;

    const badgesContainer = document.getElementById("optimalRouteGames");
    badgesContainer.innerHTML = dp.optimal_games
      .map(
        (g) =>
          `<span class="opt-badge">${g.title} ($${g.discreteCost} · +${g.merchantValue} pts)</span>`
      )
      .join("");

    const tbody = document.getElementById("dpStepsBody");
    tbody.innerHTML = dp.decision_steps
      .map(
        (step) => `
        <tr>
          <td>${step.step}</td>
          <td><strong>${step.title}</strong></td>
          <td style="color: ${step.action.includes("Entrou") ? "#232d65" : "rgba(35,45,101,0.45)"}; font-weight:800;">
            ${step.action}
          </td>
          <td>$${step.cost} ($${step.exactPrice.toFixed(2)})</td>
          <td>+${step.merchantValue} pts</td>
          <td>${step.reason}</td>
        </tr>
      `
      )
      .join("");

    const resultPanel = document.getElementById("roundResultPanel");
    resultPanel.classList.remove("hidden");
    resultPanel.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    alert("Erro ao finalizar a compra: " + err.message);
  }
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
