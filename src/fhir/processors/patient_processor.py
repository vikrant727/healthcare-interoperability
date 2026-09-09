from __future__ import annotations

import copy
from typing import Any


class PatientProcessingError(Exception):
    """Raised when a Patient resource cannot be processed safely."""


def identifier_type_codes(identifier: dict[str, Any]) -> set[str]:
    """
    Return identifier type codes from a FHIR Identifier.

    Example:
        Patient.identifier.type.coding.code == "MR"
    """
    return {
        coding.get("code", "")
        for coding in identifier.get("type", {}).get("coding", [])
        if coding.get("code")
    }


def find_mrn(patient: dict[str, Any]) -> tuple[str, str]:
    """
    Find an explicitly typed Medical Record Number.

    Important:
    We do not guess that an arbitrary Patient.identifier is an MRN.
    If no identifier is explicitly typed as MR, return blanks.
    """
    identifiers = patient.get("identifier", [])

    for identifier in identifiers:
        if not isinstance(identifier, dict):
            continue

        if "MR" in identifier_type_codes(identifier):
            return (
                str(identifier.get("value", "")),
                str(identifier.get("system", "")),
            )

    return "", ""


def preferred_name(patient: dict[str, Any]) -> dict[str, Any]:
    """
    Return the official Patient name when available.

    Otherwise return the first available name.
    """
    names = patient.get("name", [])

    if not names:
        return {}

    for name in names:
        if isinstance(name, dict) and name.get("use") == "official":
            return name

    first = names[0]

    return first if isinstance(first, dict) else {}


def first_telecom(
    patient: dict[str, Any],
    system: str,
) -> str:
    """
    Return the first telecom value matching the requested system.

    Examples:
        phone
        email
    """
    for telecom in patient.get("telecom", []):
        if not isinstance(telecom, dict):
            continue

        if telecom.get("system") == system:
            return str(telecom.get("value", ""))

    return ""


def preferred_address(patient: dict[str, Any]) -> dict[str, Any]:
    """
    Return the first available Patient address.

    Address-selection rules can become more sophisticated later
    if business requirements require home/work/temporary preference.
    """
    addresses = patient.get("address", [])

    if not addresses:
        return {}

    first = addresses[0]

    return first if isinstance(first, dict) else {}


def marital_status(patient: dict[str, Any]) -> str:
    """
    Return a human-readable marital status.
    """
    status = patient.get("maritalStatus", {})

    if not isinstance(status, dict):
        return ""

    if status.get("text"):
        return str(status["text"])

    coding = status.get("coding", [])

    if coding and isinstance(coding[0], dict):
        return str(coding[0].get("display", ""))

    return ""


def communication_language(patient: dict[str, Any]) -> str:
    """
    Return the first Patient communication language.
    """
    communications = patient.get("communication", [])

    if not communications:
        return ""

    first_communication = communications[0]

    if not isinstance(first_communication, dict):
        return ""

    language = first_communication.get("language", {})

    if not isinstance(language, dict):
        return ""

    if language.get("text"):
        return str(language["text"])

    coding = language.get("coding", [])

    if coding and isinstance(coding[0], dict):
        return str(coding[0].get("display", ""))

    return ""


def normalize_patient(
    patient: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert a FHIR Patient resource into En-Route's normalized
    Patient representation.

    This representation is destination-neutral.

    It intentionally does NOT contain:
        - source filename
        - file hash
        - processing timestamp
        - destination Patient id

    Those belong to pipeline/audit/destination layers.
    """

    if not isinstance(patient, dict):
        raise PatientProcessingError(
            "Patient resource must be a dictionary."
        )

    if patient.get("resourceType") != "Patient":
        raise PatientProcessingError(
            "Expected FHIR Patient resource, "
            f"found {patient.get('resourceType')!r}."
        )

    name = preferred_name(patient)
    given_names = name.get("given", [])

    if not isinstance(given_names, list):
        given_names = []

    address = preferred_address(patient)

    address_lines = address.get("line", [])

    if not isinstance(address_lines, list):
        address_lines = []

    mrn, mrn_system = find_mrn(patient)

    return {
        "source_fhir_patient_id": str(
            patient.get("id", "")
        ),
        "source_mrn": mrn,
        "mrn_system": mrn_system,
        "family_name": str(
            name.get("family", "")
        ),
        "given_name": (
            str(given_names[0])
            if len(given_names) >= 1
            else ""
        ),
        "middle_name": (
            " ".join(
                str(value)
                for value in given_names[1:]
            )
            if len(given_names) >= 2
            else ""
        ),
        "birth_date": str(
            patient.get("birthDate", "")
        ),
        "gender": str(
            patient.get("gender", "")
        ),
        "phone": first_telecom(
            patient,
            "phone",
        ),
        "email": first_telecom(
            patient,
            "email",
        ),
        "address_line1": (
            str(address_lines[0])
            if len(address_lines) >= 1
            else ""
        ),
        "address_line2": (
            str(address_lines[1])
            if len(address_lines) >= 2
            else ""
        ),
        "city": str(
            address.get("city", "")
        ),
        "state": str(
            address.get("state", "")
        ),
        "postal_code": str(
            address.get("postalCode", "")
        ),
        "country": str(
            address.get("country", "")
        ),
        "marital_status": marital_status(
            patient
        ),
        "language": communication_language(
            patient
        ),
    }


def source_patient_identifier_system(
    source_system: str,
) -> str:
    """
    Create an En-Route identifier namespace used to preserve
    the original source FHIR Patient.id.
    """

    safe_source = "".join(
        character.lower()
        if character.isalnum()
        else "-"
        for character in source_system.strip()
    ).strip("-")

    return (
        "urn:en-route:source:"
        f"{safe_source or 'unknown'}:"
        "patient-id"
    )


def prepare_patient_for_fhir_destination(
    patient: dict[str, Any],
    source_system: str,
) -> dict[str, Any]:
    """
    Prepare a source Patient resource for POST/create to another
    FHIR destination.

    Destination systems should assign their own Patient.id.

    The source Patient.id is therefore removed and preserved as
    an Identifier.

    Existing identifiers such as the source MRN remain intact.
    """

    if patient.get("resourceType") != "Patient":
        raise PatientProcessingError(
            "FHIR destination preparation requires "
            "a Patient resource."
        )

    output_patient = copy.deepcopy(patient)

    source_patient_id = output_patient.pop(
        "id",
        None,
    )

    # Source version metadata should not be presented as
    # destination version metadata.
    meta = output_patient.get("meta")

    if isinstance(meta, dict):
        meta.pop("versionId", None)
        meta.pop("lastUpdated", None)

        if not meta:
            output_patient.pop("meta", None)

    if source_patient_id:
        source_identifier = {
            "system": source_patient_identifier_system(
                source_system
            ),
            "value": str(source_patient_id),
        }

        identifiers = output_patient.setdefault(
            "identifier",
            [],
        )

        already_present = any(
            isinstance(identifier, dict)
            and identifier.get("system")
            == source_identifier["system"]
            and identifier.get("value")
            == source_identifier["value"]
            for identifier in identifiers
        )

        if not already_present:
            identifiers.append(
                source_identifier
            )

    return output_patient


def process_patients(
    patient_resources: list[dict[str, Any]],
    source_file=None,
) -> list[dict[str, Any]]:
    """
    Process Patient resources already extracted and grouped
    by the FHIR intake pipeline.

    The processor does not:
        - open source JSON files
        - scan directories
        - archive files
        - write CSV files
        - call destination APIs

    Returns destination-neutral normalized Patient records.
    """

    processed_patients: list[
        dict[str, Any]
    ] = []

    for patient in patient_resources:
        normalized_patient = normalize_patient(
            patient
        )

        processed_patients.append(
            normalized_patient
        )

    print(
        f"  Patient processor processed "
        f"{len(processed_patients)} patient(s)"
    )

    return processed_patients