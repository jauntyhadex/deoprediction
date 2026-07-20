const API = "http://127.0.0.1:8000";

let teamOffset = 0;
const teamPageSize = 100;

function escapeHtml(value) {
  const text = value === null || value === undefined ? "" : String(value);
  return text.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

function display(value, fallback = "") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return escapeHtml(value);
}

function localTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return display(value);
  return date.toLocaleString();
}

function lineValue(value) {
  if (value === null || value === undefined || value === "") return "";
  return display(value);
}

function dateInputValue(daysFromToday = 0) {
  const date = new Date();
  date.setDate(date.getDate() + daysFromToday);

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function dateRangeParams(dateValue) {
  if (!dateValue) return null;

  const start = new Date(`${dateValue}T00:00:00`);
  const end = new Date(`${dateValue}T23:59:59`);

  return {
    date_from: start.toISOString(),
    date_to: end.toISOString(),
  };
}

function readableDate(dateValue) {
  if (!dateValue) {
    return "All upcoming dates, sorted from closest first.";
  }

  const date = new Date(`${dateValue}T00:00:00`);
  return `Showing games for ${date.toLocaleDateString(undefined, {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  })}.`;
}

function updateDateLabel(elementId, dateValue) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = readableDate(dateValue);
  }
}

function setFixtureDate(daysFromToday) {
  document.getElementById("fixture-date").value = dateInputValue(daysFromToday);
  loadFixtures();
}

function clearFixtureDate() {
  document.getElementById("fixture-date").value = "";
  loadFixtures();
}

function setPickDate(daysFromToday) {
  document.getElementById("pick-date").value = dateInputValue(daysFromToday);
  loadPicks();
}

function clearPickDate() {
  document.getElementById("pick-date").value = "";
  loadPicks();
}

function setMarketDate(daysFromToday) {
  document.getElementById("market-date").value = dateInputValue(daysFromToday);
  loadMarkets();
}

function clearMarketDate() {
  document.getElementById("market-date").value = "";
  loadMarkets();
}

function setMarketOption(marketType, selection, line) {
  document.getElementById("market-filter").value = marketType;
  document.getElementById("market-selection").value = selection;
  document.getElementById("market-line").value = line;
  loadMarkets();
}

function goToMarketOption(marketType, selection, line) {
  showPage("markets");
  document.getElementById("market-filter").value = marketType;
  document.getElementById("market-selection").value = selection;
  document.getElementById("market-line").value = line;
  loadMarkets();
}

function messageCard(message) {
  return `<article class="card message"><p>${display(message)}</p></article>`;
}

function setLoading(containerId, message = "Loading...") {
  document.getElementById(containerId).innerHTML = messageCard(message);
}

function setError(containerId, message = "Could not load data. Check that the backend server is running.") {
  document.getElementById(containerId).innerHTML = `<article class="card error"><p>${display(message)}</p></article>`;
}

function sortByKickoff(items) {
  const list = Array.isArray(items) ? [...items] : [];

  return list.sort((a, b) => {
    const firstDate = new Date(a.kickoff_time || 0).getTime();
    const secondDate = new Date(b.kickoff_time || 0).getTime();

    if (firstDate !== secondDate) {
      return firstDate - secondDate;
    }

    return Number(b.score || 0) - Number(a.score || 0);
  });
}

function renderCards(containerId, items, emptyMessage, cardBuilder) {
  const list = Array.isArray(items) ? items : [];
  document.getElementById(containerId).innerHTML =
    list.length > 0 ? list.map(cardBuilder).join("") : messageCard(emptyMessage);
}

async function fetchJson(url) {
  const response = await fetch(url);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }

  return data;
}

function pickCard(pick) {
  return `
    <article class="card">
      <div class="row">
        <h3>${display(pick.home_team)} vs ${display(pick.away_team)}</h3>
        <span class="badge">${display(pick.grade)}</span>
      </div>
      <p class="muted">${display(pick.competition_name)} - ${localTime(pick.kickoff_time)}</p>
      <p><strong>${display(pick.market_type)}</strong>: ${display(pick.selection)} ${lineValue(pick.line)}</p>
      <p>Probability: <strong>${display(pick.probability)}%</strong> - Confidence: <strong>${display(pick.confidence)}%</strong></p>
      <p>Fair odds: <strong>${display(pick.fair_odds)}</strong> - Score: <strong>${display(pick.score)}</strong></p>
      ${oddsWarning(pick.fair_odds)}
      <p class="muted">Competition status: ${display(pick.competition_status)}</p>
      ${reliabilityWarning(pick.competition_status, pick.competition_status_message)}
    </article>
  `;
}

function marketCard(market) {
  return `
    <article class="card">
      <div class="row">
        <h3>${display(market.home_team)} vs ${display(market.away_team)}</h3>
        <span class="badge">${display(market.grade)}</span>
      </div>
      <p class="muted">${display(market.competition_name)} - ${localTime(market.kickoff_time)}</p>
      <p><strong>${display(market.market_type)}</strong>: ${display(market.selection)} ${lineValue(market.line)}</p>
      <p>Probability: <strong>${display(market.probability)}%</strong> - Market confidence: <strong>${display(market.market_confidence)}%</strong></p>
      <p>Fair odds: <strong>${display(market.fair_odds)}</strong> - Score: <strong>${display(market.score)}</strong></p>
      ${oddsWarning(market.fair_odds)}
      <p>Fixture lean: <strong>${display(market.fixture_result)}</strong> - Gate: <strong>${display(market.quality_gate)}</strong></p>
      <p class="muted">Competition status: ${display(market.competition_status)}</p>
      ${reliabilityWarning(market.competition_status, market.competition_status_message)}
    </article>
  `;
}

function reliabilityWarning(status, message = "") {
  const value = String(status || "").toUpperCase();

  if (value === "WEAK") {
    return `<p class="risk-warning">Weak competition history. Prediction is shown, but risk is higher. ${display(message)}</p>`;
  }

  if (value === "LIMITED" || value === "UNVALIDATED") {
    return `<p class="risk-caution">Limited validation history. Use extra caution. ${display(message)}</p>`;
  }

  if (value === "PROMISING") {
    return `<p class="risk-good">Promising competition history, but still not guaranteed.</p>`;
  }

  if (value === "RELIABLE") {
    return `<p class="risk-good">Reliable competition history.</p>`;
  }

  return "";
}

function oddsWarning(fairOdds) {
  const odds = Number(fairOdds);

  if (!Number.isFinite(odds)) {
    return "";
  }

  if (odds < 1.15) {
    return `<p class="odds-warning">Very low odds. High probability, but weak betting value.</p>`;
  }

  if (odds < 1.30) {
    return `<p class="odds-caution">Low odds. Better as a bet-builder leg, not a main pick.</p>`;
  }

  return "";
}

function selectionNames(selections) {
  if (!Array.isArray(selections)) return "";

  return selections
    .map((item) => {
      if (item === null || item === undefined) return "";
      if (typeof item === "object") {
        return item.selection ?? item.name ?? item.value ?? "";
      }
      return item;
    })
    .filter(Boolean)
    .join(", ");
}

function showPage(page) {
  document.getElementById("home-page").classList.toggle("hidden", page !== "home");
  document.getElementById("fixtures-page").classList.toggle("hidden", page !== "fixtures");
  document.getElementById("picks-page").classList.toggle("hidden", page !== "picks");
  document.getElementById("markets-page").classList.toggle("hidden", page !== "markets");
  document.getElementById("competitions-page").classList.toggle("hidden", page !== "competitions");
  document.getElementById("teams-page").classList.toggle("hidden", page !== "teams");
  document.getElementById("catalog-page").classList.toggle("hidden", page !== "catalog");
  document.getElementById("builder-page").classList.toggle("hidden", page !== "builder");
  document.getElementById("guide-page").classList.toggle("hidden", page !== "guide");

  if (page === "fixtures") loadFixtures();
  if (page === "picks") loadPicks();
  if (page === "markets") loadMarkets();
  if (page === "competitions") loadCompetitions();
  if (page === "teams") loadTeams();
  if (page === "catalog") loadCatalog();
  if (page === "builder") loadBuilderFixtures();
}

async function loadHome() {
  const status = document.getElementById("status");
  setLoading("counts", "Loading database stats...");
  setLoading("home-picks", "Loading top picks...");

  try {
    const data = await fetchJson(`${API}/discovery/home`);

    status.textContent = "Backend connected";

    document.getElementById("counts").innerHTML = `
      <div class="grid">
        <div class="stat"><span>Competitions</span><strong>${display(data.counts.competitions)}</strong></div>
        <div class="stat"><span>Teams</span><strong>${display(data.counts.teams)}</strong></div>
        <div class="stat"><span>Fixtures</span><strong>${display(data.counts.fixtures)}</strong></div>
        <div class="stat"><span>Predictions</span><strong>${display(data.counts.predictions)}</strong></div>
        <div class="stat"><span>Markets</span><strong>${display(data.counts.markets)}</strong></div>
        <div class="stat"><span>Picks</span><strong>${display(data.counts.picks)}</strong></div>
      </div>
    `;

    renderCards("home-picks", sortByKickoff(data.top_picks.picks), "No top picks found.", pickCard);
  } catch (error) {
    status.textContent = "Backend not connected. Start the API server.";
    setError("counts");
    setError("home-picks");
  }
}

async function loadFixtures() {
  setLoading("fixtures", "Loading fixtures...");
  document.getElementById("fixture-detail").innerHTML = "";

  const search = document.getElementById("fixture-search").value.trim();
  const status = document.getElementById("fixture-status").value;
  const upcomingOnly = document.getElementById("upcoming-only").checked;
  const selectedDate = document.getElementById("fixture-date").value;
  updateDateLabel("fixture-date-label", selectedDate);

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: String(upcomingOnly),
  });

  if (search) params.set("search", search);
  if (status) params.set("status", status);

  const fixtureDateRange = dateRangeParams(selectedDate);
  if (fixtureDateRange) {
    params.set("date_from", fixtureDateRange.date_from);
    params.set("date_to", fixtureDateRange.date_to);
    params.set("upcoming_only", "false");
  }

  try {
    const data = await fetchJson(`${API}/fixtures?${params.toString()}`);

    renderCards("fixtures", sortByKickoff(data.fixtures), "No fixtures found.", (fixture) => `
      <article class="card">
        <h3>${display(fixture.home_team?.name)} vs ${display(fixture.away_team?.name)}</h3>
        <p class="muted">${display(fixture.competition?.name)}</p>
        <p>Status: <strong>${display(fixture.status)}</strong></p>
        <p>${localTime(fixture.kickoff_time)}</p>
        <button onclick="loadFixtureDetail(${fixture.id})">View predictions</button>
      </article>
    `);
  } catch (error) {
    setError("fixtures", error.message);
  }
}


function fixtureMarketCard(market) {
  return `
    <article class="card">
      <div class="row">
        <h3>${display(market.market_type)}</h3>
        <span class="badge">${display(market.grade ?? market.quality_gate ?? "")}</span>
      </div>
      <p>Selection: <strong>${display(market.selection)}</strong> ${lineValue(market.line)}</p>
      <p>Probability: <strong>${display(market.probability)}%</strong></p>
      <p>Fair odds: <strong>${display(market.fair_odds)}</strong></p>
      ${oddsWarning(market.fair_odds)}
      <p>Score: <strong>${display(market.score)}</strong></p>
      <p class="muted">Gate: ${display(market.quality_gate)}</p>
      ${reliabilityWarning(market.competition_status, market.competition_status_message)}
    </article>
  `;
}

async function loadFixtureDetail(fixtureId) {
  const container = document.getElementById("fixture-detail");
  container.innerHTML = `
    <h2>Fixture Predictions</h2>
    ${messageCard("Loading fixture predictions...")}
  `;

  try {
    const data = await fetchJson(`${API}/prediction-picks/fixture/${fixtureId}`);

    const picks = data.picks ?? data.prediction_picks ?? [];
    const markets = data.markets ?? data.prediction_markets ?? [];
    const firstPick = picks[0] ?? markets[0] ?? {};

    container.innerHTML = `
      <h2>Fixture Predictions</h2>

      <article class="card detail-card">
        <h3>${display(firstPick.home_team, "Fixture")} vs ${display(firstPick.away_team, "")}</h3>
        <p class="muted">${display(firstPick.competition_name)}</p>
        <p>Kickoff: <strong>${localTime(firstPick.kickoff_time)}</strong></p>
        <p>Status: <strong>${display(firstPick.status)}</strong></p>
        <p>Competition reliability: <strong>${display(firstPick.competition_status)}</strong></p>
        <p class="muted">${display(firstPick.competition_status_message)}</p>
      </article>

      <h3>Official Picks</h3>
      <div>
        ${picks.length > 0 ? picks.map(pickCard).join("") : messageCard("No official picks passed the rules for this fixture.")}
      </div>

      <h3>Market Probabilities</h3>
      <div>
        ${markets.length > 0 ? markets.map(fixtureMarketCard).join("") : messageCard("No market probabilities found for this fixture.")}
      </div>
    `;
  } catch (error) {
    container.innerHTML = `
      <h2>Fixture Predictions</h2>
      ${messageCard(error.message)}
    `;
  }

  container.scrollIntoView({ behavior: "smooth" });
}

async function loadPicks() {
  setLoading("picks", "Loading picks...");

  const grade = document.getElementById("pick-grade").value;
  const market = document.getElementById("pick-market").value;
  const onePerFixture = document.getElementById("one-pick-per-fixture").checked;
  const selectedDate = document.getElementById("pick-date").value;
  updateDateLabel("pick-date-label", selectedDate);

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: "true",
    one_per_fixture: String(onePerFixture),
  });

  if (grade) params.set("minimum_grade", grade);
  if (market) params.set("market_type", market);

  const marketDateRange = dateRangeParams(selectedDate);
  if (marketDateRange) {
    params.set("date_from", marketDateRange.date_from);
    params.set("date_to", marketDateRange.date_to);
    params.set("upcoming_only", "false");
  }

  const pickDateRange = dateRangeParams(selectedDate);
  if (pickDateRange) {
    params.set("date_from", pickDateRange.date_from);
    params.set("date_to", pickDateRange.date_to);
    params.set("upcoming_only", "false");
  }

  try {
    const data = await fetchJson(`${API}/prediction-picks/top?${params.toString()}`);
    renderCards("picks", sortByKickoff(data.picks), "No picks found for these filters.", pickCard);
  } catch (error) {
    setError("picks", error.message);
  }
}

async function loadMarkets() {
  setLoading("markets", "Loading markets...");

  const market = document.getElementById("market-filter").value;
  const selection = document.getElementById("market-selection").value;
  const line = document.getElementById("market-line").value.trim();
  const selectedDate = document.getElementById("market-date").value;
  updateDateLabel("market-date-label", selectedDate);

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: "true",
  });

  if (market) {
    params.set("market_type", market);
  }

  if (selection) {
    params.set("selection", selection);
  }

  if (line) {
    params.set("line", line);
  }

  const marketDateRange = dateRangeParams(selectedDate);
  if (marketDateRange) {
    params.set("date_from", marketDateRange.date_from);
    params.set("date_to", marketDateRange.date_to);
    params.set("upcoming_only", "false");
    params.delete("days_ahead");
  }

  try {
    const data = await fetchJson(`${API}/prediction-picks/markets/top?${params.toString()}`);
    renderCards("markets", sortByKickoff(data.markets), "No markets found for this date and filter.", marketCard);
  } catch (error) {
    setError("markets", error.message);
  }
}

async function loadCompetitions() {
  setLoading("competitions", "Loading competitions...");

  const search = document.getElementById("competition-search").value.trim();
  const reliability = document.getElementById("competition-status").value;

  const params = new URLSearchParams({
    limit: "30",
  });

  if (search) params.set("search", search);
  if (reliability) params.set("reliability_status", reliability);

  try {
    const data = await fetchJson(`${API}/competitions?${params.toString()}`);

    renderCards("competitions", data.competitions, "No competitions found.", (competition) => `
      <article class="card">
        <div class="row">
          <h3>${display(competition.name)}</h3>
          <span class="badge">${display(competition.reliability?.status)}</span>
        </div>
        <p class="muted">${display(competition.country)} - ${display(competition.code)}</p>
        <p>Season: <strong>${display(competition.season)}</strong></p>
        <p>Evaluations: <strong>${display(competition.reliability?.evaluations)}</strong></p>
        <p>Accuracy: <strong>${display(competition.reliability?.accuracy)}%</strong></p>
        <p>Brier: <strong>${display(competition.reliability?.brier)}</strong></p>
        <p class="muted">${display(competition.reliability?.status_message ?? competition.reliability?.message)}</p>
      </article>
    `);
  } catch (error) {
    setError("competitions", error.message);
  }
}

function resetTeams() {
  teamOffset = 0;
  loadTeams(false);
}

function loadMoreTeams() {
  loadTeams(true);
}

async function loadTeams(append = false) {
  if (!append) {
    teamOffset = 0;
    setLoading("teams", "Loading teams...");
    document.getElementById("team-count").textContent = "";
  }

  const search = document.getElementById("team-search").value.trim();
  const country = document.getElementById("team-country").value.trim();

  const params = new URLSearchParams({
    limit: String(teamPageSize),
    offset: String(teamOffset),
  });

  if (search) params.set("search", search);
  if (country) params.set("country", country);

  try {
    const data = await fetchJson(`${API}/teams?${params.toString()}`);
    const teams = Array.isArray(data.teams) ? data.teams : [];

    const html = teams.length > 0
      ? teams.map((team) => `
        <article class="card">
          <div class="row">
            <h3>${display(team.name)}</h3>
            <span class="badge">${display(team.tla)}</span>
          </div>
          <p class="muted">${display(team.country, "Unknown country")}</p>
          <p>Short name: <strong>${display(team.short_name)}</strong></p>
          <p>Competition: <strong>${display(team.competition?.name, "None")}</strong></p>
          <p>Venue: <strong>${display(team.venue, "Unknown")}</strong></p>
        </article>
      `).join("")
      : messageCard(append ? "No more teams found." : "No teams found.");

    if (append) {
      document.getElementById("teams").insertAdjacentHTML("beforeend", html);
    } else {
      document.getElementById("teams").innerHTML = html;
    }

    teamOffset += teams.length;

    document.getElementById("team-count").textContent =
      teams.length > 0
        ? `Showing ${teamOffset} teams. Click Load more to continue.`
        : `Showing ${teamOffset} teams.`;
  } catch (error) {
    setError("teams", error.message);
  }
}

async function loadBuilderFixtures() {
  setLoading("builder-fixtures", "Loading fixtures...");
  document.getElementById("builder-results").innerHTML = "";

  const search = document.getElementById("builder-search").value.trim();

  const params = new URLSearchParams({
    limit: "12",
    upcoming_only: "true",
  });

  if (search) params.set("search", search);

  try {
    const data = await fetchJson(`${API}/fixtures?${params.toString()}`);

    renderCards("builder-fixtures", data.fixtures, "No fixtures found.", (fixture) => `
      <article class="card">
        <h3>${display(fixture.home_team?.name)} vs ${display(fixture.away_team?.name)}</h3>
        <p class="muted">${display(fixture.competition?.name)} - ${localTime(fixture.kickoff_time)}</p>
        <p>Status: <strong>${display(fixture.status)}</strong></p>
        <button onclick="loadBetBuilder(${fixture.id})">Build suggestions</button>
      </article>
    `);
  } catch (error) {
    setError("builder-fixtures", error.message);
  }
}

async function loadBetBuilder(fixtureId) {
  setLoading("builder-results", "Building bet builder suggestions...");

  try {
    const data = await fetchJson(`${API}/prediction-picks/fixture/${fixtureId}?market_limit=100`);
    const markets = data.markets ?? [];
    const first = markets[0] ?? (data.picks ?? [])[0] ?? {};
    const combos = buildBetBuilderCombos(markets);

    document.getElementById("builder-results").innerHTML = `
      <h2>Builder Suggestions</h2>

      <article class="card detail-card">
        <h3>${display(first.home_team)} vs ${display(first.away_team)}</h3>
        <p class="muted">${display(first.competition_name)} - ${localTime(first.kickoff_time)}</p>
        <p>Fixture lean: <strong>${display(first.fixture_result, "Not available")}</strong></p>
        <p>Competition reliability: <strong>${display(first.competition_status, "Unknown")}</strong></p>
        <p class="muted">${display(first.competition_status_message)}</p>
        ${reliabilityWarning(first.competition_status, first.competition_status_message)}
        <p>Markets checked: <strong>${display(markets.length)}</strong></p>
        <p class="odds-caution">Testing mode: builder suggestions are filtered, but not guaranteed profit.</p>
      </article>

      ${combos.length > 0 ? combos.map((combo) => builderComboCard(combo.title, combo.note, combo.legs)).join("") : messageCard("No builder suggestions found for this fixture.")}
    `;

    document.getElementById("builder-results").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    setError("builder-results", error.message);
  }
}

async function loadCatalog() {
  setLoading("catalog", "Loading market catalog...");

  try {
    const data = await fetchJson(`${API}/markets/catalog`);

    renderCards("catalog", data.market_types, "No market catalog found.", (market) => `
      <article class="card">
        <h3>${display(market.display_name)}</h3>
        <p class="muted">${display(market.market_type)}</p>
        <p>Markets: <strong>${display(market.market_count)}</strong></p>
        <p>Selections: <strong>${display(selectionNames(market.selections))}</strong></p>
      </article>
    `);
  } catch (error) {
    setError("catalog", error.message);
  }
}

loadHome();
