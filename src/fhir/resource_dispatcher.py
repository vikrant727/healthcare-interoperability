from fhir.services.organization_mapping import map_organization
from fhir.services.location_mapping import map_location
from destinations.fhir.patient_fhir_adapter import (
    deliver_patient_to_fhir,
)
from fhir.processors.patient_processor import process_patients
from fhir.processors.condition_classifier import ConditionClassifier
from fhir.processors.condition_processor import ConditionProcessor

from fhir.services.practitioner_reconciliation import (
    reconcile_practitioner,
)

from crosswalk import ResourceCrosswalk

def dispatch_resources(
    file_path,
    grouped_resources,
    *,
    practitioner_config=None,
    organization_config=None,
    location_config=None,
    source_system="synthea",
    destination_system="hapi",
    fhir_base_url="http://localhost:8080/fhir",  
    ):

    """
    Route already-classified FHIR resources to the
    appropriate processing/reconciliation workflow.

    The intake/classification layer has already grouped
    resources by resourceType before they reach this dispatcher.
    """

    print(f"\nDispatching resources from: {file_path.name}")

    # Fallback configuration if none is provided.
    
    if practitioner_config is None:
        practitioner_config = {
            "not_found_action": "CREATE",
            "default_mapping": {
                "destination_practitioner_id": None,
            },
        }

    if organization_config is None:
        organization_config = {
            "mapping_mode": "DEFAULT",
            "default_mapping": {
                "destination_organization_id": None,
            },
        }

    if location_config is None:
        location_config = {
            "mapping_mode": "DEFAULT",
            "default_mapping": {
                "destination_location_id": None,
            },
        }
    processing_order = [
        "Patient",
        "Practitioner",
        "Organization",
        "Location",
        "Condition",
    ]

    processed_types = set()


    # --------------------------------------------------
    # Process supported resources in dependency order
    # --------------------------------------------------

    for resource_type in processing_order:

        resources = grouped_resources.get(resource_type)

        if not resources:
            continue

        processed_types.add(resource_type)

        count = len(resources)

        # --------------------------------------------------
        # Patient
        # --------------------------------------------------

        if resource_type == "Patient":

            normalized_patients = process_patients(
                resources,
                source_file=file_path,
            )

            crosswalk = ResourceCrosswalk()

            delivered_count = 0

            for raw_patient, normalized_patient in zip(
                resources,
                normalized_patients,
            ):
                try:
                    (
                        destination_patient_id,
                        http_status,
                    ) = deliver_patient_to_fhir(
                        patient=raw_patient,
                        source_system=source_system,
                        base_url=fhir_base_url,
                    )

                    crosswalk.upsert(
                        source_system=source_system,
                        resource_type="Patient",

                        source_identifier_system=(
                            normalized_patient["mrn_system"]
                        ),
                        source_identifier_value=(
                            normalized_patient["source_mrn"]
                        ),

                        source_resource_id=(
                            normalized_patient[
                                "source_fhir_patient_id"
                            ]
                        ),

                        destination_system=destination_system,
                        destination_resource_type="Patient",
                        destination_resource_id=(
                            destination_patient_id
                        ),
                    )

                    delivered_count += 1

                    print(
                        "    Patient submitted: "
                        f"{normalized_patient['source_fhir_patient_id']} "
                        "-> "
                        f"Patient/{destination_patient_id} "
                        f"(HTTP {http_status})"
                    )

                except Exception as exc:
                    print(
                        "    Patient FAILED: "
                        f"{normalized_patient['source_fhir_patient_id']} "
                        f"- {exc}"
                    )

            print(
                "  Patient delivery -> "
                f"SUBMITTED={delivered_count}, "
                f"FAILED={len(resources) - delivered_count}"
            )
        # --------------------------------------------------
        # Practitioner
        # --------------------------------------------------

        elif resource_type == "Practitioner":

            for resource in resources:
                reconcile_practitioner(
                    resource,
                    practitioner_config=practitioner_config,
                    source_system=source_system,
                    destination_system=destination_system,
                    fhir_base_url=fhir_base_url,
                )

        # --------------------------------------------------
        # Organization
        # --------------------------------------------------

        elif resource_type == "Organization":

            for resource in resources:
                map_organization(
                    resource,
                    organization_config=organization_config,
                    source_system=source_system,
                    destination_system=destination_system,
                )

        # --------------------------------------------------
        # Location
        # --------------------------------------------------

        elif resource_type == "Location":

            for resource in resources:
                map_location(
                    resource,
                    location_config=location_config,
                    source_system=source_system,
                    destination_system=destination_system,
                )

        # --------------------------------------------------
        # Condition
        # --------------------------------------------------

        elif resource_type == "Condition":

            classifier = ConditionClassifier()
            crosswalk = ResourceCrosswalk()

            condition_processor = ConditionProcessor(
                crosswalk=crosswalk,
                fhir_base_url=fhir_base_url,
                source_system=source_system,
                destination_system=destination_system,
            )

            processing_summary = {
                "SUBMITTED": 0,
                "ALREADY_SUBMITTED": 0,
                "HELD_REVIEW": 0,
                "FAILED": 0,
            }

            for resource in resources:

                classification_result = classifier.classify(
                    resource
                )

                try:
                    result = condition_processor.process(
                        resource=resource,
                        classification_result=classification_result,
                    )

                    status = result["status"]

                    processing_summary[status] += 1

                    if status == "SUBMITTED":
                        print(
                            "    Condition submitted: "
                            f"{result['source_condition_id']} "
                            "-> "
                            f"Condition/"
                            f"{result['destination_condition_id']} "
                            "for Patient/"
                            f"{result['destination_patient_id']}"
                        )

                    elif status == "ALREADY_SUBMITTED":
                        print(
                            "    Condition already submitted: "
                            f"{result['source_condition_id']} "
                            "-> "
                            f"Condition/"
                            f"{result['destination_condition_id']}"
                        )

                except Exception as exc:

                    processing_summary["FAILED"] += 1

                    print(
                        "    Condition FAILED: "
                        f"{resource.get('id')} "
                        f"- {exc}"
                    )

            print(
                "  Condition processing -> "
                f"SUBMITTED={processing_summary['SUBMITTED']}, "
                f"ALREADY_SUBMITTED="
                f"{processing_summary['ALREADY_SUBMITTED']}, "
                f"HELD_REVIEW="
                f"{processing_summary['HELD_REVIEW']}, "
                f"FAILED={processing_summary['FAILED']}"
            )


    # --------------------------------------------------
    # Everything else is unsupported for now
    # --------------------------------------------------

    for resource_type, resources in grouped_resources.items():

        if resource_type in processed_types:
            continue

        print(
            f"  {resource_type} -> "
            f"no processor configured yet ({len(resources)})"
        )