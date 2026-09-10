def process_practitioner(resource):
    """
    Process a single already-classified FHIR Practitioner resource.

    Returns a normalized Practitioner dictionary.
    """

    if not isinstance(resource, dict):
        raise ValueError("Practitioner resource must be a dictionary")

    if resource.get("resourceType") != "Practitioner":
        raise ValueError(
            f"Expected Practitioner resource, got "
            f"{resource.get('resourceType')}"
        )

    practitioner_id = resource.get("id")

    npi_system = None
    npi_value = None

    for identifier in resource.get("identifier", []):
        if identifier.get("system") == "http://hl7.org/fhir/sid/us-npi":
            npi_system = identifier.get("system")
            npi_value = identifier.get("value")
            break

    names = resource.get("name", [])
    name = names[0] if names else {}

    given_names = name.get("given", [])

    normalized = {
        "source_fhir_practitioner_id": practitioner_id,
        "source_identifier_system": npi_system,
        "source_identifier_value": npi_value,
        "family_name": name.get("family"),
        "given_name": given_names[0] if given_names else None,
        "prefix": (
            name.get("prefix", [None])[0]
            if name.get("prefix")
            else None
        ),
        "gender": resource.get("gender"),
        "active": resource.get("active"),
    }

    return normalized