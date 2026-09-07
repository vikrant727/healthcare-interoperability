import json
from pathlib import Path
from collections import defaultdict

SOURCE_DIR = Path(r"C:\Users\vikra\synthea\output\fhir")

# Find all Practitioner source files
files = sorted(SOURCE_DIR.glob("practitionerInformation*.json"))

# Store all practitioners grouped by NPI
practitioners_by_npi = defaultdict(list)

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Practitioner":
            continue

        # Find NPI
        npi = None

        for identifier in resource.get("identifier", []):
            if identifier.get("system") == "http://hl7.org/fhir/sid/us-npi":
                npi = identifier.get("value")
                break

        # Get name
        name = resource.get("name", [{}])[0]
        given = " ".join(name.get("given", []))
        family = name.get("family", "")
        full_name = f"{given} {family}".strip()

        practitioners_by_npi[npi].append({
            "name": full_name,
            "source_file": file.name,
            "practitioner_id": resource.get("id")
        })


# Summary
total_records = sum(len(records) for records in practitioners_by_npi.values())
unique_npis = len(practitioners_by_npi)

print("=" * 80)
print("PRACTITIONER INVENTORY")
print("=" * 80)

print(f"Source files:       {len(files)}")
print(f"Total resources:    {total_records}")
print(f"Unique NPIs:        {unique_npis}")
print(f"Duplicate records:  {total_records - unique_npis}")

# Find NPIs appearing more than once
duplicate_npis = {
    npi: records
    for npi, records in practitioners_by_npi.items()
    if len(records) > 1
}

# Separate clean duplicates from conflicts
clean_duplicates = {}
conflicts = {}

for npi, records in duplicate_npis.items():

    names = {record["name"] for record in records}

    if len(names) == 1:
        clean_duplicates[npi] = records
    else:
        conflicts[npi] = records


print("\n" + "=" * 80)
print("CLEAN DUPLICATES")
print("=" * 80)

if not clean_duplicates:
    print("None found.")

for npi, records in clean_duplicates.items():
    print(f"\nNPI: {npi}")

    for record in records:
        print(f"  Name: {record['name']}")
        print(f"  File: {record['source_file']}")
        print(f"  ID:   {record['practitioner_id']}")


print("\n" + "=" * 80)
print("CONFLICTING RECORDS")
print("=" * 80)

if not conflicts:
    print("None found.")

for npi, records in conflicts.items():
    print(f"\nNPI: {npi}")

    for record in records:
        print(f"  Name: {record['name']}")
        print(f"  File: {record['source_file']}")
        print(f"  ID:   {record['practitioner_id']}")


print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"Unique NPIs:          {unique_npis}")
print(f"Clean duplicate NPIs: {len(clean_duplicates)}")
print(f"Conflict NPIs:        {len(conflicts)}")