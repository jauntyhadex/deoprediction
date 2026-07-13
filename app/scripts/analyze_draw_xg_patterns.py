from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


TOTAL_XG_BANDS = [
    (0.0, 1.5),
    (1.5, 2.0),
    (2.0, 2.5),
    (2.5, 3.0),
    (3.0, 3.5),
    (3.5, 4.0),
    (4.0, 100.0),
]


XG_GAP_BANDS = [
    (0.0, 0.15),
    (0.15, 0.30),
    (0.30, 0.50),
    (0.50, 0.75),
    (0.75, 1.00),
    (1.00, 1.50),
    (1.50, 100.0),
]


TOTAL_XG_THRESHOLDS = [
    1.8,
    2.0,
    2.2,
    2.4,
    2.6,
    2.8,
    3.0,
    3.2,
]


XG_GAP_THRESHOLDS = [
    0.15,
    0.25,
    0.35,
    0.50,
    0.75,
    1.00,
]


MINIMUM_ZONE_FIXTURES = 50


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


def get_home_xg(
    row,
) -> float:

    return float(
        row.home_xg or 0
    )


def get_away_xg(
    row,
) -> float:

    return float(
        row.away_xg or 0
    )


def get_total_xg(
    row,
) -> float:

    return (
        get_home_xg(row)
        + get_away_xg(row)
    )


def get_xg_gap(
    row,
) -> float:

    return abs(
        get_home_xg(row)
        - get_away_xg(row)
    )


def count_draws(
    rows,
) -> int:

    return sum(
        1
        for row in rows
        if row.actual_result == "DRAW"
    )


def print_overall_summary(
    rows,
) -> None:

    draw_rows = [
        row
        for row in rows
        if row.actual_result == "DRAW"
    ]

    non_draw_rows = [
        row
        for row in rows
        if row.actual_result != "DRAW"
    ]

    print(
        "\nOVERALL XG DRAW SUMMARY"
    )

    print("=" * 90)

    print(
        f"Evaluations: "
        f"{len(rows)}"
    )

    print(
        f"Actual draws: "
        f"{len(draw_rows)}"
    )

    print(
        f"Baseline draw rate: "
        f"{percentage(
            len(draw_rows),
            len(rows),
        )}%"
    )

    print(
        "Average total xG: "
        f"draws={average(
            [
                get_total_xg(row)
                for row in draw_rows
            ]
        )} | "
        f"non-draws={average(
            [
                get_total_xg(row)
                for row in non_draw_rows
            ]
        )}"
    )

    print(
        "Average xG gap: "
        f"draws={average(
            [
                get_xg_gap(row)
                for row in draw_rows
            ]
        )} | "
        f"non-draws={average(
            [
                get_xg_gap(row)
                for row in non_draw_rows
            ]
        )}"
    )

    print(
        "Average predicted draw probability: "
        f"draws={average(
            [
                float(
                    row.draw_probability
                    or 0
                )
                for row in draw_rows
            ]
        )}% | "
        f"non-draws={average(
            [
                float(
                    row.draw_probability
                    or 0
                )
                for row in non_draw_rows
            ]
        )}%"
    )


def print_total_xg_bands(
    rows,
) -> None:

    print(
        "\nDRAW RATE BY TOTAL XG"
    )

    print("=" * 90)

    print(
        "Total xG band | Fixtures | "
        "Actual draws | Draw rate | "
        "Average predicted draw probability"
    )

    print("-" * 90)

    for lower, upper in TOTAL_XG_BANDS:

        selected = [
            row
            for row in rows
            if (
                get_total_xg(row) >= lower
                and get_total_xg(row) < upper
            )
        ]

        draws = count_draws(
            selected
        )

        upper_label = (
            "+"
            if upper >= 100
            else f"{upper:.1f}"
        )

        band_label = (
            f"{lower:.1f}+"
            if upper_label == "+"
            else (
                f"{lower:.1f}-"
                f"{upper_label}"
            )
        )

        print(
            f"{band_label:12} | "
            f"{len(selected):8} | "
            f"{draws:12} | "
            f"{percentage(
                draws,
                len(selected),
            ):8.2f}% | "
            f"{average(
                [
                    float(
                        row.draw_probability
                        or 0
                    )
                    for row in selected
                ]
            )}%"
        )


def print_xg_gap_bands(
    rows,
) -> None:

    print(
        "\nDRAW RATE BY XG GAP"
    )

    print("=" * 90)

    print(
        "xG gap band | Fixtures | "
        "Actual draws | Draw rate | "
        "Average predicted draw probability"
    )

    print("-" * 90)

    for lower, upper in XG_GAP_BANDS:

        selected = [
            row
            for row in rows
            if (
                get_xg_gap(row) >= lower
                and get_xg_gap(row) < upper
            )
        ]

        draws = count_draws(
            selected
        )

        upper_label = (
            "+"
            if upper >= 100
            else f"{upper:.2f}"
        )

        band_label = (
            f"{lower:.2f}+"
            if upper_label == "+"
            else (
                f"{lower:.2f}-"
                f"{upper_label}"
            )
        )

        print(
            f"{band_label:12} | "
            f"{len(selected):8} | "
            f"{draws:12} | "
            f"{percentage(
                draws,
                len(selected),
            ):8.2f}% | "
            f"{average(
                [
                    float(
                        row.draw_probability
                        or 0
                    )
                    for row in selected
                ]
            )}%"
        )


def build_candidate_zones(
    rows,
) -> list[dict]:

    total_actual_draws = count_draws(
        rows
    )

    baseline_draw_rate = percentage(
        total_actual_draws,
        len(rows),
    )

    reports = []

    for maximum_total_xg in (
        TOTAL_XG_THRESHOLDS
    ):

        for maximum_xg_gap in (
            XG_GAP_THRESHOLDS
        ):

            selected = [
                row
                for row in rows
                if (
                    get_total_xg(row)
                    <= maximum_total_xg
                    and get_xg_gap(row)
                    <= maximum_xg_gap
                )
            ]

            if (
                len(selected)
                < MINIMUM_ZONE_FIXTURES
            ):
                continue

            draws = count_draws(
                selected
            )

            draw_rate = percentage(
                draws,
                len(selected),
            )

            draw_coverage = percentage(
                draws,
                total_actual_draws,
            )

            fixture_coverage = percentage(
                len(selected),
                len(rows),
            )

            lift = round(
                draw_rate
                - baseline_draw_rate,
                2,
            )

            reports.append(
                {
                    "maximum_total_xg": (
                        maximum_total_xg
                    ),
                    "maximum_xg_gap": (
                        maximum_xg_gap
                    ),
                    "fixtures": len(
                        selected
                    ),
                    "draws": draws,
                    "draw_rate": draw_rate,
                    "draw_coverage": (
                        draw_coverage
                    ),
                    "fixture_coverage": (
                        fixture_coverage
                    ),
                    "lift": lift,
                    "average_draw_probability": (
                        average(
                            [
                                float(
                                    row.draw_probability
                                    or 0
                                )
                                for row in selected
                            ]
                        )
                    ),
                }
            )

    return reports


def print_best_candidate_zones(
    rows,
) -> None:

    reports = build_candidate_zones(
        rows
    )

    reports.sort(
        key=lambda report: (
            report["draw_rate"],
            report["draw_coverage"],
            report["fixtures"],
        ),
        reverse=True,
    )

    print(
        "\nBEST LOW-XG, SMALL-GAP DRAW ZONES"
    )

    print("=" * 110)

    print(
        "Max total xG | Max xG gap | "
        "Fixtures | Draws | Draw rate | "
        "Draw coverage | Fixture coverage | Lift"
    )

    print("-" * 110)

    for report in reports[:20]:

        print(
            f"{report['maximum_total_xg']:12.2f} | "
            f"{report['maximum_xg_gap']:10.2f} | "
            f"{report['fixtures']:8} | "
            f"{report['draws']:5} | "
            f"{report['draw_rate']:8.2f}% | "
            f"{report['draw_coverage']:12.2f}% | "
            f"{report['fixture_coverage']:15.2f}% | "
            f"{report['lift']:+.2f}%"
        )


def print_high_coverage_zones(
    rows,
) -> None:

    reports = build_candidate_zones(
        rows
    )

    reports.sort(
        key=lambda report: (
            report["draw_coverage"],
            report["draw_rate"],
            report["fixtures"],
        ),
        reverse=True,
    )

    print(
        "\nHIGHEST ACTUAL-DRAW COVERAGE ZONES"
    )

    print("=" * 110)

    print(
        "Max total xG | Max xG gap | "
        "Fixtures | Draws | Draw rate | "
        "Draw coverage | Fixture coverage | Lift"
    )

    print("-" * 110)

    for report in reports[:20]:

        print(
            f"{report['maximum_total_xg']:12.2f} | "
            f"{report['maximum_xg_gap']:10.2f} | "
            f"{report['fixtures']:8} | "
            f"{report['draws']:5} | "
            f"{report['draw_rate']:8.2f}% | "
            f"{report['draw_coverage']:12.2f}% | "
            f"{report['fixture_coverage']:15.2f}% | "
            f"{report['lift']:+.2f}%"
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

        if not rows:

            raise RuntimeError(
                "No walk-forward evaluations "
                "were found."
            )

        print_overall_summary(
            rows
        )

        print_total_xg_bands(
            rows
        )

        print_xg_gap_bands(
            rows
        )

        print_best_candidate_zones(
            rows
        )

        print_high_coverage_zones(
            rows
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()