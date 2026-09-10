import json
from collections import Counter
from pathlib import Path

from fhir.resource_classifier import (
    load_and_group_fhir_resources,
    get_resource_counts,
)
from fhir.resource_dispatcher import dispatch_resources


def run_fhir_pipeline(config):
    """
    Scan configured incoming directory, classify FHIR resources,
    and optionally dispatch them for processing.
    """

    incoming_directory = Path(
        config["intake"]["incoming_directory"]
    )

    mode = (
        config["conversion"]
        .get("mode", "PROCESS")
        .upper()
    )

    if mode not in {"PROCESS", "ANALYZE"}:
        raise ValueError(
            f"Unsupported conversion mode: {mode}"
        )

    if not incoming_directory.exists():
        raise FileNotFoundError(
            f"Incoming directory not found: {incoming_directory}"
        )

    json_files = sorted(
        incoming_directory.glob("*.json")
    )

    if not json_files:
        print(
            f"No JSON files found in {incoming_directory}"
        )
        return

    print(
        f"Found {len(json_files)} FHIR JSON file(s)"
    )

    total_resources = Counter()

    for file_path in json_files:

        try:
            grouped_resources = load_and_group_fhir_resources(
                file_path
            )
            resource_counts = get_resource_counts(
                grouped_resources
           )

        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"\n{file_path.name}"
                f"\n  Classification failed: {exc}"
            )
            continue

        print(f"\n{file_path.name}")

        if not resource_counts:
            print("  No FHIR resources identified")
            continue

        for resource_type, count in sorted(
            resource_counts.items()
        ):
            print(
                f"  {resource_type}: {count}"
            )

        total_resources.update(resource_counts)

        if mode == "PROCESS":
            dispatch_resources(
                file_path,
                grouped_resources,
                practitioner_config=config.get("practitioner"),
            )
    print_resource_inventory(
        total_resources
    )

    if mode == "ANALYZE":
        print(
            "\nANALYZE mode complete. "
            "No resources were dispatched."
        )


def print_resource_inventory(total_resources):
    """
    Print aggregate FHIR resource inventory
    across all incoming files.
    """

    print("\nFHIR RESOURCE INVENTORY")
    print("-----------------------")

    total_count = 0

    for resource_type, count in sorted(
        total_resources.items()
    ):
        print(
            f"{resource_type:<30} {count:>8}"
        )

        total_count += count

    print("-----------------------")
    print(
        f"{'Total resources':<30} {total_count:>8}"
    )
    