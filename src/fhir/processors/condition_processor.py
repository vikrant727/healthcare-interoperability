from __future__ import annotations

from copy import deepcopy
from typing import Any

from crosswalk import ResourceCrosswalk
from destinations.fhir.condition_fhir_adapter import (
    ConditionFhirAdapter,
)


class ConditionProcessor:
    def __init__(
        self,
        *,
        crosswalk: ResourceCrosswalk,
        fhir_base_url: str,
        source_system: str = "synthea",
        destination_system: str = "hapi",
    ):
        self.crosswalk = crosswalk
        self.source_system = source_system
        self.destination_system = destination_system

        self.fhir_adapter = ConditionFhirAdapter(
            fhir_base_url=fhir_base_url
        )

    def process(
        self,
        resource: dict[str, Any],
        classification_result: dict[str, Any],
    ) -> dict[str, Any]:

        if resource.get("resourceType") != "Condition":
            raise ValueError(
                "ConditionProcessor expected Condition, "
                f"got {resource.get('resourceType')}"
            )

        classification = classification_result.get(
            "classification"
        )

        # REVIEW Conditions are not sent to the destination.
        if classification != "PROBLEM":
            return {
                "status": "HELD_REVIEW",
                "source_condition_id": resource.get("id"),
                "classification": classification,
                "destination_condition_id": None,
            }

        source_condition_id = resource.get("id")

        if not source_condition_id:
            raise ValueError(
                "Condition resource does not contain an id"
            )

        # -------------------------------------------------
        # 1. Idempotency check
        # -------------------------------------------------
        # If this Condition has already been delivered,
        # do not create it again.
        existing_condition = (
            self.crosswalk.lookup_by_source_resource_id(
                source_system=self.source_system,
                resource_type="Condition",
                source_resource_id=source_condition_id,
                destination_system=self.destination_system,
            )
        )

        if existing_condition:
            destination_condition_id = (
                self._get_destination_id(existing_condition)
            )

            return {
                "status": "ALREADY_SUBMITTED",
                "source_condition_id": source_condition_id,
                "classification": classification,
                "destination_condition_id": (
                    destination_condition_id
                ),
            }

        # -------------------------------------------------
        # 2. Resolve source Patient reference
        # -------------------------------------------------
        source_patient_id = self._extract_source_patient_id(
            resource
        )

        patient_crosswalk = (
            self.crosswalk.lookup_by_source_resource_id(
                source_system=self.source_system,
                resource_type="Patient",
                source_resource_id=source_patient_id,
                destination_system=self.destination_system,
            )
        )

        if not patient_crosswalk:
            raise RuntimeError(
                "Cannot process Condition "
                f"{source_condition_id}: "
                "no Patient crosswalk found for source "
                f"Patient {source_patient_id}"
            )

        destination_patient_id = (
            self._get_destination_id(patient_crosswalk)
        )

        if not destination_patient_id:
            raise RuntimeError(
                "Patient crosswalk was found but did not "
                "contain a destination resource id for "
                f"source Patient {source_patient_id}"
            )

        # -------------------------------------------------
        # 3. Prepare destination Condition
        # -------------------------------------------------
        condition_to_send = deepcopy(resource)

        condition_to_send["subject"] = {
            "reference": (
                f"Patient/{destination_patient_id}"
            )
        }

        # Source IDs should not be used as destination IDs.
        condition_to_send.pop("id", None)

        # Synthea Bundles frequently contain encounter
        # references using urn:uuid. We are not migrating
        # Encounter yet, so do not send an unresolved
        # source encounter reference to HAPI.
        encounter = condition_to_send.get("encounter")

        if encounter:
            encounter_reference = encounter.get(
                "reference", ""
            )

            if encounter_reference.startswith(
                "urn:uuid:"
            ):
                condition_to_send.pop(
                    "encounter",
                    None,
                )

        # -------------------------------------------------
        # 4. POST Condition to destination
        # -------------------------------------------------
        result = self.fhir_adapter.create_condition(
            condition_to_send
        )

        destination_condition_id = result[
            "destination_resource_id"
        ]

        # -------------------------------------------------
        # 5. Record Condition crosswalk
        # -------------------------------------------------
        self.crosswalk.upsert(
            source_system=self.source_system,
            resource_type="Condition",
            source_resource_id=source_condition_id,
            destination_system=self.destination_system,
            destination_resource_type="Condition",
            destination_resource_id=(
                destination_condition_id
            ),
        )

        return {
            "status": "SUBMITTED",
            "source_condition_id": source_condition_id,
            "source_patient_id": source_patient_id,
            "destination_patient_id": (
                destination_patient_id
            ),
            "destination_condition_id": (
                destination_condition_id
            ),
            "classification": classification,
        }

    @staticmethod
    def _extract_source_patient_id(
        resource: dict[str, Any],
    ) -> str:

        subject_reference = (
            resource
            .get("subject", {})
            .get("reference", "")
        )

        if not subject_reference:
            raise ValueError(
                "Condition does not contain "
                "subject.reference"
            )

        # Synthea commonly uses:
        #
        # urn:uuid:<patient-id>
        #
        # but this also handles:
        #
        # Patient/<patient-id>
        if subject_reference.startswith(
            "urn:uuid:"
        ):
            return subject_reference.removeprefix(
                "urn:uuid:"
            )

        if subject_reference.startswith(
            "Patient/"
        ):
            return subject_reference.split(
                "/",
                1,
            )[1]

        raise ValueError(
            "Unsupported Condition.subject.reference: "
            f"{subject_reference}"
        )

    @staticmethod
    def _get_destination_id(
        crosswalk_record: Any,
    ) -> str | None:
        """
        Allows the processor to tolerate either a dict-like
        crosswalk row or an object returned by ResourceCrosswalk.
        """

        if crosswalk_record is None:
            return None

        if isinstance(crosswalk_record, dict):
            return crosswalk_record.get(
                "destination_resource_id"
            )

        if hasattr(
            crosswalk_record,
            "destination_resource_id",
        ):
            return getattr(
                crosswalk_record,
                "destination_resource_id",
            )

        # sqlite3.Row supports key lookup.
        try:
            return crosswalk_record[
                "destination_resource_id"
            ]
        except (KeyError, IndexError, TypeError):
            return None