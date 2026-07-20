const API = "http://127.0.0.1:8000";

function localTime(value) {
  return new Date(value).toLocaleString();
}

function lineValue(value) {
  return value ?? "";
}

function pickCard(pick) {
  return `
    <article class="card">
      <div class="row">
        <h3>${pick.home_team} vs ${pick.away_team}</h3>
        <span class="badge">${pick.grade}</span>
      </div>
      <p class="muted">${pick.competition_name} - ${localTime(pick.kickoff_time)}</p>
      <p><strong>${pick.market_type}</strong>: ${pick.selection} ${lineValue(pick.line)}</p>
      <p>Probability: <strong>${pick.probability}%</strong> - Confidence: <strong>${pick.confidence}%</strong></p>
      <p>Fair odds: <strong>${pick.fair_odds}</strong> - Score: <strong>${pick.score}</strong></p>
      <p class="muted">Competition status: ${pick.competition_status}</p>
    </article>
  `;
}

function marketCard(market) {
  return `
    <article class="card">
      <div class="row">
        <h3>${market.home_team} vs ${market.away_team}</h3>
        <span class="badge">${market.grade}</span>
      </div>
      <p class="muted">${market.competition_name} - ${localTime(market.kickoff_time)}</p>
      <p><strong>${market.market_type}</strong>: ${market.selection} ${lineValue(market.line)}</p>
      <p>Probability: <strong>${market.probability}%</strong> - Market confidence: <strong>${market.market_confidence}%</strong></p>
      <p>Fair odds: <strong>${market.fair_odds}</strong> - Score: <strong>${market.score}</strong></p>
      <p>Fixture lean: <strong>${market.fixture_result}</strong> - Gate: <strong>${market.quality_gate}</strong></p>
      <p class="muted">Competition status: ${market.competition_status}</p>
    </article>
  `;
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

  try {
    const response = await fetch(`${API}/discovery/home`);
    const data = await response.json();

    status.textContent = "Backend connected";

    document.getElementById("counts").innerHTML = `
      <div class="grid">
        <div class="stat"><span>Competitions</span><strong>${data.counts.competitions}</strong></div>
        <div class="stat"><span>Teams</span><strong>${data.counts.teams}</strong></div>
        <div class="stat"><span>Fixtures</span><strong>${data.counts.fixtures}</strong></div>
        <div class="stat"><span>Predictions</span><strong>${data.counts.predictions}</strong></div>
        <div class="stat"><span>Markets</span><strong>${data.counts.markets}</strong></div>
        <div class="stat"><span>Picks</span><strong>${data.counts.picks}</strong></div>
      </div>
    `;

    document.getElementById("home-picks").innerHTML =
      data.top_picks.picks.map(pickCard).join("");

  } catch (error) {
    status.textContent = "Backend not connected. Start the API server.";
  }
}

async function loadFixtures() {
  const search = document.getElementById("fixture-search").value.trim();
  const status = document.getElementById("fixture-status").value;
  const upcomingOnly = document.getElementById("upcoming-only").checked;

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: String(upcomingOnly),
  });

  if (search) params.set("search", search);
  if (status) params.set("status", status);

  const response = await fetch(`${API}/fixtures?${params.toString()}`);
  const data = await response.json();

  document.getElementById("fixtures").innerHTML =
    data.fixtures.map((fixture) => `
      <article class="card">
        <h3>${fixture.home_team.name} vs ${fixture.away_team.name}</h3>
        <p class="muted">${fixture.competition.name}</p>
        <p>Status: <strong>${fixture.status}</strong></p>
        <p>${localTime(fixture.kickoff_time)}</p>
      </article>
    `).join("");
}

async function loadPicks() {
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

  const response = await fetch(`${API}/prediction-picks/top?${params.toString()}`);
  const data = await response.json();

  document.getElementById("picks").innerHTML =
    data.picks.map(pickCard).join("");
}

async function loadMarkets() {
  const market = document.getElementById("market-filter").value;

  const params = new URLSearchParams({
    limit: "20",
    upcoming_only: "true",
  });

  if (market) params.set("market_type", market);

  const response = await fetch(`${API}/prediction-picks/markets/top?${params.toString()}`);
  const data = await response.json();

  document.getElementById("markets").innerHTML =
    data.markets.map(marketCard).join("");
}

async function loadCompetitions() {
  const search = document.getElementById("competition-search").value.trim();
  const reliability = document.getElementById("competition-status").value;

  const params = new URLSearchParams({
    limit: "30",
  });

  if (search) params.set("search", search);
  if (reliability) params.set("reliability_status", reliability);

  const response = await fetch(`${API}/competitions?${params.toString()}`);
  const data = await response.json();

  document.getElementById("competitions").innerHTML =
    data.competitions.map((competition) => `
      <article class="card">
        <div class="row">
          <h3>${competition.name}</h3>
          <span class="badge">${competition.reliability.status}</span>
        </div>
        <p class="muted">${competition.country} - ${competition.code}</p>
        <p>Season: <strong>${competition.season}</strong></p>
        <p>Evaluations: <strong>${competition.reliability.evaluations}</strong></p>
        <p>Accuracy: <strong>${competition.reliability.accuracy}%</strong></p>
        <p>Brier: <strong>${competition.reliability.brier}</strong></p>
        <p class="muted">${competition.reliability.status_message ?? competition.reliability.message ?? ""}</p>
      </article>
    `).join("");
}

async function loadTeams() {
  const search = document.getElementById("team-search").value.trim();
  const country = document.getElementById("team-country").value.trim();

  const params = new URLSearchParams({
    limit: "30",
  });

  if (search) params.set("search", search);
  if (country) params.set("country", country);

  const response = await fetch(`${API}/teams?${params.toString()}`);
  const data = await response.json();

  document.getElementById("teams").innerHTML =
    data.teams.map((team) => `
      <article class="card">
        <div class="row">
          <h3>${team.name}</h3>
          <span class="badge">${team.tla ?? ""}</span>
        </div>
        <p class="muted">${team.country ?? "Unknown country"}</p>
        <p>Short name: <strong>${team.short_name ?? ""}</strong></p>
        <p>Competition: <strong>${team.competition?.name ?? "None"}</strong></p>
        <p>Venue: <strong>${team.venue ?? "Unknown"}</strong></p>
      </article>
    `).join("");
}


function selectionNames(selections) {
  return selections.map((item) => item.selection ?? item).join(", ");
}

async function loadCatalog() {
  const response = await fetch(`${API}/markets/catalog`);
  const data = await response.json();

  document.getElementById("catalog").innerHTML = `
    <div class="grid">
      ${data.market_types.map((market) => `
        <article class="card">
          <h3>${market.display_name}</h3>
          <p class="muted">${market.market_type}</p>
          <p>Markets: <strong>${market.market_count}</strong></p>
          <p>Selections: <strong>${selectionNames(market.selections)}</strong></p>
        </article>
      `).join("")}
    </div>
  `;
}

loadHome();
