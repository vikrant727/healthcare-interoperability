from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class PatientCsvAdapterError(Exception):
    """Raised when Patient CSV output cannot be generated safely."""


DELIMITER_NAMES = {
    "comma": ",",
    "pipe": "|",
    "tab": "\t",
}


def load_csv_profile(
    profile_path: str | Path,
) -> dict[str, Any]:
    """
    Load and validate a Patient CSV profile.
    """

    profile_path = Path(profile_path)

    if not profile_path.exists():
        raise FileNotFoundError(
            f"CSV profile not found: {profile_path}"
        )

    with profile_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        profile = json.load(file)

    validate_csv_profile(profile)

    return profile


def validate_csv_profile(
    profile: dict[str, Any],
) -> None:
    """
    Validate the CSV profile structure.
    """

    if not isinstance(profile, dict):
        raise PatientCsvAdapterError(
            "CSV profile must be a JSON object."
        )

    columns = profile.get("columns")

    if not isinstance(columns, list) or not columns:
        raise PatientCsvAdapterError(
            "CSV profile must contain a non-empty "
            "'columns' list."
        )

    for column in columns:
        if not isinstance(column, dict):
            raise PatientCsvAdapterError(
                "Each CSV column definition "
                "must be an object."
            )

        if not column.get("source"):
            raise PatientCsvAdapterError(
                "Each CSV column must define "
                "a source field using 'source'."
            )

        if not column.get("header"):
            raise PatientCsvAdapterError(
                "Each CSV column must define "
                "a destination 'header'."
            )


def resolve_delimiter(
    profile: dict[str, Any],
) -> str:
    """
    Resolve the configured delimiter.
    """

    delimiter = profile.get(
        "delimiter",
        "comma",
    )

    if delimiter in DELIMITER_NAMES:
        return DELIMITER_NAMES[delimiter]

    if delimiter == "\\t":
        return "\t"

    if isinstance(delimiter, str) and len(delimiter) == 1:
        return delimiter

    raise PatientCsvAdapterError(
        f"Unsupported CSV delimiter: {delimiter!r}"
    )


def output_fieldnames(
    profile: dict[str, Any],
) -> list[str]:
    """
    Return destination column names in configured order.
    """

    return [
        column["header"]
        for column in profile["columns"]
    ]


def validate_required_fields(
    patient: dict[str, Any],
    profile: dict[str, Any],
) -> None:
    """
    Validate required normalized Patient fields.
    """

    missing_fields = []

    for column in profile["columns"]:

        if not column.get(
            "required",
            False,
        ):
            continue

        source_field = column["source"]

        value = patient.get(
            source_field
        )

        if value is None or value == "":
            missing_fields.append(
                source_field
            )

    if missing_fields:
        raise PatientCsvAdapterError(
            "Patient is missing required "
            "CSV field(s): "
            + ", ".join(missing_fields)
        )


def patient_to_csv_row(
    patient: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert one normalized Patient record into
    a destination-specific CSV row.

    The profile maps:

        normalized Patient field
            ↓
        configured CSV header

    Example:

        source_mrn
            ↓
        MRN
    """

    validate_required_fields(
        patient,
        profile,
    )

    row: dict[str, Any] = {}

    for column in profile["columns"]:

        source_field = column["source"]
        destination_header = column["header"]

        value = patient.get(
            source_field,
            "",
        )

        if value is None:
            value = ""

        row[destination_header] = value

    return row


def write_patients_csv(
    patients: list[dict[str, Any]],
    profile: dict[str, Any],
    output_directory: str | Path,
) -> Path:
    """
    Write normalized Patient records using the
    configured destination CSV profile.
    """

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_filename = profile.get(
        "output_filename",
        "patients.csv",
    )

    output_path = (
        output_directory
        / output_filename
    )

    delimiter = resolve_delimiter(
        profile
    )

    fieldnames = output_fieldnames(
        profile
    )

    include_header = profile.get(
        "include_header",
        True,
    )

    file_exists_and_has_content = (
        output_path.exists()
        and output_path.stat().st_size > 0
    )

    rows = [
        patient_to_csv_row(
            patient,
            profile,
        )
        for patient in patients
    ]

    if not rows:
        return output_path

    with output_path.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            delimiter=delimiter,
            extrasaction="ignore",
        )

        if (
            include_header
            and not file_exists_and_has_content
        ):
            writer.writeheader()

        writer.writerows(
            rows
        )

    print(
        f"  CSV adapter wrote "
        f"{len(rows)} patient(s) "
        f"to {output_path}"
    )

    return output_path


def export_patients_to_csv(
    patients: list[dict[str, Any]],
    profile_path: str | Path,
    output_directory: str | Path,
) -> Path:
    """
    Public entry point for Patient CSV export.
    """

    profile = load_csv_profile(
        profile_path
    )

    return write_patients_csv(
        patients,
        profile,
        output_directory,
    )