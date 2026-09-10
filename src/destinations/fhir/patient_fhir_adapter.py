from __future__ import annotations

from typing import Any

import requests

from fhir.processors.patient_processor import (
    prepare_patient_for_fhir_destination,
    source_patient_identifier_system,
)


class PatientFhirAdapterError(Exception):
    """Raised when Patient delivery to a FHIR destination fails."""


def extract_destination_patient_id(
    response: requests.Response,
) -> str:
    """
    Extract destination Patient.id from a FHIR response.

    Prefer the response body. Fall back to the Location header.
    """

    try:
        body = response.json()

        if (
            isinstance(body, dict)
            and body.get("resourceType") == "Patient"
            and body.get("id")
        ):
            return str(body["id"])

    except ValueError:
        pass

    location = (
        response.headers.get("Location")
        or response.headers.get("Content-Location")
    )

    if location:
        clean_location = location.split("/_history/")[0].rstrip("/")
        destination_id = clean_location.split("/")[-1]

        if destination_id:
            return destination_id

    raise PatientFhirAdapterError(
        "FHIR destination returned success but "
        "Patient.id could not be determined."
    )


def deliver_patient_to_fhir(
    patient: dict[str, Any],
    source_system: str,
    base_url: str,
    timeout_seconds: int = 30,
) -> tuple[str, int]:
    """
    Deliver one source FHIR Patient to a destination FHIR server.

    Uses conditional create based on the En-Route source
    Patient identifier.

    Returns:
        (
            destination_patient_id,
            http_status
        )
    """

    destination_patient = (
        prepare_patient_for_fhir_destination(
            patient,
            source_system,
        )
    )

    source_patient_id = patient.get("id")

    if not source_patient_id:
        raise PatientFhirAdapterError(
            "Source Patient does not contain Patient.id."
        )

    identifier_system = (
        source_patient_identifier_system(
            source_system
        )
    )

    identifier_value = str(
        source_patient_id
    )

    patient_url = (
        base_url.rstrip("/")
        + "/Patient"
    )

    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",

        # FHIR conditional create:
        # only create the Patient when this source
        # identifier does not already exist.
        "If-None-Exist": (
            "identifier="
            f"{identifier_system}|"
            f"{identifier_value}"
        ),
    }

    try:
        response = requests.post(
            patient_url,
            json=destination_patient,
            headers=headers,
            timeout=timeout_seconds,
        )

    except requests.RequestException as exc:
        raise PatientFhirAdapterError(
            f"FHIR Patient delivery failed: {exc}"
        ) from exc

    if response.status_code not in {
        200,
        201,
    }:
        raise PatientFhirAdapterError(
            "FHIR Patient delivery failed. "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    destination_patient_id = (
        extract_destination_patient_id(
            response
        )
    )

    return (
        destination_patient_id,
        response.status_code,
    )