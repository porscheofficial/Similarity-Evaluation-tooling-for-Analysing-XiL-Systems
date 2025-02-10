
from dataclasses import dataclass


@dataclass
class Channel():
    id: str
    name: str
    aliases: list[str]
    value_name_mapping: dict[float, str]

    def to_dict(self) -> dict:

        swapped_value_name_mapping = {
            str(value): key for key, value in self.value_name_mapping.items()}

        return {
            "id": self.id,
            "name": self.name,
            "value_name_mapping": swapped_value_name_mapping,
            "aliases": self.aliases
        }

    @staticmethod
    def from_dict(data: dict) -> 'Channel':

        original_value_name_mapping = {
            float(value): key for key, value in data["value_name_mapping"].items()}

        return Channel(data["id"], data["name"], data["aliases"], original_value_name_mapping)

    def is_name_qualified(self) -> bool:
        if len(self.name.split("::")) != 3:
            return False
        last_name = self.name.split("::")[-1]
        if "XIX" not in last_name:
            return False
        return True
