import json

SOURCE_FILE = r"C:\Users\vikra\synthea\output\fhir\hospitalInformation1788630120737.json"
OUTPUT_FILE = r".\data\location_fbe2ea9.json"

TARGET_IDENTIFIER = "fbe2ea9a-e200-36fa-b018-dc34f094b5f5"

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    bundle = json.load(f)

location = None

for entry in bundle.get("entry", []):
    resource = entry.get("resource", {})

    if resource.get("resourceType") != "Location":
        print(resource.get("resourceType") )              
        continue

    for identifier in resource.get("identifier", []):
        if identifier.get("value") == TARGET_IDENTIFIER:
            location = resource
            break

    if location:
        break

if location is None:
    print("Location not found.")
else:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(location, f, indent=2)

    print("Location extracted successfully.")
    print("Location ID:", location.get("id"))
    print("Location Name:", location.get("name"))
    print("Saved to:", OUTPUT_FILE)