# DeoPrediction

DeoPrediction is a FastAPI football prediction backend.

It imports football fixtures, calculates team statistics and ratings, generates match predictions, creates prediction markets, ranks prediction picks, and exposes the results through an API.

## Features

- Football fixture importing and updating
- Team statistics and home/away statistics
- Recent form and head-to-head calculations
- Elo, strength-of-schedule, team, and power ratings
- Expected-goals and match-result predictions
- Prediction market generation
- Ranked prediction picks
- Walk-forward model validation
- Competition reliability classifications
- Prediction quality gates
- FastAPI and Swagger documentation
- SQLite database with SQLAlchemy and Alembic
- One-command data refresh

## Requirements

- Python
- Git
- A football-data.org API key

## Windows Setup

Clone the repository:

```powershell
git clone https://github.com/jauntyhadex/deoprediction.git
cd deoprediction
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace:

```text
FOOTBALL_DATA_API_KEY=replace_with_your_api_key
```

with your real football-data.org API key.

Do not commit the `.env` file.

## Database Setup

Apply all database migrations:

```powershell
alembic upgrade head
```

## Start the API

Run:

```powershell
uvicorn app.main:app --reload
```

Open the Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Basic health endpoint:

```text
GET /health
```

Detailed system status endpoint:

```text
GET /system/status
```

The detailed status endpoint reports database connectivity and the current fixture, prediction, market, and pick counts.

## Prediction Endpoints

Top ranked prediction picks:

```text
GET /prediction-picks/top
```

Top prediction markets:

```text
GET /prediction-picks/markets/top
```

Prediction picks for one fixture:

```text
GET /prediction-picks/fixture/{fixture_id}
```

The Swagger page provides all supported query parameters and filters.

## Full Data Refresh

Run the complete refresh workflow:

```powershell
python -m app.scripts.refresh_prediction_data
```

The command performs these steps:

1. Imports new fixtures and updates existing fixtures.
2. Rebuilds walk-forward validation results.
3. Rebuilds the complete prediction pipeline.

The full refresh can take several minutes and makes requests to the football data provider.

## Rebuild Predictions Without Importing Fixtures

Run:

```powershell
python -m app.scripts.rebuild_prediction_pipeline
```

## Run Walk-Forward Validation

Run:

```powershell
python -m app.scripts.walk_forward_backtest
```

## Project Structure

```text
app/
├── api/          FastAPI routes
├── clients/      External API clients
├── config/       Application settings
├── database/     Database connection and model loading
├── models/       SQLAlchemy database models
├── prediction/   Prediction calculations
├── providers/    Football data providers
├── scripts/      Import, rebuild, validation, and refresh commands
└── services/     Application services
```

## Environment Variables

The required variables are documented in `.env.example`:

```text
DATABASE_URL=sqlite:///./deoprediction.db
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4
FOOTBALL_DATA_API_KEY=replace_with_your_api_key
```

## Security

The following local files must not be committed:

```text
.env
deoprediction.db
.venv/
```

Never publish or paste the real football API key.