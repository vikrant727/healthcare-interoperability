from pathlib import Path
import yaml
from reconcile_practitioners import (
    load_practitioners,
    reconcile_practitioners,
    print_summary,
    export_to_csv
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

SOURCE_DIR = Path(
    r"C:\Users\vikra\synthea\output\fhir"
)

HAPI_URL = (
    "http://localhost:8080/fhir/Practitioner"
)

OUTPUT_FILE = Path(
    r".\data\practitioner_reconciliation.csv"
)

def load_config(config_file):
    with open(
        config_file,
        "r",
        encoding="utf-8"
    ) as f:
        return yaml.safe_load(f)
# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def main():
    config = load_config(
        Path(r".\src\config.yaml")
    )

    practitioners_by_npi, files = load_practitioners(
        SOURCE_DIR
    )

    missing_policy = config[
    "reconciliation"
    ]["practitioner"]["if_missing"]

    decision_inventory = reconcile_practitioners(
        practitioners_by_npi,
        HAPI_URL,
        missing_policy
)

    print_summary(
        practitioners_by_npi,
        decision_inventory
    )

    export_to_csv(
        decision_inventory,
        OUTPUT_FILE
    )

# --------------------------------------------------
# Program entry point
# --------------------------------------------------

if __name__ == "__main__":
    main()