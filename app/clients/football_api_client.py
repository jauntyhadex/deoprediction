from typing import Any

import httpx

from app.config.settings import settings


class FootballAPIClient:

    def __init__(self):
        self.base_url = (
            settings.football_data_base_url.rstrip(
                "/"
            )
        )

        self.headers = {
            "X-Auth-Token": (
                settings.football_data_api_key
            )
        }

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict:

        response = httpx.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        return response.json()

    def get_competitions(
        self,
    ) -> dict:

        return self._get(
            "/competitions"
        )

    def get_teams(
        self,
        competition_code: str,
        season: int | None = None,
    ) -> dict:

        params = {}

        if season is not None:
            params["season"] = season

        return self._get(
            (
                "/competitions/"
                f"{competition_code}/teams"
            ),
            params=params,
        )

    def get_matches(
        self,
        competition_code: str,
        season: int | None = None,
        status: str | None = None,
    ) -> dict:

        params = {}

        if season is not None:
            params["season"] = season

        if status is not None:
            params["status"] = status

        return self._get(
            (
                "/competitions/"
                f"{competition_code}/matches"
            ),
            params=params,
        )

    def get_players(
        self,
        team_id: int,
    ) -> dict:

        return self._get(
            f"/teams/{team_id}"
        )


if __name__ == "__main__":

    client = FootballAPIClient()

    data = client.get_competitions()

    print(
        f"Found {data.get('count', 0)} "
        "competitions"
    )