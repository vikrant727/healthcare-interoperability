import json
from pathlib import Path


class ResourceMapping:
    def __init__(self):
        self.mappings = {}

    def add_mapping(
        self,
        resource_type,
        source_id,
        destination_reference
    ):
        if resource_type not in self.mappings:
            self.mappings[resource_type] = {}

        existing_mapping = self.mappings[
            resource_type
        ].get(source_id)

        if existing_mapping is None:
            self.mappings[
                resource_type
            ][source_id] = destination_reference

            return "ADDED"

        if existing_mapping == destination_reference:
            return "EXISTS"

        raise ValueError(
            "Mapping conflict: "
            f"{resource_type}/{source_id} "
            f"is already mapped to "
            f"{existing_mapping}, "
            f"cannot remap to "
            f"{destination_reference}"
        )

    def get_mapping(
        self,
        resource_type,
        source_id
    ):
        return self.mappings.get(
            resource_type,
            {}
        ).get(source_id)

    def has_mapping(
        self,
        resource_type,
        source_id
    ):
        return self.get_mapping(
            resource_type,
            source_id
        ) is not None

    def save(self, output_file):
        output_file = Path(output_file)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.mappings,
                f,
                indent=2
            )

    def load(self, input_file):
        input_file = Path(input_file)

        if not input_file.exists():
            return

        with open(
            input_file,
            "r",
            encoding="utf-8"
        ) as f:
            self.mappings = json.load(f)