from pathlib import Path
import yaml


DEFAULT_SOURCE_FORMAT = "FHIR_JSON"


def load_intake_config(config_path="config/intake_pipeline.yml"):
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Intake configuration not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    config.setdefault("conversion", {})
    config["conversion"].setdefault(
        "source_format",
        DEFAULT_SOURCE_FORMAT
    )

    return config