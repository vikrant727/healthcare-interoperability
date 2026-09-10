from __future__ import annotations

from typing import Any

from crosswalk import ResourceCrosswalk

from fhir.processors.location_processor import (
    process_location,
)


def map_location(
    resource: dict[str, Any],
    *,
    location_config: dict[str, Any],
    source_system: str,
    destination_system: str,
) -> dict[str, Any]:
    """
    Map a source Location to the configured destination Location.

    MVP behavior:
    - DEFAULT mapping only
    - no destination search
    - no Location creation
    - write source-to-destination crosswalk
    """

    normalized = process_location(resource)

    mapping_mode = str(
        location_config.get("mapping_mode", "DEFAULT")
    ).upper()

    if mapping_mode != "DEFAULT":
        raise ValueError(
            f"Unsupported Location mapping_mode: {mapping_mode}"
        )

    default_mapping = location_config.get(
        "default_mapping", {}
    )

    destination_location_id = default_mapping.get(
        "destination_location_id"
    )

    if not destination_location_id:
        raise ValueError(
            "Location mapping_mode is DEFAULT "
            "but no destination_location_id is configured."
        )

    destination_location_id = str(
        destination_location_id
    )

    crosswalk = ResourceCrosswalk()

    crosswalk.upsert(
        source_system=source_system,
        resource_type="Location",
        source_identifier_system=normalized.get(
            "source_identifier_system"
        ),
        source_identifier_value=normalized.get(
            "source_identifier_value"
        ),
        source_resource_id=normalized.get(
            "source_fhir_location_id"
        ),
        destination_system=destination_system,
        destination_resource_type="Location",
        destination_resource_id=destination_location_id,
    )

    return {
        "action": "DEFAULTED",
        "destination_location_id": destination_location_id,
        "normalized": normalized,
    }