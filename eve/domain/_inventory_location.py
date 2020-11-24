from dataclasses import dataclass


@dataclass
class InventoryLocation:
    parent_location_id: int
    type_id: int
