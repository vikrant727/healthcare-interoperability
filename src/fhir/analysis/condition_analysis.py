from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any
from fhir.processors.condition_classifier import ConditionClassifier
from datetime import datetime

def analyze_conditions(
    resources,
    output_path=None,
):
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_path = (
            Path("data")
            / "analysis"
            / f"condition_analysis_{timestamp}.csv"
        )
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

def _extract_patient_id(
    resource: dict[str, Any],
) -> str | None:

    reference = (
        resource
        .get("subject", {})
        .get("reference")
    )

    if not reference:
        return None

    if reference.startswith("urn:uuid:"):
        return reference.removeprefix("urn:uuid:")

    if reference.startswith("Patient/"):
        return reference.split("/", 1)[1]

    return reference


def analyze_conditions(
    resources: list[dict[str, Any]],
    *,
    output_path: str | Path | None = None,
) -> dict[str, int]:
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_path = (
            Path("data")
            / "analysis"
            / f"condition_analysis_{timestamp}.csv"
        )
    else:
        output_path = Path(output_path)
        
    classifier = ConditionClassifier()

    summary = {
        "PROBLEM": 0,
        "REVIEW": 0,
    }

    distinct_codes = defaultdict(int)
    csv_rows = []

    for item in resources:

        # Allows us to carry source filename with the resource.
        if isinstance(item, tuple):
            source_file, resource = item
        else:
            source_file = ""
            resource = item

        result = classifier.classify(resource)

        classification = result["classification"]
        code_system = result.get("code_system")
        code = result.get("code")
        display = result.get("display")
        review_reason = result.get("review_reason", "")

        summary[classification] += 1

        key = (
            classification,
            code,
            display,
        )

        distinct_codes[key] += 1

        csv_rows.append(
            {
                "source_file": source_file,
                "source_condition_id": resource.get("id"),
                "source_patient_id": _extract_patient_id(
                    resource
                ),
                "code_system": code_system,
                "code": code,
                "display": display,
                "classification": classification,
                "review_reason": review_reason,
            }
        )

    print("\nCONDITION CLASSIFICATION")
    print("------------------------")

    for classification in [
        "PROBLEM",
        "REVIEW",
    ]:

        print(f"\n{classification}")

        rows = [
            (code, display, count)
            for (
                row_classification,
                code,
                display,
            ), count in distinct_codes.items()
            if row_classification == classification
        ]

        rows.sort(
            key=lambda row: (
                -row[2],
                row[1] or "",
            )
        )

        if not rows:
            print("  none")
            continue

        for code, display, count in rows:
            print(
                f"  {count:>3}  "
                f"{code or '<no-code>':<18} "
                f"{display or '<no display>'}"
            )

    print(
        "\nCondition totals -> "
        f"PROBLEM={summary['PROBLEM']}, "
        f"REVIEW={summary['REVIEW']}"
    )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        fieldnames = [
            "source_file",
            "source_condition_id",
            "source_patient_id",
            "code_system",
            "code",
            "display",
            "classification",
            "review_reason",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(csv_rows)

    print(
        f"\nCondition analysis CSV written to: "
        f"{output_path}"
    )

    return summary