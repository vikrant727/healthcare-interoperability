import json
import csv
from pathlib import Path
from collections import defaultdict

from fhir_loader import get_matching_resource_id ,create_resource


NPI_SYSTEM = "http://hl7.org/fhir/sid/us-npi"


# --------------------------------------------------
# Load Practitioner resources
# --------------------------------------------------

def load_practitioners(source_dir):

    files = sorted(
        source_dir.glob("practitionerInformation*.json")
    )

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

    return practitioners_by_npi, files


# --------------------------------------------------
# Reconcile Practitioners against HAPI
# --------------------------------------------------
def reconcile_practitioners(
    practitioners_by_npi,
    hapi_url,
    missing_policy,
    mapping
):
    decision_inventory = []

    for npi, records in practitioners_by_npi.items():
        names = {record["name"] for record in records}

        if len(names) > 1:
            for record in records:
                decision_inventory.append({
                    "npi": npi,
                    "name": record["name"],
                    "source_file": record["source_file"],
                    "source_id": record["practitioner_id"],
                    "decision": "EXCEPTION_CONFLICT",
                    "hapi_id": None
                })
            continue

        practitioner = records[0]

        hapi_id = get_matching_resource_id(
            hapi_url,
            NPI_SYSTEM,
            npi
        )

        if hapi_id:
            decision_inventory.append({
                "npi": npi,
                "name": practitioner["name"],
                "source_file": practitioner["source_file"],
                "source_id": practitioner["practitioner_id"],
                "decision": "CLEAN_EXISTING",
                "hapi_id": hapi_id
            })

        else:
            if missing_policy == "default":
                decision_inventory.append({
                "npi": npi,
                "name": practitioner["name"],
                "source_file": practitioner["source_file"],
                "source_id": practitioner["practitioner_id"],
                "decision": "DEFAULT",
                "hapi_id": None
        })

            elif missing_policy == "create":
                new_hapi_id = create_resource(
                    hapi_url,
                    practitioner["resource"]
                )

                decision_inventory.append({
                    "npi": npi,
                    "name": practitioner["name"],
                    "source_file": practitioner["source_file"],
                    "source_id": practitioner["practitioner_id"],
                    "decision": "CLEAN_CREATED",
                    "hapi_id": new_hapi_id
        })

            elif missing_policy == "exception":
                decision_inventory.append({
                    "npi": npi,
                    "name": practitioner["name"],
                    "source_file": practitioner["source_file"],
                    "source_id": practitioner["practitioner_id"],
                    "decision": "EXCEPTION_MISSING",
                    "hapi_id": None
                })

            else:
                raise ValueError(
                    f"Unsupported practitioner missing policy: {missing_policy}"
                )

    return decision_inventory
# --------------------------------------------------
# Print reconciliation summary
# --------------------------------------------------

def print_summary(practitioners_by_npi, decision_inventory):
    clean_existing = [
        record for record in decision_inventory
        if record["decision"] == "CLEAN_EXISTING"
    ]

    clean_created = [
        record for record in decision_inventory
        if record["decision"] == "CLEAN_CREATED"
    ]

    defaults = [
        record for record in decision_inventory
        if record["decision"] == "DEFAULT"
    ]

    conflict_exceptions = [
        record for record in decision_inventory
        if record["decision"] == "EXCEPTION_CONFLICT"
    ]

    missing_exceptions = [
        record for record in decision_inventory
        if record["decision"] == "EXCEPTION_MISSING"
    ]

    conflict_npis = len({
        record["npi"] for record in conflict_exceptions
    })

    total_records = sum(
        len(records)
        for records in practitioners_by_npi.values()
    )

    print()
    print("=" * 80)
    print("RECONCILIATION SUMMARY")
    print("=" * 80)

    print(f"Total source records:       {total_records}")
    print(f"Unique NPIs:                {len(practitioners_by_npi)}")
    print(f"Conflict NPIs:              {conflict_npis}")
    print(f"CLEAN_EXISTING:             {len(clean_existing)}")
    print(f"CLEAN_CREATED:              {len(clean_created)}")
    print(f"DEFAULT:                     {len(defaults)}")
    print(f"EXCEPTION_CONFLICT records: {len(conflict_exceptions)}")
    print(f"EXCEPTION_MISSING records:  {len(missing_exceptions)}")
# --------------------------------------------------
# Export reconciliation inventory
# --------------------------------------------------

def export_to_csv(decision_inventory, output_file):

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "npi",
                "name",
                "source_file",
                "source_id",
                "decision",
                "hapi_id"
            ]
        )

        writer.writeheader()
        writer.writerows(decision_inventory)

    print()
    print("=" * 80)
    print("CSV EXPORT")
    print("=" * 80)

    print(
        f"Decision inventory saved to: {output_file}"
    )
