import json

HOSPITAL_FILE = r"C:\Users\vikra\synthea\output\fhir\practitionerInformation1788630120737.json"

with open(HOSPITAL_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Top-level type:", type(data).__name__)

if isinstance(data, dict):
    print("Top-level keys:")
    for key in data.keys():
        print(" -", key)

elif isinstance(data, list):
    print("Number of records:", len(data))
    if data:
        print("First record keys:")
        for key in data[0].keys():
            print(" -", key)
resource_types = sorted(
    set(
        entry.get("resource", {}).get("resourceType")
        for entry in data.get("entry", [])
        if entry.get("resource")
    )
)

print("\nResource types found:")
for resource_type in resource_types:
    print(" -", resource_type)            