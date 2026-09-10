from __future__ import annotations

from typing import Any


def process_organization(
    resource: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize a single already-classified FHIR Organization resource.

    MVP scope:
    - extract source Organization id
    - extract first identifier
    - preserve basic identifying details
    - no destination matching or creation here
    """

    if not isinstance(resource, dict):
        raise ValueError(
            "Organization resource must be a dictionary"
        )

    if resource.get("resourceType") != "Organization":
        raise ValueError(
            f"Expected Organization resource, got "
            f"{resource.get('resourceType')}"
        )

    identifiers = resource.get("identifier", [])
    identifier = identifiers[0] if identifiers else {}

    normalized = {
        "source_fhir_organization_id": resource.get("id"),
        "source_identifier_system": identifier.get("system"),
        "source_identifier_value": identifier.get("value"),
        "name": resource.get("name"),
        "active": resource.get("active"),
    }

    return normalized