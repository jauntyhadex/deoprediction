import math
from collections import defaultdict, deque
from itertools import groupby

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.fixture import Fixture
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)
from app.prediction.probability import ProbabilityPredictor
from app.prediction.xg_bias_correction import XGBiasCorrection


MAX_HISTORY_MATCHES = 10
MIN_TEAM_HISTORY = 3

DEFAULT_HOME_GOALS = 1.45
DEFAULT_AWAY_GOALS = 1.15

PRIOR_WEIGHT = 5.0
COMPETITION_PRIOR_WEIGHT = 10.0

MIN_EXPECTED_GOALS = 0.25
MAX_EXPECTED_GOALS = 3.50

ELO_START = 1500.0
ELO_HOME_ADVANTAGE = 65.0
ELO_K_FACTOR = 20.0


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(float(value), maximum),
    )


def percentage(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2,
    )


def average(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        4,
    )


def result_from_score(
    home_score: int,
    away_score: int,
) -> str:
    if home_score > away_score:
        return "HOME"

    if home_score < away_score:
        return "AWAY"

    return "DRAW"


def smoothed_rate(
    records,
    field_name: str,
    prior_rate: float,
) -> float:
    matches = len(records)

    total = sum(
        float(record[field_name])
        for record in records
    )

    return (
        total
        + prior_rate * PRIOR_WEIGHT
    ) / (
        matches
        + PRIOR_WEIGHT
    )


def form_multiplier(records) -> float:
    recent_records = list(records)[-5:]

    if not recent_records:
        return 1.0

    points = sum(
        float(record["points"])
        for record in recent_records
    )

    points_per_game = (
        points / len(recent_records)
    )

    adjustment = (
        points_per_game - 1.5
    ) / 15

    return clamp(
        1 + adjustment,
        0.90,
        1.10,
    )


def competition_goal_averages(
    competition_data: dict,
) -> tuple[float, float]:
    matches = competition_data["matches"]

    home_average = (
        competition_data["home_goals"]
        + (
            DEFAULT_HOME_GOALS
            * COMPETITION_PRIOR_WEIGHT
        )
    ) / (
        matches
        + COMPETITION_PRIOR_WEIGHT
    )

    away_average = (
        competition_data["away_goals"]
        + (
            DEFAULT_AWAY_GOALS
            * COMPETITION_PRIOR_WEIGHT
        )
    ) / (
        matches
        + COMPETITION_PRIOR_WEIGHT
    )

    return (
        home_average,
        away_average,
    )


def elo_multiplier(
    home_elo: float,
    away_elo: float,
) -> tuple[float, float]:
    difference = (
        home_elo
        + ELO_HOME_ADVANTAGE
        - away_elo
    )

    home_multiplier = 10 ** (
        difference / 1600
    )

    away_multiplier = 10 ** (
        -difference / 1600
    )

    return (
        clamp(
            home_multiplier,
            0.85,
            1.20,
        ),
        clamp(
            away_multiplier,
            0.85,
            1.20,
        ),
    )


def calculate_expected_goals(
    fixture,
    team_history,
    home_history,
    away_history,
    competition_stats,
    elo_ratings,
) -> tuple[float, float]:
    home_team_id = fixture.home_team_id
    away_team_id = fixture.away_team_id

    competition_data = competition_stats[
        fixture.competition_id
    ]

    (
        competition_home_average,
        competition_away_average,
    ) = competition_goal_averages(
        competition_data
    )

    home_attack_rate = smoothed_rate(
        home_history[home_team_id],
        "goals_for",
        competition_home_average,
    )

    away_defense_rate = smoothed_rate(
        away_history[away_team_id],
        "goals_against",
        competition_home_average,
    )

    away_attack_rate = smoothed_rate(
        away_history[away_team_id],
        "goals_for",
        competition_away_average,
    )

    home_defense_rate = smoothed_rate(
        home_history[home_team_id],
        "goals_against",
        competition_away_average,
    )

    home_expected = math.sqrt(
        max(home_attack_rate, 0.01)
        * max(away_defense_rate, 0.01)
    )

    away_expected = math.sqrt(
        max(away_attack_rate, 0.01)
        * max(home_defense_rate, 0.01)
    )

    home_form = form_multiplier(
        team_history[home_team_id]
    )

    away_form = form_multiplier(
        team_history[away_team_id]
    )

    form_ratio = clamp(
        home_form / max(away_form, 0.01),
        0.90,
        1.10,
    )

    home_expected *= form_ratio
    away_expected /= form_ratio

    (
        home_elo_multiplier,
        away_elo_multiplier,
    ) = elo_multiplier(
        elo_ratings[home_team_id],
        elo_ratings[away_team_id],
    )

    home_expected *= home_elo_multiplier
    away_expected *= away_elo_multiplier

    home_expected = clamp(
        home_expected,
        MIN_EXPECTED_GOALS,
        MAX_EXPECTED_GOALS,
    )

    away_expected = clamp(
        away_expected,
        MIN_EXPECTED_GOALS,
        MAX_EXPECTED_GOALS,
    )

    base_home_xg = round(
        home_expected,
        2,
    )

    base_away_xg = round(
        away_expected,
        2,
    )

    (
        corrected_home_xg,
        corrected_away_xg,
    ) = XGBiasCorrection.apply(
        home_xg=base_home_xg,
        away_xg=base_away_xg,
    )

    return (
        round(corrected_home_xg, 2),
        round(corrected_away_xg, 2),
    )


def calculate_brier_score(
    probabilities: dict,
    actual_result: str,
) -> float:
    targets = {
        "HOME": 0.0,
        "DRAW": 0.0,
        "AWAY": 0.0,
    }

    targets[actual_result] = 1.0

    score = (
        (
            probabilities["home"] / 100
            - targets["HOME"]
        ) ** 2
        + (
            probabilities["draw"] / 100
            - targets["DRAW"]
        ) ** 2
        + (
            probabilities["away"] / 100
            - targets["AWAY"]
        ) ** 2
    ) / 3

    return round(score, 4)


def calculate_log_loss(
    probabilities: dict,
    actual_result: str,
) -> float:
    probability_map = {
        "HOME": probabilities["home"] / 100,
        "DRAW": probabilities["draw"] / 100,
        "AWAY": probabilities["away"] / 100,
    }

    actual_probability = clamp(
        probability_map[actual_result],
        0.000001,
        0.999999,
    )

    return round(
        -math.log(actual_probability),
        4,
    )


def update_elo(
    fixture,
    elo_ratings,
) -> None:
    home_team_id = fixture.home_team_id
    away_team_id = fixture.away_team_id

    home_elo = elo_ratings[home_team_id]
    away_elo = elo_ratings[away_team_id]

    expected_home = 1 / (
        1
        + 10 ** (
            (
                away_elo
                - (
                    home_elo
                    + ELO_HOME_ADVANTAGE
                )
            ) / 400
        )
    )

    actual_result = result_from_score(
        fixture.home_score,
        fixture.away_score,
    )

    if actual_result == "HOME":
        actual_home = 1.0
    elif actual_result == "DRAW":
        actual_home = 0.5
    else:
        actual_home = 0.0

    change = ELO_K_FACTOR * (
        actual_home - expected_home
    )

    elo_ratings[home_team_id] = (
        home_elo + change
    )

    elo_ratings[away_team_id] = (
        away_elo - change
    )


def update_history(
    fixture,
    team_history,
    home_history,
    away_history,
    competition_stats,
    elo_ratings,
) -> None:
    home_score = int(fixture.home_score)
    away_score = int(fixture.away_score)

    if home_score > away_score:
        home_points = 3
        away_points = 0
    elif home_score < away_score:
        home_points = 0
        away_points = 3
    else:
        home_points = 1
        away_points = 1

    home_record = {
        "goals_for": home_score,
        "goals_against": away_score,
        "points": home_points,
    }

    away_record = {
        "goals_for": away_score,
        "goals_against": home_score,
        "points": away_points,
    }

    team_history[
        fixture.home_team_id
    ].append(home_record)

    team_history[
        fixture.away_team_id
    ].append(away_record)

    home_history[
        fixture.home_team_id
    ].append(home_record)

    away_history[
        fixture.away_team_id
    ].append(away_record)

    competition_data = competition_stats[
        fixture.competition_id
    ]

    competition_data["matches"] += 1
    competition_data["home_goals"] += home_score
    competition_data["away_goals"] += away_score

    update_elo(
        fixture,
        elo_ratings,
    )


def print_report(
    evaluations,
    skipped: int,
) -> None:
    total = len(evaluations)

    correct_results = sum(
        1
        for evaluation in evaluations
        if evaluation.result_correct
    )

    exact_scores = sum(
        1
        for evaluation in evaluations
        if evaluation.score_correct
    )

    print("\nWALK-FORWARD BACKTEST")
    print("-" * 60)

    print(f"Evaluations: {total}")
    print(f"Skipped for insufficient history: {skipped}")

    print(
        f"Result accuracy: "
        f"{percentage(correct_results, total)}%"
    )

    print(
        f"Exact-score accuracy: "
        f"{percentage(exact_scores, total)}%"
    )

    print(
        f"Average Brier score: "
        f"{average([
            float(row.brier_score)
            for row in evaluations
        ])}"
    )

    print(
        f"Average log loss: "
        f"{average([
            float(row.log_loss)
            for row in evaluations
        ])}"
    )

    print(
        f"Average goal error: "
        f"{average([
            float(row.goal_error)
            for row in evaluations
        ])}"
    )

    print("\nPREDICTED RESULT BREAKDOWN")
    print("-" * 60)

    for result in [
        "HOME",
        "DRAW",
        "AWAY",
    ]:
        rows = [
            row
            for row in evaluations
            if row.predicted_result == result
        ]

        correct = sum(
            1
            for row in rows
            if row.result_correct
        )

        print(
            f"{result}: "
            f"{correct}/{len(rows)} correct "
            f"({percentage(correct, len(rows))}%)"
        )

    print("\nACTUAL RESULT RECALL")
    print("-" * 60)

    for result in [
        "HOME",
        "DRAW",
        "AWAY",
    ]:
        rows = [
            row
            for row in evaluations
            if row.actual_result == result
        ]

        detected = sum(
            1
            for row in rows
            if row.predicted_result == result
        )

        print(
            f"{result}: "
            f"{detected}/{len(rows)} detected "
            f"({percentage(detected, len(rows))}%)"
        )


def main():
    db = SessionLocal()

    team_history = defaultdict(
        lambda: deque(
            maxlen=MAX_HISTORY_MATCHES
        )
    )

    home_history = defaultdict(
        lambda: deque(
            maxlen=MAX_HISTORY_MATCHES
        )
    )

    away_history = defaultdict(
        lambda: deque(
            maxlen=MAX_HISTORY_MATCHES
        )
    )

    competition_stats = defaultdict(
        lambda: {
            "matches": 0,
            "home_goals": 0.0,
            "away_goals": 0.0,
        }
    )

    elo_ratings = defaultdict(
        lambda: ELO_START
    )

    try:
        db.query(
            WalkForwardEvaluation
        ).delete(
            synchronize_session=False
        )

        db.commit()

        fixtures = (
            db.query(Fixture)
            .filter(
                Fixture.kickoff_time.isnot(None),
                Fixture.home_score.isnot(None),
                Fixture.away_score.isnot(None),
            )
            .order_by(
                Fixture.kickoff_time.asc(),
                Fixture.id.asc(),
            )
            .all()
        )

        skipped = 0
        created = 0

        grouped_fixtures = groupby(
            fixtures,
            key=lambda fixture: fixture.kickoff_time,
        )

        for _, fixture_group in grouped_fixtures:
            batch = list(fixture_group)
            pending_evaluations = []

            for fixture in batch:
                home_history_count = len(
                    team_history[
                        fixture.home_team_id
                    ]
                )

                away_history_count = len(
                    team_history[
                        fixture.away_team_id
                    ]
                )

                if (
                    home_history_count
                    < MIN_TEAM_HISTORY
                    or away_history_count
                    < MIN_TEAM_HISTORY
                ):
                    skipped += 1
                    continue

                home_xg, away_xg = (
                    calculate_expected_goals(
                        fixture,
                        team_history,
                        home_history,
                        away_history,
                        competition_stats,
                        elo_ratings,
                    )
                )

                probabilities = (
                    ProbabilityPredictor
                    .match_probabilities(
                        home_xg,
                        away_xg,
                    )
                )

                probability_map = {
                    "HOME": probabilities["home"],
                    "DRAW": probabilities["draw"],
                    "AWAY": probabilities["away"],
                }

                predicted_result = max(
                    probability_map,
                    key=probability_map.get,
                )

                actual_result = result_from_score(
                    fixture.home_score,
                    fixture.away_score,
                )

                predicted_home_score = round(
                    home_xg
                )

                predicted_away_score = round(
                    away_xg
                )

                actual_home_score = int(
                    fixture.home_score
                )

                actual_away_score = int(
                    fixture.away_score
                )

                goal_error = (
                    abs(
                        predicted_home_score
                        - actual_home_score
                    )
                    + abs(
                        predicted_away_score
                        - actual_away_score
                    )
                ) / 2

                pending_evaluations.append(
                    WalkForwardEvaluation(
                        fixture_id=fixture.id,
                        competition_id=(
                            fixture.competition_id
                        ),
                        home_team_id=(
                            fixture.home_team_id
                        ),
                        away_team_id=(
                            fixture.away_team_id
                        ),
                        kickoff_time=(
                            fixture.kickoff_time
                        ),
                        home_history_matches=(
                            home_history_count
                        ),
                        away_history_matches=(
                            away_history_count
                        ),
                        home_xg=home_xg,
                        away_xg=away_xg,
                        home_win_probability=(
                            probabilities["home"]
                        ),
                        draw_probability=(
                            probabilities["draw"]
                        ),
                        away_win_probability=(
                            probabilities["away"]
                        ),
                        confidence=max(
                            probability_map.values()
                        ),
                        predicted_result=(
                            predicted_result
                        ),
                        actual_result=actual_result,
                        result_correct=(
                            predicted_result
                            == actual_result
                        ),
                        predicted_home_score=(
                            predicted_home_score
                        ),
                        predicted_away_score=(
                            predicted_away_score
                        ),
                        actual_home_score=(
                            actual_home_score
                        ),
                        actual_away_score=(
                            actual_away_score
                        ),
                        score_correct=(
                            predicted_home_score
                            == actual_home_score
                            and predicted_away_score
                            == actual_away_score
                        ),
                        brier_score=(
                            calculate_brier_score(
                                probabilities,
                                actual_result,
                            )
                        ),
                        log_loss=(
                            calculate_log_loss(
                                probabilities,
                                actual_result,
                            )
                        ),
                        goal_error=round(
                            goal_error,
                            2,
                        ),
                    )
                )

            for evaluation in pending_evaluations:
                db.add(evaluation)
                created += 1

            for fixture in batch:
                update_history(
                    fixture,
                    team_history,
                    home_history,
                    away_history,
                    competition_stats,
                    elo_ratings,
                )

            if created > 0 and created % 100 == 0:
                db.commit()

                print(
                    f"{created} evaluations created"
                )

        db.commit()

        evaluations = (
            db.query(WalkForwardEvaluation)
            .order_by(
                WalkForwardEvaluation
                .kickoff_time.asc()
            )
            .all()
        )

        print_report(
            evaluations,
            skipped,
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
