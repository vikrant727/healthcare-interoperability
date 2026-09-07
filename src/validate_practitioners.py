import json
from pathlib import Path
from collections import defaultdict

SOURCE_DIR = Path(r"C:\Users\vikra\synthea\output\fhir")

NPI_SYSTEM = "http://hl7.org/fhir/sid/us-npi"

# --------------------------------------------------
# 1. Load all Practitioner resources
# --------------------------------------------------

files = sorted(SOURCE_DIR.glob("practitionerInformation*.json"))

practitioners_by_npi = defaultdict(list)

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})

        if resource.get("resourceType") != "Practitioner":
            continue

        npi = None

        for identifier in resource.get("identifier", []):
            if identifier.get("system") == NPI_SYSTEM:
                npi = identifier.get("value")
                break

        if not npi:
            continue

        name = resource.get("name", [{}])[0]

        given = " ".join(name.get("given", []))
        family = name.get("family", "")
        full_name = f"{given} {family}".strip()

        practitioners_by_npi[npi].append({
            "resource": resource,
            "name": full_name,
            "source_file": file.name,
            "practitioner_id": resource.get("id")
        })


# --------------------------------------------------
# 2. Identify conflicts
# --------------------------------------------------

conflicts = set()

for npi, records in practitioners_by_npi.items():

    names = {record["name"] for record in records}

    if len(names) > 1:
        conflicts.add(npi)


# --------------------------------------------------
# 3. Validate non-conflicting Practitioners
# --------------------------------------------------

clean = []
invalid = []
skipped_conflicts = []

for npi, records in practitioners_by_npi.items():

    # Don't validate/create conflicting NPIs yet
    if npi in conflicts:
        skipped_conflicts.extend(records)
        continue

    practitioner = records[0]["resource"]

    issues = []

    # Check resource type
    if practitioner.get("resourceType") != "Practitioner":
        issues.append("Invalid resourceType")

    # Check NPI
    if not npi:
        issues.append("Missing NPI")

    # Check name
    names = practitioner.get("name", [])

    if not names:
        issues.append("Missing name")

    else:
        name = names[0]

        given = name.get("given", [])
        family = name.get("family", "")

        if not given:
            issues.append("Missing given name")

        if not family:
            issues.append("Missing family name")

    # ----------------------------------------------
    # Classification
    # ----------------------------------------------

    record = {
        "npi": npi,
        "name": records[0]["name"],
        "source_file": records[0]["source_file"],
        "practitioner_id": records[0]["practitioner_id"],
        "issues": issues
    }

    if issues:
        invalid.append(record)
    else:
        clean.append(record)


# --------------------------------------------------
# 4. Print results
# --------------------------------------------------

print("=" * 80)
print("PRACTITIONER VALIDATION")
print("=" * 80)

print(f"Source files:              {len(files)}")
print(f"Unique NPIs:               {len(practitioners_by_npi)}")
print(f"Conflict NPIs:             {len(conflicts)}")
print(f"Clean practitioners:       {len(clean)}")
print(f"Invalid practitioners:     {len(invalid)}")
print(f"Skipped conflict records:  {len(skipped_conflicts)}")

print()
print("=" * 80)
print("CLEAN PRACTITIONERS")
print("=" * 80)

for record in clean:
    print(
        f"NPI: {record['npi']} | "
        f"Name: {record['name']} | "
        f"Source: {record['source_file']}"
    )

print()
print("=" * 80)
print("INVALID PRACTITIONERS")
print("=" * 80)

if not invalid:
    print("None")

else:
    for record in invalid:
        print(
            f"NPI: {record['npi']} | "
            f"Name: {record['name']} | "
            f"Issues: {', '.join(record['issues'])}"
        )

print()
print("=" * 80)
print("CONFLICTING NPIs - SKIPPED")
print("=" * 80)

for npi in sorted(conflicts):
    print(f"NPI: {npi}")

    for record in practitioners_by_npi[npi]:
        print(
            f"    {record['name']} | "
            f"{record['source_file']}"
        )