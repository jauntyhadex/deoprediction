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
      <p class="muted">${pick.competition_name} · ${localTime(pick.kickoff_time)}</p>
      <p><strong>${pick.market_type}</strong>: ${pick.selection} ${lineValue(pick.line)}</p>
      <p>Probability: <strong>${pick.probability}%</strong> · Confidence: <strong>${pick.confidence}%</strong></p>
      <p>Fair odds: <strong>${pick.fair_odds}</strong> · Score: <strong>${pick.score}</strong></p>
      <p class="muted">Competition status: ${pick.competition_status}</p>
    </article>
  `;
}

function showPage(page) {
  document.getElementById("home-page").classList.toggle("hidden", page !== "home");
  document.getElementById("fixtures-page").classList.toggle("hidden", page !== "fixtures");
  document.getElementById("picks-page").classList.toggle("hidden", page !== "picks");

  if (page === "fixtures") {
    loadFixtures();
  }

  if (page === "picks") {
    loadPicks();
  }
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

  if (search) {
    params.set("search", search);
  }

  if (status) {
    params.set("status", status);
  }

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

  if (grade) {
    params.set("minimum_grade", grade);
  }

  if (market) {
    params.set("market_type", market);
  }

  const response = await fetch(`${API}/prediction-picks/top?${params.toString()}`);
  const data = await response.json();

  document.getElementById("picks").innerHTML =
    data.picks.map(pickCard).join("");
}

loadHome();
