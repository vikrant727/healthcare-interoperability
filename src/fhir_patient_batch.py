#!/usr/bin/env python3

"""
Standalone En-Route FHIR Patient processor test utility.

This is NOT the production intake pipeline.

Production flow:

    main.py
        -> intake router
        -> FHIR pipeline
        -> resource classifier
        -> resource dispatcher
        -> patient processor

This utility exists so developers can test Patient processing
directly against one or more FHIR JSON files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fhir.resource_classifier import (
    load_and_group_fhir_resources,
)

from fhir.processors.patient_processor import (
    process_patients,
)


def process_file(
    file_path: Path,
) -> list[dict[str, Any]]:
    """
    Load one FHIR JSON file using the standard En-Route
    classifier and send any Patient resources to the
    Patient processor.
    """

    grouped_resources = (
        load_and_group_fhir_resources(
            file_path
        )
    )

    patient_resources = (
        grouped_resources.get(
            "Patient",
            [],
        )
    )

    if not patient_resources:
        print(
            f"{file_path.name}: "
            "no Patient resources found"
        )

        return []

    print(
        f"{file_path.name}: "
        f"found {len(patient_resources)} "
        "Patient resource(s)"
    )

    return process_patients(
        patient_resources,
        source_file=file_path,
    )


def print_normalized_patients(
    patients: list[dict[str, Any]],
) -> None:
    """
    Print normalized Patient records for inspection.
    """

    for index, patient in enumerate(
        patients,
        start=1,
    ):
        print(
            f"\nNormalized Patient {index}"
        )
        print("--------------------")

        print(
            json.dumps(
                patient,
                indent=2,
                ensure_ascii=False,
            )
        )


def find_json_files(
    input_path: Path,
) -> list[Path]:
    """
    Accept either:

        - one JSON file
        - a directory containing JSON files
    """

    if input_path.is_file():
        if input_path.suffix.lower() != ".json":
            raise ValueError(
                "Input file must be JSON."
            )

        return [input_path]

    if input_path.is_dir():
        return sorted(
            input_path.glob("*.json")
        )

    raise FileNotFoundError(
        f"Input path not found: {input_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Test En-Route Patient processing "
            "against FHIR JSON files."
        )
    )

    parser.add_argument(
        "input",
        type=Path,
        help=(
            "FHIR JSON file or directory "
            "containing FHIR JSON files"
        ),
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help=(
            "Print normalized Patient "
            "records to the console"
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = args.input.resolve()

    files = find_json_files(
        input_path
    )

    if not files:
        print(
            f"No JSON files found in "
            f"{input_path}"
        )

        return 0

    print(
        f"Found {len(files)} JSON file(s)"
    )

    total_patients = 0

    for file_path in files:
        try:
            patients = process_file(
                file_path
            )

            total_patients += len(
                patients
            )

            if args.show and patients:
                print_normalized_patients(
                    patients
                )

        except (
            json.JSONDecodeError,
            OSError,
            ValueError,
        ) as exc:
            print(
                f"{file_path.name}: "
                f"FAILED - {exc}"
            )

    print(
        "\nPatient processing test complete"
    )

    print(
        f"Total Patient resources processed: "
        f"{total_patients}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )