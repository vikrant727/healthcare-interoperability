from fhir.processors.patient_processor import process_patients
from fhir.services.practitioner_reconciliation import (
    reconcile_practitioner,
)


def dispatch_resources(
    file_path,
    grouped_resources,
    *,
    practitioner_config=None,
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

    # Temporary fallback until the caller passes the
    # Practitioner section from intake_pipeline.yml.
    if practitioner_config is None:
        practitioner_config = {
            "not_found_action": "CREATE",
            "default_mapping": {
                "destination_practitioner_id": None,
            },
        }

    for resource_type, resources in sorted(
        grouped_resources.items()
    ):
        count = len(resources)

        # --------------------------------------------------
        # Patient
        # --------------------------------------------------

        if resource_type == "Patient":
            process_patients(
                resources,
                source_file=file_path,
            )

        # --------------------------------------------------
        # Practitioner
        # --------------------------------------------------

        elif resource_type == "Practitioner":
            print(
                f"  Practitioner -> "
                f"Practitioner reconciliation ({count})"
            )

            for resource in resources:
                result = reconcile_practitioner(
                    resource,
                    base_url=fhir_base_url,
                    practitioner_config=practitioner_config,
                    source_system=source_system,
                    destination_system=destination_system,
                )

                normalized = result["normalized"]

                print(
                    "    "
                    f"{normalized['source_fhir_practitioner_id']} "
                    f"-> NPI "
                    f"{normalized['source_identifier_value']} "
                    f"-> {result['action']} "
                    f"Practitioner/"
                    f"{result['destination_practitioner_id']}"
                )

        # --------------------------------------------------
        # Not implemented yet
        # --------------------------------------------------

        else:
            print(
                f"  {resource_type} -> "
                f"no processor configured yet ({count})"
            )