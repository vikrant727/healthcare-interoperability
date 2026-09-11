from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


SYSTEM_ALIASES = {
    "http://snomed.info/sct": "SNOMED",
    "http://hl7.org/fhir/sid/icd-10-cm": "ICD10CM",
}


class ConditionClassifier:
    def __init__(
        self,
        config_path: str | Path = "config/condition_classification.csv",
    ):
        self.config_path = Path(config_path)
        self.problem_codes = self._load_problem_codes()

    def _load_problem_codes(
        self,
    ) -> set[tuple[str, str]]:

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Condition classification file not found: "
                f"{self.config_path}"
            )

        problem_codes: set[tuple[str, str]] = set()

        with open(
            self.config_path,
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as f:

            reader = csv.DictReader(f)

            required_columns = {
                "code_system",
                "code",
            }

            actual_columns = set(reader.fieldnames or [])
            missing_columns = required_columns - actual_columns

            if missing_columns:
                raise ValueError(
                    "Condition classification file is missing "
                    f"required columns: {sorted(missing_columns)}"
                )

            for row in reader:

                code_system = (
                    row.get("code_system") or ""
                ).strip().upper()

                code = (
                    row.get("code") or ""
                ).strip()

                if not code_system or not code:
                    continue

                problem_codes.add(
                    (code_system, code)
                )

        return problem_codes

    def classify(
        self,
        resource: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(resource, dict):
            raise ValueError(
                "Condition resource must be a dictionary"
            )

        if resource.get("resourceType") != "Condition":
            raise ValueError(
                f"Expected Condition resource, got "
                f"{resource.get('resourceType')}"
            )

        codings = (
            resource
            .get("code", {})
            .get("coding", [])
        )

        recognized_coding = None

        for coding in codings:

            fhir_system = coding.get("system")
            code = coding.get("code")
            display = coding.get("display")

            code_system = SYSTEM_ALIASES.get(
                fhir_system
            )

            if not code_system or not code:
                continue

            # Keep the first recognized coding so we can
            # report it even if it is not in the approved list.
            if recognized_coding is None:
                recognized_coding = {
                    "code_system": code_system,
                    "code": code,
                    "display": display,
                }

            if (code_system, code) in self.problem_codes:
                return {
                    "code_system": code_system,
                    "code": code,
                    "display": display,
                    "classification": "PROBLEM",
                    "review_reason": "",
                }

        if recognized_coding:
            return {
                **recognized_coding,
                "classification": "REVIEW",
                "review_reason": (
                    "Code not found in approved "
                    "Problem List candidate set"
                ),
            }

        return {
            "code_system": None,
            "code": None,
            "display": (
                resource
                .get("code", {})
                .get("text")
            ),
            "classification": "REVIEW",
            "review_reason": (
                "No supported coding system found"
            ),
        }