from __future__ import annotations

from typing import Any

import requests


class ConditionFhirAdapter:
    def __init__(
        self,
        fhir_base_url: str,
        timeout: int = 30,
    ):
        self.fhir_base_url = fhir_base_url.rstrip("/")
        self.timeout = timeout

    def create_condition(
        self,
        resource: dict[str, Any],
    ) -> dict[str, Any]:

        if resource.get("resourceType") != "Condition":
            raise ValueError(
                "ConditionFhirAdapter expected "
                f"Condition, got {resource.get('resourceType')}"
            )

        url = f"{self.fhir_base_url}/Condition"

        response = requests.post(
            url,
            json=resource,
            headers={
                "Content-Type": "application/fhir+json",
                "Accept": "application/fhir+json",
            },
            timeout=self.timeout,
        )

        if response.status_code not in {
            200,
            201,
        }:
            raise RuntimeError(
                "Condition POST failed: "
                f"HTTP {response.status_code} "
                f"{response.text}"
            )

        body = response.json()

        destination_id = body.get("id")

        if not destination_id:
            raise RuntimeError(
                "Condition POST succeeded but "
                "destination resource did not contain an id"
            )

        return {
            "status_code": response.status_code,
            "destination_resource_type": "Condition",
            "destination_resource_id": destination_id,
            "resource": body,
        }