from collections import defaultdict

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.competition import Competition
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


DRAW_PROBABILITY_BANDS = [
    (0.0, 15.0),
    (15.0, 20.0),
    (20.0, 25.0),
    (25.0, 30.0),
    (30.0, 35.0),
    (35.0, 40.0),
    (40.0, 45.0),
    (45.0, 50.0),
    (50.0, 101.0),
]


def percentage(
    numerator: int,
    denominator: int,
) -> float:

    if denominator <= 0:
        return 0.0

    return round(
        numerator / denominator * 100,
        2,
    )


def average(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        4,
    )


def get_probabilities(
    row,
) -> dict[str, float]:

    return {
        "HOME": float(
            row.home_win_probability
            or 0
        ),
        "DRAW": float(
            row.draw_probability
            or 0
        ),
        "AWAY": float(
            row.away_win_probability
            or 0
        ),
    }


def get_leading_side_probability(
    row,
) -> float:

    probabilities = get_probabilities(
        row
    )

    return max(
        probabilities["HOME"],
        probabilities["AWAY"],
    )


def print_overall_report(
    rows,
) -> None:

    actual_draws = [
        row
        for row in rows
        if row.actual_result == "DRAW"
    ]

    non_draws = [
        row
        for row in rows
        if row.actual_result != "DRAW"
    ]

    draw_predicted_highest = [
        row
        for row in rows
        if (
            float(
                row.draw_probability
                or 0
            )
            >= float(
                row.home_win_probability
                or 0
            )
            and float(
                row.draw_probability
                or 0
            )
            >= float(
                row.away_win_probability
                or 0
            )
        )
    ]

    actual_draw_probabilities = [
        float(
            row.draw_probability
            or 0
        )
        for row in actual_draws
    ]

    non_draw_probabilities = [
        float(
            row.draw_probability
            or 0
        )
        for row in non_draws
    ]

    actual_draw_leader_gaps = [
        (
            get_leading_side_probability(
                row
            )
            - float(
                row.draw_probability
                or 0
            )
        )
        for row in actual_draws
    ]

    print(
        "\nOVERALL DRAW ANALYSIS"
    )

    print("=" * 80)

    print(
        f"Evaluations: "
        f"{len(rows)}"
    )

    print(
        f"Actual draws: "
        f"{len(actual_draws)}"
    )

    print(
        f"Actual draw rate: "
        f"{percentage(
            len(actual_draws),
            len(rows),
        )}%"
    )

    print(
        "Fixtures where draw was "
        "the highest probability: "
        f"{len(draw_predicted_highest)}"
    )

    print(
        "Average draw probability "
        "for actual draws: "
        f"{average(
            actual_draw_probabilities
        )}%"
    )

    print(
        "Average draw probability "
        "for non-draws: "
        f"{average(
            non_draw_probabilities
        )}%"
    )

    print(
        "Maximum draw probability: "
        f"{round(
            max(
                [
                    float(
                        row.draw_probability
                        or 0
                    )
                    for row in rows
                ],
                default=0,
            ),
            2,
        )}%"
    )

    print(
        "Average side-leader gap "
        "for actual draws: "
        f"{average(
            actual_draw_leader_gaps
        )} percentage points"
    )


def print_probability_bands(
    rows,
) -> None:

    print(
        "\nDRAW PROBABILITY BANDS"
    )

    print("=" * 80)

    print(
        "Band | Fixtures | Actual draws | "
        "Actual draw rate"
    )

    print("-" * 80)

    for lower, upper in (
        DRAW_PROBABILITY_BANDS
    ):

        band_rows = [
            row
            for row in rows
            if (
                float(
                    row.draw_probability
                    or 0
                )
                >= lower
                and float(
                    row.draw_probability
                    or 0
                )
                < upper
            )
        ]

        actual_draws = sum(
            1
            for row in band_rows
            if row.actual_result == "DRAW"
        )

        upper_label = (
            "100"
            if upper > 100
            else str(int(upper))
        )

        print(
            f"{int(lower):02d}-"
            f"{upper_label}% | "
            f"{len(band_rows)} | "
            f"{actual_draws} | "
            f"{percentage(
                actual_draws,
                len(band_rows),
            )}%"
        )


def print_top_draw_probability_report(
    rows,
) -> None:

    sorted_rows = sorted(
        rows,
        key=lambda row: float(
            row.draw_probability
            or 0
        ),
        reverse=True,
    )

    print(
        "\nTOP DRAW-PROBABILITY COVERAGE"
    )

    print("=" * 80)

    for top_count in [
        25,
        50,
        100,
        200,
        400,
        800,
    ]:

        selected = sorted_rows[
            :top_count
        ]

        if not selected:
            continue

        actual_draws = sum(
            1
            for row in selected
            if row.actual_result == "DRAW"
        )

        minimum_probability = float(
            selected[-1].draw_probability
            or 0
        )

        print(
            f"Top {len(selected)} | "
            f"Minimum draw probability: "
            f"{round(
                minimum_probability,
                2,
            )}% | "
            f"Actual draws: "
            f"{actual_draws} | "
            f"Draw rate: "
            f"{percentage(
                actual_draws,
                len(selected),
            )}%"
        )


def print_leader_gap_report(
    rows,
) -> None:

    print(
        "\nACTUAL DRAWS BY SIDE-LEADER GAP"
    )

    print("=" * 80)

    actual_draw_rows = [
        row
        for row in rows
        if row.actual_result == "DRAW"
    ]

    for maximum_gap in [
        5,
        10,
        15,
        20,
        25,
        30,
    ]:

        selected = [
            row
            for row in rows
            if (
                get_leading_side_probability(
                    row
                )
                - float(
                    row.draw_probability
                    or 0
                )
            )
            <= maximum_gap
        ]

        actual_draws = sum(
            1
            for row in selected
            if row.actual_result == "DRAW"
        )

        detected_draws = sum(
            1
            for row in actual_draw_rows
            if (
                get_leading_side_probability(
                    row
                )
                - float(
                    row.draw_probability
                    or 0
                )
            )
            <= maximum_gap
        )

        print(
            f"Maximum gap {maximum_gap} | "
            f"Selected fixtures: "
            f"{len(selected)} | "
            f"Actual draw rate: "
            f"{percentage(
                actual_draws,
                len(selected),
            )}% | "
            f"Actual-draw coverage: "
            f"{percentage(
                detected_draws,
                len(actual_draw_rows),
            )}%"
        )


def print_competition_report(
    rows,
    competition_names: dict[int, str],
) -> None:

    grouped = defaultdict(list)

    for row in rows:
        grouped[
            row.competition_id
        ].append(row)

    print(
        "\nDRAW ANALYSIS BY COMPETITION"
    )

    print("=" * 80)

    for competition_id, competition_rows in sorted(
        grouped.items(),
        key=lambda item: len(
            item[1]
        ),
        reverse=True,
    ):

        actual_draw_rows = [
            row
            for row in competition_rows
            if row.actual_result == "DRAW"
        ]

        actual_draw_probabilities = [
            float(
                row.draw_probability
                or 0
            )
            for row in actual_draw_rows
        ]

        non_draw_probabilities = [
            float(
                row.draw_probability
                or 0
            )
            for row in competition_rows
            if row.actual_result != "DRAW"
        ]

        name = competition_names.get(
            competition_id,
            f"Competition {competition_id}",
        )

        print()
        print(
            f"{name} "
            f"(ID {competition_id})"
        )

        print(
            f"Evaluations: "
            f"{len(competition_rows)} | "
            f"Actual draws: "
            f"{len(actual_draw_rows)} | "
            f"Draw rate: "
            f"{percentage(
                len(actual_draw_rows),
                len(competition_rows),
            )}%"
        )

        print(
            "Average draw probability: "
            f"actual draws="
            f"{average(
                actual_draw_probabilities
            )}% | "
            f"non-draws="
            f"{average(
                non_draw_probabilities
            )}%"
        )


def main():

    db = SessionLocal()

    try:

        rows = (
            db.query(
                WalkForwardEvaluation
            )
            .order_by(
                WalkForwardEvaluation
                .kickoff_time.asc(),
                WalkForwardEvaluation
                .id.asc(),
            )
            .all()
        )

        competitions = (
            db.query(
                Competition
            )
            .all()
        )

        competition_names = {
            competition.id: (
                competition.name
            )
            for competition in competitions
        }

        if not rows:

            raise RuntimeError(
                "No walk-forward evaluations "
                "were found."
            )

        print_overall_report(
            rows
        )

        print_probability_bands(
            rows
        )

        print_top_draw_probability_report(
            rows
        )

        print_leader_gap_report(
            rows
        )

        print_competition_report(
            rows=rows,
            competition_names=(
                competition_names
            ),
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()