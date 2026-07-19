const API = "http://127.0.0.1:8000";

function localTime(value) {
  return new Date(value).toLocaleString();
}

async function loadHome() {
  const status = document.getElementById("status");

  try {
    const response = await fetch(`${API}/discovery/home`);
    const data = await response.json();

    status.textContent = "Backend connected.";

    document.getElementById("counts").innerHTML = `
      <div class="card">
        <p>Competitions: ${data.counts.competitions}</p>
        <p>Teams: ${data.counts.teams}</p>
        <p>Fixtures: ${data.counts.fixtures}</p>
        <p>Predictions: ${data.counts.predictions}</p>
        <p>Markets: ${data.counts.markets}</p>
        <p>Picks: ${data.counts.picks}</p>
      </div>
    `;

    document.getElementById("picks").innerHTML =
      data.top_picks.picks.map((pick) => `
        <div class="card">
          <strong>${pick.home_team} vs ${pick.away_team}</strong>
          <p>${pick.market_type}: ${pick.selection} ${pick.line ?? ""}</p>
          <p>Probability: ${pick.probability}%</p>
          <p>Confidence: ${pick.confidence}%</p>
          <p>Grade: ${pick.grade}</p>
          <p class="small">${localTime(pick.kickoff_time)}</p>
        </div>
      `).join("");

    document.getElementById("fixtures").innerHTML =
      data.upcoming_fixtures.fixtures.map((fixture) => `
        <div class="card">
          <strong>${fixture.home_team.name} vs ${fixture.away_team.name}</strong>
          <p>${fixture.competition.name}</p>
          <p>Status: ${fixture.status}</p>
          <p class="small">${localTime(fixture.kickoff_time)}</p>
        </div>
      `).join("");

  } catch (error) {
    status.textContent = "Backend not connected. Start the API server first.";
  }
}

loadHome();
