import subprocess
import sys
import time


STEPS = [
    (
        "Import and update fixtures",
        "app.scripts.import_fixtures",
    ),
    (
        "Rebuild walk-forward validation",
        "app.scripts.walk_forward_backtest",
    ),
    (
        "Rebuild prediction pipeline",
        "app.scripts.rebuild_prediction_pipeline",
    ),
    (
        "Run API smoke test",
        "app.scripts.check_api",
    ),
    (
        "Run authentication smoke test",
        "app.scripts.check_auth",
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

    started_at = time.time()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            module_name,
        ],
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
        "DEOPREDICTION DATA REFRESH"
    )

    print("=" * 70)

    print(
        f"Total steps: "
        f"{total_steps}"
    )

    started_at = time.time()

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

    duration = round(
        time.time() - started_at,
        2,
    )

    print()
    print("=" * 70)
    print(
        "FULL DATA REFRESH PASSED"
    )
    print(
        f"Total duration: "
        f"{duration} seconds"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
