import json
import requests

PRACTITIONER_FILE = r".\data\practitioner_9999962993.json"
HAPI_URL = "http://localhost:8080/fhir/Practitioner"

with open(PRACTITIONER_FILE, "r", encoding="utf-8") as f:
    practitioner = json.load(f)

response = requests.post(
    HAPI_URL,
    json=practitioner,
    headers={"Content-Type": "application/fhir+json"}
)

print("HTTP Status:", response.status_code)
print(response.text)