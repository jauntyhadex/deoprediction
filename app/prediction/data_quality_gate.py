class PredictionDataQualityGate:

    MINIMUM_TOTAL_MATCHES = 3
    MINIMUM_HOME_MATCHES = 1
    MINIMUM_AWAY_MATCHES = 1

    @staticmethod
    def passes(
        home_team_id: int,
        away_team_id: int,
        team_stats: dict,
        venue_stats: dict,
    ) -> bool:

        home_team_stat = team_stats.get(
            home_team_id
        )

        away_team_stat = team_stats.get(
            away_team_id
        )

        home_venue_stat = venue_stats.get(
            home_team_id
        )

        away_venue_stat = venue_stats.get(
            away_team_id
        )

        if not all(
            [
                home_team_stat,
                away_team_stat,
                home_venue_stat,
                away_venue_stat,
            ]
        ):
            return False

        home_total_matches = int(
            home_team_stat.matches_played or 0
        )

        away_total_matches = int(
            away_team_stat.matches_played or 0
        )

        home_matches = int(
            home_venue_stat.home_matches or 0
        )

        away_matches = int(
            away_venue_stat.away_matches or 0
        )

        return (
            home_total_matches
            >= PredictionDataQualityGate.MINIMUM_TOTAL_MATCHES
            and away_total_matches
            >= PredictionDataQualityGate.MINIMUM_TOTAL_MATCHES
            and home_matches
            >= PredictionDataQualityGate.MINIMUM_HOME_MATCHES
            and away_matches
            >= PredictionDataQualityGate.MINIMUM_AWAY_MATCHES
        )