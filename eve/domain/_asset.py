from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


@dataclass
class Asset:
    is_blueprint_copy: bool
    is_singleton: bool
    item_id: int
    location_flag: str
    location_id: int
    location_type: str
    quantity: int
    type_id: int

    @staticmethod
    def from_dict(src: Dict[str, Any]):
        return Asset(
            is_blueprint_copy=src.get("is_blueprint_copy", False),
            is_singleton=src.get("is_singleton", False),
            item_id=src["item_id"],
            location_flag=src["location_flag"],
            location_id=src["location_id"],
            location_type=src["location_type"],
            quantity=src["quantity"],
            type_id=src["type_id"],
        )

'''
class LocationFlag(Enum):
    AssetSafety = "AssetSafety"
    AutoFit = "AutoFit"
    Bonus = "Bonus"
    Booster = "Booster"
    BoosterBay, \
    Capsule,\
    Cargo, \
    CorpDeliveries, \
    CorpSAG1, \
    CorpSAG2, \
    CorpSAG3, \
    CorpSAG4, \
    CorpSAG5, \
    CorpSAG6, \
    CorpSAG7, \
    CrateLoot, \
    Deliveries, \
    DroneBay, \
    DustBattle, \
    DustDatabank, \
    FighterBay, \
    FighterTube0, \
    FighterTube1, \
    FighterTube2, \
    FighterTube3, \
    FighterTube4, \
    FleetHangar, \
    FrigateEscapeBay, Hangar, HangarAll, HiSlot0, HiSlot1, HiSlot2, HiSlot3, HiSlot4, HiSlot5, HiSlot6, HiSlot7, HiddenModifiers, Implant, Impounded, JunkyardReprocessed, JunkyardTrashed, LoSlot0, LoSlot1, LoSlot2, LoSlot3, LoSlot4, LoSlot5, LoSlot6, LoSlot7, Locked, MedSlot0, MedSlot1, MedSlot2, MedSlot3, MedSlot4, MedSlot5, MedSlot6, MedSlot7, OfficeFolder, Pilot, PlanetSurface, QuafeBay, QuantumCoreRoom, Reward, RigSlot0, RigSlot1, RigSlot2, RigSlot3, RigSlot4, RigSlot5, RigSlot6, RigSlot7, SecondaryStorage, ServiceSlot0, ServiceSlot1, ServiceSlot2, ServiceSlot3, ServiceSlot4, ServiceSlot5, ServiceSlot6, ServiceSlot7, ShipHangar, ShipOffline, Skill, SkillInTraining, SpecializedAmmoHold, SpecializedCommandCenterHold, SpecializedFuelBay, SpecializedGasHold, SpecializedIndustrialShipHold, SpecializedLargeShipHold, SpecializedMaterialBay, SpecializedMediumShipHold, SpecializedMineralHold, SpecializedOreHold, SpecializedPlanetaryCommoditiesHold, SpecializedSalvageHold, SpecializedShipHold, SpecializedSmallShipHold, StructureActive, StructureFuel, StructureInactive, StructureOffline, SubSystemBay, SubSystemSlot0, SubSystemSlot1, SubSystemSlot2, SubSystemSlot3, SubSystemSlot4, SubSystemSlot5, SubSystemSlot6, SubSystemSlot7, Unlocked, Wallet, Wardrobe
'''
