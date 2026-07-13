import subprocess
import sys
import time


STEPS = [
    (
        "Team statistics",
        "app.scripts.generate_team_stats",
    ),
    (
        "Home and away statistics",
        "app.scripts.generate_home_away_stats",
    ),
    (
        "Team forms",
        "app.scripts.generate_team_forms",
    ),
    (
        "Head-to-head statistics",
        "app.scripts.generate_head_to_head",
    ),
    (
        "Elo ratings",
        "app.scripts.generate_elo_ratings",
    ),
    (
        "Strength of schedule",
        "app.scripts.generate_strength_of_schedule",
    ),
    (
        "Team ratings",
        "app.scripts.generate_team_ratings",
    ),
    (
        "Team power ratings",
        "app.scripts.generate_team_power_ratings",
    ),
    (
        "Predictions",
        "app.scripts.generate_predictions",
    ),
    (
        "Prediction markets",
        "app.scripts.generate_prediction_markets",
    ),
    (
        "Prediction picks",
        "app.scripts.generate_prediction_picks",
    ),
    (
        "Quality-gate verification",
        "app.scripts.verify_quality_gate",
    ),
    (
        "Pipeline verification",
        "app.scripts.verify_prediction_pipeline",
    ),
]


def run_step(
    step_number: int,
    total_steps: int,
    title: str,
    module_name: str,
) -> None:

    print()
    print("=" * 70)
    print(
        f"STEP {step_number}/{total_steps}: "
        f"{title}"
    )
    print("=" * 70)

    command = [
        sys.executable,
        "-c",
        (
            "from app.database import model_loader; "
            f"from {module_name} import main; "
            "main()"
        ),
    ]

    started_at = time.time()

    result = subprocess.run(
        command,
        check=False,
    )

    duration = round(
        time.time() - started_at,
        2,
    )

    if result.returncode != 0:

        print()
        print(
            f"FAILED: {title}"
        )

        print(
            f"Exit code: "
            f"{result.returncode}"
        )

        raise SystemExit(
            result.returncode
        )

    print()
    print(
        f"PASSED: {title} "
        f"({duration} seconds)"
    )


def main() -> None:

    total_steps = len(
        STEPS
    )

    print()
    print(
        "DEOPREDICTION FULL PIPELINE REBUILD"
    )

    print("=" * 70)

    print(
        f"Total steps: "
        f"{total_steps}"
    )

    pipeline_started_at = time.time()

    for index, (
        title,
        module_name,
    ) in enumerate(
        STEPS,
        start=1,
    ):

        run_step(
            step_number=index,
            total_steps=total_steps,
            title=title,
            module_name=module_name,
        )

    total_duration = round(
        time.time()
        - pipeline_started_at,
        2,
    )

    print()
    print("=" * 70)
    print(
        "FULL PIPELINE REBUILD PASSED"
    )
    print(
        f"Total duration: "
        f"{total_duration} seconds"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
