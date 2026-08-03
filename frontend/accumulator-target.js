(function () {
  const API_BASE = "http://127.0.0.1:8000";

  function byId(id) {
    return document.getElementById(id);
  }

  function safe(value) {
    if (value === null || value === undefined || value === "") return "-";
    return String(value);
  }

  function numberValue(id, fallback) {
    const element = byId(id);
    const value = Number(element && element.value ? element.value : fallback);
    return Number.isFinite(value) ? value : fallback;
  }

  function localKickoff(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  }

  function lineText(value) {
    if (value === null || value === undefined || value === "") return "";
    return ` ${value}`;
  }

  function minimumLegOdds(targetOdds, maxLegs) {
    const target = Math.max(Number(targetOdds) || 2, 2);
    const legs = Math.max(Number(maxLegs) || 2, 2);
    const requiredAverage = Math.pow(target, 1 / legs);

    return Math.max(1.05, Math.round(requiredAverage * 100) / 100);
  }

  function resultsContainer() {
    return byId("accumulator-results") || byId("accumulators");
  }

  function ensureControls() {
    const oldTarget = byId("accumulator-target");
    const newTarget = byId("accumulator-target-odds");
    const target = oldTarget || newTarget;

    if (target && target.tagName === "SELECT") {
      const input = document.createElement("input");
      input.id = target.id;
      input.type = "number";
      input.min = "2";
      input.max = "1000000";
      input.value = target.value || "1000";
      target.replaceWith(input);
    }

    const activeTarget = byId("accumulator-target") || byId("accumulator-target-odds");

    if (activeTarget && !byId("accumulator-target-buttons")) {
      const buttons = document.createElement("div");
      buttons.id = "accumulator-target-buttons";
      buttons.className = "quick-buttons";
      buttons.innerHTML = `
        <button type="button" onclick="setAccumulatorTargetOdds(100)">100</button>
        <button type="button" onclick="setAccumulatorTargetOdds(500)">500</button>
        <button type="button" onclick="setAccumulatorTargetOdds(1000)">1000</button>
        <button type="button" onclick="setAccumulatorTargetOdds(5000)">5000</button>
        <button type="button" onclick="setAccumulatorTargetOdds(20000)">20000</button>
        <button type="button" onclick="setAccumulatorTargetOdds(30000)">30000</button>
      `;
      activeTarget.insertAdjacentElement("afterend", buttons);
    }

    if (!byId("accumulator-count") && activeTarget) {
      const count = document.createElement("select");
      count.id = "accumulator-count";
      count.innerHTML = `
        <option value="20">20 slips</option>
        <option value="100" selected>100 slips</option>
        <option value="500">500 slips</option>
        <option value="1000">1000 slips</option>
      `;
      activeTarget.insertAdjacentElement("afterend", count);
    }
  }

  window.setAccumulatorTargetOdds = function setAccumulatorTargetOdds(value) {
    const target = byId("accumulator-target") || byId("accumulator-target-odds");
    if (target) target.value = value;
  };

  window.loadAccumulator = async function loadAccumulator() {
    ensureControls();

    const container = resultsContainer();
    if (!container) return;

    const targetElement = byId("accumulator-target") || byId("accumulator-target-odds");
    const targetOdds = Number(targetElement && targetElement.value ? targetElement.value : 1000);
    const maxLegs = numberValue("accumulator-max-legs", 30);
    const count = numberValue("accumulator-count", 20);
    const minFairOdds = minimumLegOdds(targetOdds, maxLegs);

    const params = new URLSearchParams({
      count: String(count),
      target_odds: String(targetOdds),
      min_legs: "2",
      max_legs: String(maxLegs),
      pool_limit: "3000",
      days_ahead: "30",
      minimum_probability: "1",
      minimum_fair_odds: String(minFairOdds),
      maximum_fair_odds: "100",
      max_overshoot_percent: "35",
    });

    container.innerHTML = `
      <article class="card detail-card">
        <h3>Building target odds accumulators...</h3>
        <p>Target: <strong>${safe(targetOdds)}</strong></p>
        <p>Minimum leg odds required: <strong>${safe(minFairOdds)}</strong></p>
      </article>
    `;

    try {
      const response = await fetch(`${API_BASE}/prediction-picks/accumulators/target?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`Accumulator API failed: ${response.status}`);
      }

      const data = await response.json();
      const slips = data.accumulators || [];

      container.innerHTML = `
        <article class="card detail-card">
          <h3>Target Odds Accumulators</h3>
          <p>Requested slips: <strong>${safe(data.requested)}</strong></p>
          <p>Returned slips: <strong>${safe(data.count)}</strong></p>
          <p>Target odds: <strong>${safe(data.target_odds)}</strong></p>
          <p>Allowed range: <strong>${safe(data.minimum_total_odds)}</strong> - <strong>${safe(data.maximum_total_odds)}</strong></p>
          <p>Minimum leg odds used: <strong>${safe(minFairOdds)}</strong></p>
          <p>Market pool: <strong>${safe(data.pool_size)}</strong></p>
        </article>

        ${
          slips.length
            ? slips.map((slip) => `
              <article class="card detail-card">
                <div class="row">
                  <h3>Slip #${safe(slip.rank)}</h3>
                  <span class="badge">${safe(slip.legs_count)} legs</span>
                </div>

                <div class="pick-main">
                  <p class="pick-label">Total Fair Odds</p>
                  <h2>${safe(slip.total_fair_odds)}</h2>
                </div>

                <p>Target: <strong>${safe(slip.target_odds)}</strong></p>
                <p>Combined probability: <strong>${safe(slip.combined_probability)}%</strong></p>
                <p>Average confidence: <strong>${safe(slip.average_confidence)}%</strong></p>

                <details>
                  <summary>View legs</summary>
                  <div class="stack">
                    ${(slip.legs || []).map((leg, index) => `
                      <div class="mini-card">
                        <strong>Leg ${index + 1}: ${safe(leg.home_team)} vs ${safe(leg.away_team)}</strong>
                        <p class="muted">${safe(leg.competition_name)} - ${localKickoff(leg.kickoff_time)}</p>
                        <p>${safe(leg.market_type)}: <strong>${safe(leg.selection)}${lineText(leg.line)}</strong></p>
                        <p>Fair odds: <strong>${safe(leg.fair_odds)}</strong> - Probability: <strong>${safe(leg.probability)}%</strong></p>
                      </div>
                    `).join("")}
                  </div>
                </details>
              </article>
            `).join("")
            : `<article class="card detail-card"><h3>No accumulator found</h3><p>Try more legs or lower target odds.</p></article>`
        }
      `;
    } catch (error) {
      container.innerHTML = `
        <article class="card detail-card error">
          <h3>Accumulator failed</h3>
          <p>${safe(error.message)}</p>
        </article>
      `;
    }
  };

  window.loadAccumulators = window.loadAccumulator;
  window.buildAccumulators = window.loadAccumulator;

  document.addEventListener("DOMContentLoaded", function () {
    ensureControls();
  });
})();
