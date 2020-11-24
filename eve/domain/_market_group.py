from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MarketGroup:
    group_id: int
    icon_id: int
    name: Dict[str, str]
    parent_group_id: Optional[int]
