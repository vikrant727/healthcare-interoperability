from fhir.processors.patient_processor import process_patients

def dispatch_resources(file_path, grouped_resources):
    """
    Route grouped FHIR resources to resource-specific processors.

    Actual processors will be plugged in gradually.
    """

    print(f"\nDispatching resources from: {file_path.name}")

    for resource_type, resources in sorted(grouped_resources.items()):
        count = len(resources)

        if resource_type == "Patient":
            process_patients(
                resources,
                source_file=file_path,
    )

        elif resource_type == "Practitioner":
            print(f"  Practitioner -> Practitioner processor ({count})")

        elif resource_type == "PractitionerRole":
            print(f"  PractitionerRole -> PractitionerRole processor ({count})")

        elif resource_type == "Organization":
            print(f"  Organization -> Organization processor ({count})")

        elif resource_type == "Location":
            print(f"  Location -> Location processor ({count})")

        else:
            print(
                f"  {resource_type} -> no processor configured yet ({count})"
            )