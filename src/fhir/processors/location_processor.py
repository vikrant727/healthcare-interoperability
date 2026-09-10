from __future__ import annotations

from typing import Any


def process_location(
    resource: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize a single already-classified FHIR Location resource.

    MVP scope:
    - extract source Location id
    - extract first identifier
    - preserve basic identifying details
    - no destination matching or creation here
    """

    if not isinstance(resource, dict):
        raise ValueError(
            "Location resource must be a dictionary"
        )

    if resource.get("resourceType") != "Location":
        raise ValueError(
            f"Expected Location resource, got "
            f"{resource.get('resourceType')}"
        )

    identifiers = resource.get("identifier", [])
    identifier = identifiers[0] if identifiers else {}

    normalized = {
        "source_fhir_location_id": resource.get("id"),
        "source_identifier_system": identifier.get("system"),
        "source_identifier_value": identifier.get("value"),
        "name": resource.get("name"),
        "status": resource.get("status"),
    }

    return normalized