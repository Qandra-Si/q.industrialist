from dataclasses import dataclass
from typing import Optional, Dict, Any


class Position:
    x: float
    y: float
    z: float


@dataclass
class StructureData:
    name: str
    owner_id: int
    solar_system_id: int
    type_id: int
    position: Optional[Position] = None

    def from_dict(src: Dict[str, Any]):
        return StructureData(
            name=src["name"],
            owner_id=src["owner_id"],
            solar_system_id=src["solar_system_id"],
            type_id=src["type_id"]
        )
