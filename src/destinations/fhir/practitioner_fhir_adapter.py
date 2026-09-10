from __future__ import annotations

from typing import Any

import requests


class PractitionerFhirAdapterError(Exception):
    """Raised when Practitioner FHIR operations fail."""


NPI_SYSTEM = "http://hl7.org/fhir/sid/us-npi"


def find_practitioner_by_npi(
    npi: str,
    base_url: str,
    timeout_seconds: int = 30,
) -> str | None:
    """
    Search the destination FHIR server for a Practitioner
    with the supplied NPI.

    Returns:
        destination Practitioner.id when found
        None when no match exists
    """

    practitioner_url = (
        base_url.rstrip("/")
        + "/Practitioner"
    )

    try:
        response = requests.get(
            practitioner_url,
            params={
                "identifier": (
                    f"{NPI_SYSTEM}|{npi}"
                )
            },
            headers={
                "Accept": "application/fhir+json",
            },
            timeout=timeout_seconds,
        )

    except requests.RequestException as exc:
        raise PractitionerFhirAdapterError(
            f"FHIR Practitioner search failed: {exc}"
        ) from exc

    if response.status_code != 200:
        raise PractitionerFhirAdapterError(
            "FHIR Practitioner search failed. "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    try:
        bundle = response.json()

    except ValueError as exc:
        raise PractitionerFhirAdapterError(
            "FHIR Practitioner search returned invalid JSON."
        ) from exc

    entries = bundle.get("entry", [])

    if not entries:
        return None

    practitioners = []

    for entry in entries:
        resource = entry.get("resource", {})

        if (
            resource.get("resourceType")
            == "Practitioner"
            and resource.get("id")
        ):
            practitioners.append(resource)

    if not practitioners:
        return None

    if len(practitioners) > 1:
        raise PractitionerFhirAdapterError(
            f"Multiple destination Practitioners found "
            f"for NPI {npi}."
        )

    return str(
        practitioners[0]["id"]
    )


def extract_destination_practitioner_id(
    response: requests.Response,
) -> str:
    """
    Extract destination Practitioner.id from a FHIR response.

    Prefer the response body. Fall back to the Location header.
    """

    try:
        body = response.json()

        if (
            isinstance(body, dict)
            and body.get("resourceType")
            == "Practitioner"
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
        clean_location = (
            location
            .split("/_history/")[0]
            .rstrip("/")
        )

        destination_id = (
            clean_location.split("/")[-1]
        )

        if destination_id:
            return destination_id

    raise PractitionerFhirAdapterError(
        "FHIR destination returned success but "
        "Practitioner.id could not be determined."
    )


def create_practitioner(
    practitioner: dict[str, Any],
    base_url: str,
    timeout_seconds: int = 30,
) -> tuple[str, int]:
    """
    Create one Practitioner at the destination FHIR server.

    This function is called only after NPI matching has
    determined that no destination Practitioner exists.

    Returns:
        (
            destination_practitioner_id,
            http_status
        )
    """

    if (
        practitioner.get("resourceType")
        != "Practitioner"
    ):
        raise PractitionerFhirAdapterError(
            "Expected FHIR Practitioner resource."
        )

    practitioner_url = (
        base_url.rstrip("/")
        + "/Practitioner"
    )

    try:
        response = requests.post(
            practitioner_url,
            json=practitioner,
            headers={
                "Content-Type":
                    "application/fhir+json",
                "Accept":
                    "application/fhir+json",
            },
            timeout=timeout_seconds,
        )

    except requests.RequestException as exc:
        raise PractitionerFhirAdapterError(
            f"FHIR Practitioner creation failed: {exc}"
        ) from exc

    if response.status_code not in {
        200,
        201,
    }:
        raise PractitionerFhirAdapterError(
            "FHIR Practitioner creation failed. "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    destination_practitioner_id = (
        extract_destination_practitioner_id(
            response
        )
    )

    return (
        destination_practitioner_id,
        response.status_code,
    )