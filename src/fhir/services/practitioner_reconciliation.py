from __future__ import annotations

from typing import Any

from crosswalk import ResourceCrosswalk

from destinations.fhir.practitioner_fhir_adapter import (
    create_practitioner,
    find_practitioner_by_npi,
)

from fhir.processors.practitioner_processor import (
    process_practitioner,
)


def record_practitioner_crosswalk(
    *,
    crosswalk: ResourceCrosswalk,
    normalized: dict[str, Any],
    source_system: str,
    destination_system: str,
    destination_practitioner_id: str,
) -> None:
    """
    Record the source Practitioner to destination Practitioner mapping.
    """

    crosswalk.upsert(
        source_system=source_system,
        resource_type="Practitioner",
        source_identifier_system=(
            normalized.get("source_identifier_system")
        ),
        source_identifier_value=(
            normalized.get("source_identifier_value")
        ),
        source_resource_id=(
            normalized.get(
                "source_fhir_practitioner_id"
            )
        ),
        destination_system=destination_system,
        destination_resource_type="Practitioner",
        destination_resource_id=(
            destination_practitioner_id
        ),
    )


def reconcile_practitioner(
    resource: dict[str, Any],
    *,
    base_url: str,
    practitioner_config: dict[str, Any],
    source_system: str,
    destination_system: str,
) -> dict[str, Any]:
    """
    Reconcile one source Practitioner against a FHIR destination.

    Flow:
    1. Normalize the source Practitioner.
    2. Extract the NPI.
    3. Search the destination for the same NPI.
    4. If found, map to the existing destination Practitioner.
    5. If not found:
       - CREATE -> create a destination Practitioner.
       - DEFAULT -> map to the configured default Practitioner.
    6. Record the source-to-destination crosswalk.
    """

    normalized = process_practitioner(
        resource
    )

    npi = normalized.get(
        "source_identifier_value"
    )

    if not npi:
        raise ValueError(
            "Source Practitioner does not contain an NPI."
        )

    crosswalk = ResourceCrosswalk()

    # --------------------------------------------------
    # Always search destination by NPI first
    # --------------------------------------------------

    destination_practitioner_id = (
        find_practitioner_by_npi(
            npi=npi,
            base_url=base_url,
        )
    )

    # --------------------------------------------------
    # Existing destination Practitioner found
    # --------------------------------------------------

    if destination_practitioner_id:
        destination_practitioner_id = str(
            destination_practitioner_id
        )

        record_practitioner_crosswalk(
            crosswalk=crosswalk,
            normalized=normalized,
            source_system=source_system,
            destination_system=destination_system,
            destination_practitioner_id=(
                destination_practitioner_id
            ),
        )

        return {
            "action": "MATCHED",
            "destination_practitioner_id": (
                destination_practitioner_id
            ),
            "normalized": normalized,
        }

    # --------------------------------------------------
    # No NPI match
    # --------------------------------------------------

    not_found_action = str(
        practitioner_config.get(
            "not_found_action",
            "CREATE",
        )
    ).upper()

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    if not_found_action == "CREATE":
        (
            destination_practitioner_id,
            http_status,
        ) = create_practitioner(
            practitioner=resource,
            base_url=base_url,
        )

        destination_practitioner_id = str(
            destination_practitioner_id
        )

        record_practitioner_crosswalk(
            crosswalk=crosswalk,
            normalized=normalized,
            source_system=source_system,
            destination_system=destination_system,
            destination_practitioner_id=(
                destination_practitioner_id
            ),
        )

        return {
            "action": "CREATED",
            "destination_practitioner_id": (
                destination_practitioner_id
            ),
            "http_status": http_status,
            "normalized": normalized,
        }

    # --------------------------------------------------
    # DEFAULT
    # --------------------------------------------------

    if not_found_action == "DEFAULT":
        default_mapping = (
            practitioner_config.get(
                "default_mapping",
                {},
            )
        )

        destination_practitioner_id = (
            default_mapping.get(
                "destination_practitioner_id"
            )
        )

        if not destination_practitioner_id:
            raise ValueError(
                "Practitioner not_found_action is DEFAULT "
                "but no destination_practitioner_id "
                "is configured."
            )

        destination_practitioner_id = str(
            destination_practitioner_id
        )

        record_practitioner_crosswalk(
            crosswalk=crosswalk,
            normalized=normalized,
            source_system=source_system,
            destination_system=destination_system,
            destination_practitioner_id=(
                destination_practitioner_id
            ),
        )

        return {
            "action": "DEFAULTED",
            "destination_practitioner_id": (
                destination_practitioner_id
            ),
            "normalized": normalized,
        }

    # --------------------------------------------------
    # Invalid configuration
    # --------------------------------------------------

    raise ValueError(
        "Unsupported Practitioner "
        f"not_found_action: {not_found_action}"
    )