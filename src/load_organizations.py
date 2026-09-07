import json
import requests 
ORGANIZATION_FILE = r".\data\organization_d2284f74.json"
HAPI_URL = "http://localhost:8080/fhir/Organization"

with open(ORGANIZATION_FILE, "r", encoding="utf-8") as f:
    organization = json.load(f) 

response = requests.post(
    HAPI_URL,
    json=organization,
    headers={"Content-Type": "application/fhir+json"}
)
print("HTTP Status:", response.status_code)
print(response.text)