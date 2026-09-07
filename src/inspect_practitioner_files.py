import json
from pathlib import Path

SOURCE_DIR = Path(r"C:\Users\vikra\synthea\output\fhir")

files = sorted(SOURCE_DIR.glob("practitionerInformation*.json"))

print(f"Found {len(files)} practitioner files.\n")

total_practitioners = 0

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    practitioners = [
        entry.get("resource", {})
        for entry in bundle.get("entry", [])
        if entry.get("resource", {}).get("resourceType") == "Practitioner"
    ]

    print(f"\n{'=' * 80}")
    print(f"FILE: {file.name}")
    print(f"Practitioners: {len(practitioners)}")
    print(f"{'=' * 80}")

    for practitioner in practitioners:
        npi = None

        for identifier in practitioner.get("identifier", []):
            if identifier.get("system") == "http://hl7.org/fhir/sid/us-npi":
                npi = identifier.get("value")
                break

        name = practitioner.get("name", [{}])[0]

        given = " ".join(name.get("given", []))
        family = name.get("family", "")

        print(f"NPI: {npi} | Name: {given} {family}")

        total_practitioners += 1

print(f"\n{'=' * 80}")
print(f"TOTAL PRACTITIONER RESOURCES: {total_practitioners}")
print(f"{'=' * 80}")