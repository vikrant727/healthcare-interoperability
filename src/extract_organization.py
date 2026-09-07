import json

SOURCE_FILE = r"C:\Users\vikra\synthea\output\fhir\hospitalInformation1788630120737.json"
OUTPUT_FILE = r".\data\organization_d2284f74.json"

TARGET_IDENTIFIER = "d2284f74-b6da-3a15-9791-84cdf2db18fb"

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    bundle = json.load(f)

organization = None

for entry in bundle.get("entry", []):
    resource = entry.get("resource", {})

    if resource.get("resourceType") != "Organization":
        continue

    for identifier in resource.get("identifier", []):
        if identifier.get("value") == TARGET_IDENTIFIER:
            organization = resource
            break

    if organization:
        break

if organization is None:
    print("Organization not found.")
else:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(organization, f, indent=2)

    print("Organization extracted successfully.")
    print("Organization ID:", organization.get("id"))
    print("Organization Name:", organization.get("name"))
    print("Saved to:", OUTPUT_FILE)