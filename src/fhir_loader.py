import requests


def search_by_identifier(
    resource_url,
    identifier_system,
    identifier_value
):
    response = requests.get(
        resource_url,
        params={
            "identifier": (
                f"{identifier_system}|{identifier_value}"
            )
        }
    )

    response.raise_for_status()

    return response.json()


def get_matching_resource_id(
    resource_url,
    identifier_system,
    identifier_value
):
    result = search_by_identifier(
        resource_url,
        identifier_system,
        identifier_value
    )

    total = result.get("total", 0)

    if total == 0:
        return None

    matches = result.get("entry", [])

    return matches[0]["resource"].get("id")


def create_resource(
    resource_url,
    resource
):
    response = requests.post(
        resource_url,
        json=resource,
        headers={
            "Content-Type": "application/fhir+json"
        }
    )

    response.raise_for_status()

    result = response.json()

    return result.get("id")