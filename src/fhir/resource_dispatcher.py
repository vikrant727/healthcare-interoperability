def dispatch_resources(file_path, resource_counts):
    """
    Route detected FHIR resource types to their processors.

    Actual processors will be plugged in gradually.
    """

    print(f"\nDispatching resources from: {file_path.name}")

    for resource_type, count in sorted(resource_counts.items()):

        if resource_type == "Patient":
            print(f"  Patient -> Patient processor ({count})")

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