print("Starting extract Practioner check ")
import json
TARGET_NPI = "9999962993"
PRACTITIONER_FILE = r"C:\Users\vikra\synthea\output\fhir\practitionerInformation1788630120737.json"

with open(PRACTITIONER_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

practitioners = []

for entry in data.get("entry", []):
    resource = entry.get("resource", {})

    if resource.get("resourceType") == "Practitioner":
        practitioners.append(resource)

print(f"Found {len(practitioners)} Practitioner resources")

for practitioner in practitioners[:5]:
    print("\n--- Practitioner ---")
    print("ID:", practitioner.get("id"))

    for identifier in practitioner.get("identifier", []):
        print(
            "Identifier:",
            identifier.get("system"),
            identifier.get("value")
        )

    for name in practitioner.get("name", []):
        print(
            "Name:",
            " ".join(name.get("given", [])),
            name.get("family", "")
        )


for practitioner in practitioners:
    for identifier in practitioner.get("identifier", []):
        if identifier.get("value") == TARGET_NPI:
            print("\nMATCH FOUND")
            print(json.dumps(practitioner, indent=2))