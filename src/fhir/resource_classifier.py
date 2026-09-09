import json
from collections import Counter
from pathlib import Path


def classify_fhir_file(file_path):
    """
    Inspect one FHIR JSON file and return the resource types found.

    Returns:
        {
            "Patient": 1,
            "Encounter": 5,
            "Observation": 10
        }
    """

    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    resource_counts = Counter()

    resource_type = data.get("resourceType")

    if resource_type == "Bundle":
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            entry_resource_type = resource.get("resourceType")

            if entry_resource_type:
                resource_counts[entry_resource_type] += 1

    elif resource_type:
        resource_counts[resource_type] += 1

    return dict(resource_counts)