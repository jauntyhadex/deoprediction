const API = "http://127.0.0.1:8000";

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

function messageCard(message) {
  return `<article class="card message"><p>${display(message)}</p></article>`;
}

function setLoading(containerId, message = "Loading...") {
  document.getElementById(containerId).innerHTML = messageCard(message);
}

function setError(containerId, message = "Could not load data. Check that the backend server is running.") {
  document.getElementById(containerId).innerHTML = `<article class="card error"><p>${display(message)}</p></article>`;
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
      <p class="muted">Competition status: ${display(pick.competition_status)}</p>
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
      <p>Fixture lean: <strong>${display(market.fixture_result)}</strong> - Gate: <strong>${display(market.quality_gate)}</strong></p>
      <p class="muted">Competition status: ${display(market.competition_status)}</p>
    </article>
  `;
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

  if (page === "fixtures") loadFixtures();
  if (page === "picks") loadPicks();
  if (page === "markets") loadMarkets();
  if (page === "competitions") loadCompetitions();
  if (page === "teams") loadTeams();
  if (page === "catalog") loadCatalog();
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

    renderCards("home-picks", data.top_picks.picks, "No top picks found.", pickCard);
  } catch (error) {
    status.textContent = "Backend not connected. Start the API server.";
    setError("counts");
    setError("home-picks");
  }
}

async function loadFixtures() {
  setLoading("fixtures", "Loading fixtures...");

  const search = document.getElementById("fixture-search").value.trim();
  const status = document.getElementById("fixture-status").value;
  const upcomingOnly = document.getElementById("upcoming-only").checked;

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: String(upcomingOnly),
  });

  if (search) params.set("search", search);
  if (status) params.set("status", status);

  try {
    const data = await fetchJson(`${API}/fixtures?${params.toString()}`);

    renderCards("fixtures", data.fixtures, "No fixtures found.", (fixture) => `
      <article class="card">
        <h3>${display(fixture.home_team?.name)} vs ${display(fixture.away_team?.name)}</h3>
        <p class="muted">${display(fixture.competition?.name)}</p>
        <p>Status: <strong>${display(fixture.status)}</strong></p>
        <p>${localTime(fixture.kickoff_time)}</p>
      </article>
    `);
  } catch (error) {
    setError("fixtures", error.message);
  }
}

async function loadPicks() {
  setLoading("picks", "Loading picks...");

  const grade = document.getElementById("pick-grade").value;
  const market = document.getElementById("pick-market").value;
  const onePerFixture = document.getElementById("one-pick-per-fixture").checked;

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: "true",
    one_per_fixture: String(onePerFixture),
  });

  if (grade) params.set("minimum_grade", grade);
  if (market) params.set("market_type", market);

  try {
    const data = await fetchJson(`${API}/prediction-picks/top?${params.toString()}`);
    renderCards("picks", data.picks, "No picks found for these filters.", pickCard);
  } catch (error) {
    setError("picks", error.message);
  }
}

async function loadMarkets() {
  setLoading("markets", "Loading markets...");

  const market = document.getElementById("market-filter").value;

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: "true",
  });

  if (market) params.set("market_type", market);

  try {
    const data = await fetchJson(`${API}/prediction-picks/markets/top?${params.toString()}`);
    renderCards("markets", data.markets, "No markets found for these filters.", marketCard);
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

async function loadTeams() {
  setLoading("teams", "Loading teams...");

  const search = document.getElementById("team-search").value.trim();
  const country = document.getElementById("team-country").value.trim();

  const params = new URLSearchParams({
    limit: "30",
  });

  if (search) params.set("search", search);
  if (country) params.set("country", country);

  try {
    const data = await fetchJson(`${API}/teams?${params.toString()}`);

    renderCards("teams", data.teams, "No teams found.", (team) => `
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
    `);
  } catch (error) {
    setError("teams", error.message);
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
