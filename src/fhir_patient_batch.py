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
from __future__  import annotations
from destinations.fhir.patient_fhir_adapter import (
    deliver_patient_to_fhir,
)

from state.patient_crosswalk import (
    record_patient_crosswalk,
)


from destinations.csv.patient_csv_adapter import (
    export_patients_to_csv,
)
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
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Load one FHIR JSON file once.

    Returns:
        (
            normalized_patients,
            raw_patient_resources
        )

    The same parsed Patient resources can therefore feed
    multiple destination adapters without reopening the
    source JSON file.
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

        return [], []

    print(
        f"{file_path.name}: "
        f"found {len(patient_resources)} "
        "Patient resource(s)"
    )

    normalized_patients = (
        process_patients(
            patient_resources,
            source_file=file_path,
        )
    )

    return (
        normalized_patients,
        patient_resources,
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
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Export normalized Patient records to CSV.",
    )

    parser.add_argument(
        "--csv-profile",
        type=Path,
        default=Path("config/epic_patient_csv_profile.json"),
        help=(
            "CSV profile JSON file. "
            "Default: config/epic_patient_csv_profile.json"
        ),
    )

    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("data/output"),
        help=(
            "Directory for CSV output. "
            "Default: data/output"
        ),
    )  

    parser.add_argument(
        "--hapi",
        action="store_true",
        help=(
            "Deliver Patient resources "
            "to HAPI FHIR."
        ),
    )

    parser.add_argument(
        "--hapi-base-url",
        default="http://localhost:8080/fhir",
        help=(
            "FHIR base URL. "
            "Default: http://localhost:8080/fhir"
        ),
    )

    parser.add_argument(
        "--source-system",
        default="synthea",
        help=(
            "Logical source system name. "
            "Default: synthea"
        ),
    )

    parser.add_argument(
        "--crosswalk-db",
        type=Path,
        default=Path(
            "data/state/patient_crosswalk.sqlite3"
        ),
        help=(
            "Patient crosswalk SQLite database."
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
    all_patients = []
    all_raw_patients = []

    for file_path in files:
        try:
            patients, raw_patients = process_file(
                file_path
            )
            total_patients += len(
                patients
            )

            all_patients.extend(
                patients
            )

            all_raw_patients.extend(
                raw_patients
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

    if args.csv and all_patients:
        try:
            output_path = export_patients_to_csv(
                patients=all_patients,
                profile_path=args.csv_profile,
                output_directory=args.csv_output,
            )

            print(
                f"\nCSV output created: "
                f"{output_path}"
            )

        except Exception as exc:
            print(
                f"\nCSV export FAILED: {exc}"
            )

            return 1

    # HAPI export
    if args.hapi and all_raw_patients:

        print(
            "\nFHIR Patient delivery"
        )
        print(
            "---------------------"
        )

        delivered_count = 0

        for raw_patient, normalized_patient in zip(
            all_raw_patients,
            all_patients,
        ):
            try:
                (
                    destination_patient_id,
                    http_status,
                ) = deliver_patient_to_fhir(
                    patient=raw_patient,
                    source_system=args.source_system,
                    base_url=args.hapi_base_url,
                )

                record_patient_crosswalk(
                    args.crosswalk_db,
                    source_system=args.source_system,
                    source_patient_id=(
                        normalized_patient[
                            "source_fhir_patient_id"
                        ]
                    ),
                    source_mrn=(
                        normalized_patient[
                            "source_mrn"
                        ]
                    ),
                    source_mrn_system=(
                        normalized_patient[
                            "mrn_system"
                        ]
                    ),
                    destination_system="HAPI",
                    destination_base_url=(
                        args.hapi_base_url
                    ),
                    destination_patient_id=(
                        destination_patient_id
                    ),
                )

                delivered_count += 1

                print(
                    "  "
                    f"{normalized_patient['source_fhir_patient_id']}"
                    " -> "
                    f"Patient/{destination_patient_id}"
                    f" (HTTP {http_status})"
                )

            except Exception as exc:
                print(
                    "  FAILED "
                    f"{normalized_patient['source_fhir_patient_id']}: "
                    f"{exc}"
                )

        print(
            f"\nFHIR Patients delivered: "
            f"{delivered_count}"
        )


    # Final summary
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