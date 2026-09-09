def process_patients(patient_resources, source_file=None):
    """
    Process already-parsed FHIR Patient resources.

    Args:
        patient_resources: list of FHIR Patient dictionaries
        source_file: optional source filename/path for logging

    Returns:
        list of normalized patient records
    """

    processed_patients = []

    for patient in patient_resources:
        processed_patients.append(
            {
                "resource_id": patient.get("id"),
                "identifiers": patient.get("identifier", []),
                "name": patient.get("name", []),
                "birth_date": patient.get("birthDate"),
                "gender": patient.get("gender"),
                "address": patient.get("address", []),
                "telecom": patient.get("telecom", []),
            }
        )

    print(
        f"  Patient processor processed "
        f"{len(processed_patients)} patient(s)"
    )

    return processed_patients