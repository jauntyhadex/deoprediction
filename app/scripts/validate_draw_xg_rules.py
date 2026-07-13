from dataclasses import dataclass

from app.database import model_loader
from app.database.connection import SessionLocal
from app.models.walk_forward_evaluation import (
    WalkForwardEvaluation,
)


TRAIN_RATIO = 0.60
VALIDATION_RATIO = 0.20

MINIMUM_DRAW_PREDICTIONS = 20
MINIMUM_DRAW_PRECISION = 28.0

MAXIMUM_VALIDATION_ACCURACY_DROP = 1.0

MINIMUM_DRAW_PROBABILITIES = [
    20.0,
    22.0,
    24.0,
    25.0,
    26.0,
    27.0,
    28.0,
    29.0,
]

MAXIMUM_TOTAL_XG_VALUES = [
    2.4,
    2.6,
    2.8,
    3.0,
    3.2,
]

MAXIMUM_XG_GAPS = [
    0.15,
    0.25,
    0.35,
    0.50,
    0.75,
]

MAXIMUM_LEADER_GAPS = [
    10.0,
    15.0,
    20.0,
    25.0,
    30.0,
]


@dataclass
class DrawRule:

    minimum_draw_probability: float
    maximum_total_xg: float
    maximum_xg_gap: float
    maximum_leader_gap: float


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


def get_baseline_result(
    row,
) -> str:

    probabilities = get_probabilities(
        row
    )

    return max(
        probabilities,
        key=probabilities.get,
    )


def get_total_xg(
    row,
) -> float:

    return (
        float(row.home_xg or 0)
        + float(row.away_xg or 0)
    )


def get_xg_gap(
    row,
) -> float:

    return abs(
        float(row.home_xg or 0)
        - float(row.away_xg or 0)
    )


def get_leader_gap(
    row,
) -> float:

    probabilities = get_probabilities(
        row
    )

    strongest_side = max(
        probabilities["HOME"],
        probabilities["AWAY"],
    )

    return (
        strongest_side
        - probabilities["DRAW"]
    )


def predict_result(
    row,
    rule: DrawRule | None,
) -> str:

    baseline_result = (
        get_baseline_result(row)
    )

    if rule is None:
        return baseline_result

    probabilities = get_probabilities(
        row
    )

    draw_probability = (
        probabilities["DRAW"]
    )

    total_xg = get_total_xg(
        row
    )

    xg_gap = get_xg_gap(
        row
    )

    leader_gap = get_leader_gap(
        row
    )

    draw_candidate = (
        draw_probability
        >= rule.minimum_draw_probability
        and total_xg
        <= rule.maximum_total_xg
        and xg_gap
        <= rule.maximum_xg_gap
        and leader_gap
        <= rule.maximum_leader_gap
    )

    if draw_candidate:
        return "DRAW"

    return baseline_result


def evaluate(
    rows,
    rule: DrawRule | None,
) -> dict:

    actual_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    predicted_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    correct_counts = {
        "HOME": 0,
        "DRAW": 0,
        "AWAY": 0,
    }

    total_correct = 0

    for row in rows:

        actual_result = (
            row.actual_result
        )

        predicted_result = (
            predict_result(
                row=row,
                rule=rule,
            )
        )

        if (
            actual_result
            not in actual_counts
        ):
            continue

        actual_counts[
            actual_result
        ] += 1

        predicted_counts[
            predicted_result
        ] += 1

        if (
            predicted_result
            == actual_result
        ):

            total_correct += 1

            correct_counts[
                actual_result
            ] += 1

    home_recall = percentage(
        correct_counts["HOME"],
        actual_counts["HOME"],
    )

    draw_recall = percentage(
        correct_counts["DRAW"],
        actual_counts["DRAW"],
    )

    away_recall = percentage(
        correct_counts["AWAY"],
        actual_counts["AWAY"],
    )

    macro_recall = round(
        (
            home_recall
            + draw_recall
            + away_recall
        ) / 3,
        2,
    )

    predicted_draws = (
        predicted_counts["DRAW"]
    )

    correct_draws = (
        correct_counts["DRAW"]
    )

    draw_precision = percentage(
        correct_draws,
        predicted_draws,
    )

    actual_draw_rate = percentage(
        actual_counts["DRAW"],
        len(rows),
    )

    return {
        "fixtures": len(rows),
        "correct": total_correct,
        "accuracy": percentage(
            total_correct,
            len(rows),
        ),
        "home_recall": home_recall,
        "draw_recall": draw_recall,
        "away_recall": away_recall,
        "macro_recall": macro_recall,
        "predicted_home": (
            predicted_counts["HOME"]
        ),
        "predicted_draw": (
            predicted_counts["DRAW"]
        ),
        "predicted_away": (
            predicted_counts["AWAY"]
        ),
        "correct_draws": correct_draws,
        "draw_precision": draw_precision,
        "actual_draw_rate": (
            actual_draw_rate
        ),
    }


def generate_rules() -> list[DrawRule]:

    rules = []

    for minimum_draw_probability in (
        MINIMUM_DRAW_PROBABILITIES
    ):

        for maximum_total_xg in (
            MAXIMUM_TOTAL_XG_VALUES
        ):

            for maximum_xg_gap in (
                MAXIMUM_XG_GAPS
            ):

                for maximum_leader_gap in (
                    MAXIMUM_LEADER_GAPS
                ):

                    rules.append(
                        DrawRule(
                            minimum_draw_probability=(
                                minimum_draw_probability
                            ),
                            maximum_total_xg=(
                                maximum_total_xg
                            ),
                            maximum_xg_gap=(
                                maximum_xg_gap
                            ),
                            maximum_leader_gap=(
                                maximum_leader_gap
                            ),
                        )
                    )

    return rules


def select_rule(
    validation_rows,
) -> tuple[
    DrawRule | None,
    dict,
    dict | None,
]:

    baseline = evaluate(
        rows=validation_rows,
        rule=None,
    )

    candidates = []

    for rule in generate_rules():

        result = evaluate(
            rows=validation_rows,
            rule=rule,
        )

        accuracy_drop = (
            baseline["accuracy"]
            - result["accuracy"]
        )

        macro_recall_gain = (
            result["macro_recall"]
            - baseline["macro_recall"]
        )

        if (
            result["predicted_draw"]
            < MINIMUM_DRAW_PREDICTIONS
        ):
            continue

        if (
            result["draw_precision"]
            < MINIMUM_DRAW_PRECISION
        ):
            continue

        if (
            accuracy_drop
            > MAXIMUM_VALIDATION_ACCURACY_DROP
        ):
            continue

        if macro_recall_gain <= 0:
            continue

        candidates.append(
            (
                rule,
                result,
            )
        )

    if not candidates:

        return (
            None,
            baseline,
            None,
        )

    candidates.sort(
        key=lambda item: (
            item[1]["macro_recall"],
            item[1]["draw_recall"],
            item[1]["accuracy"],
            item[1]["draw_precision"],
            -item[1]["predicted_draw"],
        ),
        reverse=True,
    )

    selected_rule, selected_result = (
        candidates[0]
    )

    return (
        selected_rule,
        baseline,
        selected_result,
    )


def print_rule(
    rule: DrawRule,
) -> None:

    print(
        "Minimum draw probability: "
        f"{rule.minimum_draw_probability}%"
    )

    print(
        "Maximum total xG: "
        f"{rule.maximum_total_xg}"
    )

    print(
        "Maximum xG gap: "
        f"{rule.maximum_xg_gap}"
    )

    print(
        "Maximum side-leader gap: "
        f"{rule.maximum_leader_gap}"
    )


def print_result(
    title: str,
    result: dict,
) -> None:

    print()
    print(title)
    print("-" * 70)

    print(
        f"Fixtures: "
        f"{result['fixtures']}"
    )

    print(
        f"Correct: "
        f"{result['correct']}"
    )

    print(
        f"Accuracy: "
        f"{result['accuracy']}%"
    )

    print(
        "Recall: "
        f"HOME={result['home_recall']}% | "
        f"DRAW={result['draw_recall']}% | "
        f"AWAY={result['away_recall']}%"
    )

    print(
        f"Macro recall: "
        f"{result['macro_recall']}%"
    )

    print(
        "Predictions: "
        f"HOME={result['predicted_home']} | "
        f"DRAW={result['predicted_draw']} | "
        f"AWAY={result['predicted_away']}"
    )

    print(
        f"Correct draw predictions: "
        f"{result['correct_draws']}"
    )

    print(
        f"Draw precision: "
        f"{result['draw_precision']}%"
    )

    print(
        f"Actual draw rate: "
        f"{result['actual_draw_rate']}%"
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

        if len(rows) < 300:

            raise RuntimeError(
                "Not enough walk-forward "
                "evaluations."
            )

        training_end = int(
            len(rows)
            * TRAIN_RATIO
        )

        validation_end = int(
            len(rows)
            * (
                TRAIN_RATIO
                + VALIDATION_RATIO
            )
        )

        training_rows = rows[
            :training_end
        ]

        validation_rows = rows[
            training_end:validation_end
        ]

        test_rows = rows[
            validation_end:
        ]

        print(
            "\nDRAW XG RULE VALIDATION"
        )

        print("=" * 70)

        print(
            f"Total evaluations: "
            f"{len(rows)}"
        )

        print(
            f"Training rows: "
            f"{len(training_rows)}"
        )

        print(
            f"Validation rows: "
            f"{len(validation_rows)}"
        )

        print(
            f"Test rows: "
            f"{len(test_rows)}"
        )

        (
            selected_rule,
            validation_baseline,
            validation_selected,
        ) = select_rule(
            validation_rows
        )

        print_result(
            "VALIDATION BASELINE",
            validation_baseline,
        )

        if selected_rule is None:

            print()
            print(
                "NO VALIDATION RULE PASSED"
            )

            print(
                "No draw rule met the minimum "
                "accuracy, precision, recall, "
                "and sample-size requirements."
            )

            print()
            print(
                "DRAW XG VALIDATION FAILED"
            )

            return

        print()
        print(
            "SELECTED DRAW RULE"
        )

        print("-" * 70)

        print_rule(
            selected_rule
        )

        print_result(
            "SELECTED VALIDATION RESULT",
            validation_selected,
        )

        test_baseline = evaluate(
            rows=test_rows,
            rule=None,
        )

        test_selected = evaluate(
            rows=test_rows,
            rule=selected_rule,
        )

        print_result(
            "OUT-OF-SAMPLE BASELINE",
            test_baseline,
        )

        print_result(
            "OUT-OF-SAMPLE DRAW RULE",
            test_selected,
        )

        accuracy_change = round(
            test_selected["accuracy"]
            - test_baseline["accuracy"],
            2,
        )

        macro_recall_change = round(
            test_selected["macro_recall"]
            - test_baseline["macro_recall"],
            2,
        )

        draw_recall_change = round(
            test_selected["draw_recall"]
            - test_baseline["draw_recall"],
            2,
        )

        print()
        print(
            "OUT-OF-SAMPLE CHANGE"
        )

        print("-" * 70)

        print(
            f"Accuracy change: "
            f"{accuracy_change:+.2f}%"
        )

        print(
            f"Macro-recall change: "
            f"{macro_recall_change:+.2f}%"
        )

        print(
            f"Draw-recall change: "
            f"{draw_recall_change:+.2f}%"
        )

        print(
            f"Draw precision: "
            f"{test_selected['draw_precision']}%"
        )

        passed = (
            test_selected["predicted_draw"]
            >= MINIMUM_DRAW_PREDICTIONS
            and test_selected["draw_precision"]
            >= MINIMUM_DRAW_PRECISION
            and accuracy_change >= -1.0
            and macro_recall_change > 0
            and draw_recall_change > 0
        )

        if passed:

            print()
            print(
                "DRAW XG VALIDATION PASSED"
            )

        else:

            print()
            print(
                "DRAW XG VALIDATION FAILED"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()