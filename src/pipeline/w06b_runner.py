
from pathlib import Path
import json
import csv
from src.pipeline.w06_pipeline import run_pipeline


def main():
    project_root = Path(".").resolve()
    artifacts_dir = project_root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    print("W06B runner iniciado")
    print(f"PROJECT_ROOT: {project_root}")

    report = run_pipeline(project_root)

    report_path = artifacts_dir / "w06b_run_report.json"
    timings_path = artifacts_dir / "w06b_stage_timings.csv"

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    with timings_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["mode", "seconds"])
        writer.writeheader()
        writer.writerows(report["stages"])

    print("Artifacts generados:")
    print(f"- {report_path}")
    print(f"- {timings_path}")

    print("Stage timings:")
    for stage in report["stages"]:
        print(f"- {stage['mode']}: {stage['seconds']} s")

    print("Checks:")
    for k, v in report["checks"].items():
        print(f"- {k}: {v}")

    print("W06B runner finalizado correctamente")


if __name__ == "__main__":
    main()
