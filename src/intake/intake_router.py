from fhir.fhir_pipeline import run_fhir_pipeline

def route_intake(config):
    """
    Route En-Route processing to the configured source-format pipeline.
    """

    source_format = config["conversion"]["source_format"]

    if source_format == "FHIR_JSON":
        print("Routing intake to FHIR pipeline")
        run_fhir_pipeline(config)
    elif source_format == "CCDA":
        raise NotImplementedError(
            "CCDA processing is planned for a future release."
        )

    elif source_format == "HL7V2":
        raise NotImplementedError(
            "HL7v2 processing is planned for a future release."
        )

    else:
        raise ValueError(
            f"Unsupported source format: {source_format}"
        )