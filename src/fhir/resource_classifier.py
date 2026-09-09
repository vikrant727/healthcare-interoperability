import json
from collections import defaultdict
from pathlib import Path


def load_and_group_fhir_resources(file_path):
    """
    Load one FHIR JSON file and group actual resources by resourceType.

    Returns:
        {
            "Patient": [patient_resource],
            "Encounter": [encounter_1, encounter_2],
            "Observation": [observation_1, ...]
        }
    """

    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    grouped_resources = defaultdict(list)

    resource_type = data.get("resourceType")

    if resource_type == "Bundle":
        for entry in data.get("entry", []):
            resource = entry.get("resource")

            if not resource:
                continue

            entry_resource_type = resource.get("resourceType")

            if entry_resource_type:
                grouped_resources[entry_resource_type].append(
                    resource
                )

    elif resource_type:
        grouped_resources[resource_type].append(data)

    return dict(grouped_resources)


def get_resource_counts(grouped_resources):
    """
    Return resource counts from already-grouped FHIR resources.
    """

    return {
        resource_type: len(resources)
        for resource_type, resources
        in grouped_resources.items()
    }