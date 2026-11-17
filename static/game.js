/**
 * Motor Óptico <lg-lens> (refraction=17, bezel=0.6, curvature=7, chroma=0.4, blur=0, specular=0.5)
 * Gera mapas de deslocamento (R,G bend + B highlight) via SDF e aplica via SVG backdrop-filter.
 */

const LG_CONFIG = {
  refraction: 17,
  bezel: 0.6,
  curvature: 7,
  chroma: 0.4,
  blur: 0,
  specular: 0.5,
};

let currentRound = {
  budget: 30,
  games: [],
  selectedIds: new Set(),
  hints: [],
  revealedHintsCount: 0,
};

const generatedFilters = new Map();

/**
 * Constrói o Displacement Map R,G (curvatura de borda) + B (specular highlight)
 * idêntico ao algoritmo do <lg-lens> (liquidglass.dev).
 */
function createLgLensDisplacementFilter(width, height, radius, config = LG_CONFIG) {
  const w = Math.max(40, Math.round(width));
  const h = Math.max(40, Math.round(height));
  const r = Math.min(Math.round(radius), Math.floor(Math.min(w, h) / 2));
  const key = `lg-${w}-${h}-${r}`;

  if (generatedFilters.has(key)) {
    return generatedFilters.get(key);
  }

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  const imgData = ctx.createImageData(w, h);
  const data = imgData.data;

  const halfW = w / 2;
  const halfH = h / 2;
  const innerW = halfW - r;
  const innerH = halfH - r;
  const maxBezelPx = Math.max(8, Math.min(halfW, halfH) * config.bezel);

  for (let y = 0; y < h; y++) {
    const dyCenter = y - halfH;
    const qy = Math.abs(dyCenter) - innerH;

    for (let x = 0; x < w; x++) {
      const dxCenter = x - halfW;
      const qx = Math.abs(dxCenter) - innerW;

      // Signed Distance Function (SDF) para retângulo arredondado
      const outX = Math.max(qx, 0);
      const outY = Math.max(qy, 0);
      const outDist = Math.hypot(outX, outY);
      const inDist = Math.min(Math.max(qx, qy), 0);
      const sdf = outDist + inDist - r; // sdf <= 0 dentro da lente

      const idx = (y * w + x) * 4;

      if (sdf > 0) {
        data[idx] = 128;
        data[idx + 1] = 128;
        data[idx + 2] = 128;
        data[idx + 3] = 255;
        continue;
      }

      const distFromEdge = -sdf;
      const t = Math.min(1, distFromEdge / maxBezelPx);

      // Perfil de curvatura da borda: (1 - t)^curvature
      const bendStrength = Math.pow(1 - t, config.curvature * 0.45);

      // Vetor normal apontando para a borda mais próxima
      let nx = 0;
      let ny = 0;
      if (outDist > 0.0001) {
        nx = (Math.sign(dxCenter) * outX) / outDist;
        ny = (Math.sign(dyCenter) * outY) / outDist;
      } else if (qx > qy) {
        nx = Math.sign(dxCenter);
      } else {
        ny = Math.sign(dyCenter);
      }

      // Canais R e G codificam a refração da borda (128 = neutro no centro)
      const rBend = Math.round(128 + nx * bendStrength * 127);
      const gBend = Math.round(128 + ny * bendStrength * 127);

      // Canal B codifica o brilho especular na borda
      const specRim = Math.pow(1 - t, config.curvature) * config.specular;
      const bSpec = Math.round(128 + specRim * 127);

      data[idx] = Math.max(0, Math.min(255, rBend));
      data[idx + 1] = Math.max(0, Math.min(255, gBend));
      data[idx + 2] = Math.max(0, Math.min(255, bSpec));
      data[idx + 3] = 255;
    }
  }

  ctx.putImageData(imgData, 0, 0);
  const dataUrl = canvas.toDataURL("image/png");

  // Escalas cromáticas R, G, B (refraction = 17, chroma = 0.4, blur = 0)
  const scaleR = (config.refraction * (1 + config.chroma)).toFixed(2);
  const scaleG = config.refraction.toFixed(2);
  const scaleB = (config.refraction * (1 - config.chroma)).toFixed(2);

  const defs = document.getElementById("lgFilterContainer");
  if (defs) {
    const filterEl = document.createElementNS("http://www.w3.org/2000/svg", "filter");
    filterEl.setAttribute("id", key);
    filterEl.setAttribute("x", "0%");
    filterEl.setAttribute("y", "0%");
    filterEl.setAttribute("width", "100%");
    filterEl.setAttribute("height", "100%");
    filterEl.setAttribute("color-interpolation-filters", "sRGB");

    filterEl.innerHTML = `
      <feImage href="${dataUrl}" x="0" y="0" width="${w}" height="${h}" preserveAspectRatio="none" result="dispMap" />
      <feDisplacementMap in="SourceGraphic" in2="dispMap" scale="${scaleR}" xChannelSelector="R" yChannelSelector="G" result="dispR" />
      <feDisplacementMap in="SourceGraphic" in2="dispMap" scale="${scaleG}" xChannelSelector="R" yChannelSelector="G" result="dispG" />
      <feDisplacementMap in="SourceGraphic" in2="dispMap" scale="${scaleB}" xChannelSelector="R" yChannelSelector="G" result="dispB" />
      <feColorMatrix in="dispR" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="rOnly" />
      <feColorMatrix in="dispG" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="gOnly" />
      <feColorMatrix in="dispB" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="bOnly" />
      <feBlend in="rOnly" in2="gOnly" mode="screen" result="rg" />
      <feBlend in="rg" in2="bOnly" mode="screen" result="rgbOut" />
    `;
    defs.appendChild(filterEl);
  }

  generatedFilters.set(key, key);
  return key;
}

/**
 * Aplica o filtro <lg-lens> (blur=0) a todos os elementos .lg-surface e .game-card
 */
function applyLgLensSurfaces() {
  document.querySelectorAll(".lg-surface, .game-card").forEach((el) => {
    const rect = el.getBoundingClientRect();
    if (rect.width < 20 || rect.height < 20) return;
    const radius = parseInt(el.dataset.lgRadius || "26", 10);
    const filterId = createLgLensDisplacementFilter(rect.width, rect.height, radius, LG_CONFIG);
    el.style.backdropFilter = `url(#${filterId})`;
    el.style.webkitBackdropFilter = `url(#${filterId})`;
  });
}

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

  btnToggleInspector.addEventListener("click", () => {
    const body = document.getElementById("inspectorBody");
    const arrow = document.getElementById("drawerArrow");
    const isHidden = body.classList.toggle("hidden");
    arrow.textContent = isHidden ? "▼" : "▲";
    if (!isHidden) {
      requestAnimationFrame(applyLgLensSurfaces);
    }
  });

  document.querySelectorAll(".tab-pill").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-pill").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".raw-viewer").forEach((v) => v.classList.remove("active"));
      btn.classList.add("active");
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add("active");
    });
  });

  window.addEventListener("resize", () => {
    requestAnimationFrame(applyLgLensSurfaces);
  });

  applyLgLensSurfaces();
  loadNewRound();
});

async function loadNewRound() {
  const budgetSelect = document.getElementById("budgetSelect");
  const budget = parseInt(budgetSelect.value, 10) || 30;
  const gamesGrid = document.getElementById("gamesGrid");
  const resultPanel = document.getElementById("roundResultPanel");

  resultPanel.classList.add("hidden");
  gamesGrid.innerHTML = `<div class="lg-surface loading-state" data-lg-radius="28">Carregando 10 jogos...</div>`;

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
    requestAnimationFrame(applyLgLensSurfaces);
  } catch (err) {
    gamesGrid.innerHTML = `<div class="lg-surface loading-state">Erro: ${err.message}</div>`;
  }
}

function renderGamesGrid() {
  const gamesGrid = document.getElementById("gamesGrid");
  gamesGrid.innerHTML = "";

  currentRound.games.forEach((game) => {
    const isSelected = currentRound.selectedIds.has(String(game.gameID));
    const card = document.createElement("div");
    card.className = `game-card ${isSelected ? "selected" : ""}`;
    card.dataset.lgRadius = "26";

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

  requestAnimationFrame(applyLgLensSurfaces);
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
    requestAnimationFrame(() => {
      applyLgLensSurfaces();
      resultPanel.scrollIntoView({ behavior: "smooth" });
    });
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
