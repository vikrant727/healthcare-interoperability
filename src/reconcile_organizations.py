import json
from pathlib import Path

from mapping import ResourceMapping


def load_organizations(source_file):
    with open(
        source_file,
        "r",
        encoding="utf-8"
    ) as f:
        bundle = json.load(f)

    organizations = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Organization":
            continue

        organizations.append(resource)

    return organizations


def reconcile_organizations(
    organizations,
    destination_id,
    mapping
):
    decisions = []

    destination_reference = (
        f"Organization/{destination_id}"
    )

    for organization in organizations:

        source_id = organization.get("id")

        name = organization.get(
            "name",
            ""
        )

        mapping.add_mapping(
            "Organization",
            source_id,
            destination_reference
        )

        decisions.append({
            "source_id": source_id,
            "source_name": name,
            "decision": "MAP_EXISTING",
            "destination": destination_reference
        })

    return decisions