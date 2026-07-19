const API = "http://127.0.0.1:8000";

function localTime(value) {
  return new Date(value).toLocaleString();
}

function money(value) {
  return value ?? "";
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

    document.getElementById("picks").innerHTML =
      data.top_picks.picks.map((pick) => `
        <article class="card">
          <div class="row">
            <h3>${pick.home_team} vs ${pick.away_team}</h3>
            <span class="badge">${pick.grade}</span>
          </div>
          <p class="muted">${pick.competition_name} · ${localTime(pick.kickoff_time)}</p>
          <p><strong>${pick.market_type}</strong>: ${pick.selection} ${money(pick.line)}</p>
          <p>Probability: <strong>${pick.probability}%</strong> · Confidence: <strong>${pick.confidence}%</strong></p>
          <p class="muted">Competition status: ${pick.competition_status}</p>
        </article>
      `).join("");

    document.getElementById("fixtures").innerHTML =
      data.upcoming_fixtures.fixtures.map((fixture) => `
        <article class="card">
          <h3>${fixture.home_team.name} vs ${fixture.away_team.name}</h3>
          <p class="muted">${fixture.competition.name}</p>
          <p>Status: <strong>${fixture.status}</strong></p>
          <p>${localTime(fixture.kickoff_time)}</p>
        </article>
      `).join("");

  } catch (error) {
    status.textContent = "Backend not connected. Start the API server.";
  }
}

loadHome();
