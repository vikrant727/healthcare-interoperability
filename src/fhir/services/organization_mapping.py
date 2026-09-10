from __future__ import annotations

from typing import Any

from crosswalk import ResourceCrosswalk

from fhir.processors.organization_processor import (
    process_organization,
)


def map_organization(
    resource: dict[str, Any],
    *,
    organization_config: dict[str, Any],
    source_system: str,
    destination_system: str,
) -> dict[str, Any]:
    """
    Map a source Organization to the configured destination Organization.

    MVP behavior:
    - DEFAULT mapping only
    - no destination search
    - no Organization creation
    - write source-to-destination crosswalk
    """

    normalized = process_organization(resource)

    mapping_mode = str(
        organization_config.get("mapping_mode", "DEFAULT")
    ).upper()

    if mapping_mode != "DEFAULT":
        raise ValueError(
            f"Unsupported Organization mapping_mode: {mapping_mode}"
        )

    default_mapping = organization_config.get(
        "default_mapping", {}
    )

    destination_organization_id = default_mapping.get(
        "destination_organization_id"
    )

    if not destination_organization_id:
        raise ValueError(
            "Organization mapping_mode is DEFAULT "
            "but no destination_organization_id is configured."
        )

    destination_organization_id = str(
        destination_organization_id
    )

    crosswalk = ResourceCrosswalk()

    crosswalk.upsert(
        source_system=source_system,
        resource_type="Organization",
        source_identifier_system=normalized.get(
            "source_identifier_system"
        ),
        source_identifier_value=normalized.get(
            "source_identifier_value"
        ),
        source_resource_id=normalized.get(
            "source_fhir_organization_id"
        ),
        destination_system=destination_system,
        destination_resource_type="Organization",
        destination_resource_id=destination_organization_id,
    )

    return {
        "action": "DEFAULTED",
        "destination_organization_id": (
            destination_organization_id
        ),
        "normalized": normalized,
    }