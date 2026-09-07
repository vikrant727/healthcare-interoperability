import json
import requests

LOCATION_FILE = r".\data\location_fbe2ea9.json"
HAPI_URL = "http://localhost:8080/fhir/Location"

with open(LOCATION_FILE, "r", encoding="utf-8") as f:
    location = json.load(f)

response = requests.post(
    HAPI_URL,
    json=location,
    headers={"Content-Type": "application/fhir+json"}
)

print("HTTP Status:", response.status_code)
print(response.text)