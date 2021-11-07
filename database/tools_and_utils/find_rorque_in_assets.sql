select
  ci.name,
  ca.name,
  str.name,
  sta.name
from character_assets ca
  left outer join character_infos ci on (ci.character_id = ca.character_id)
  left outer join universe_structures str on (str.structure_id = ca.location_id)
  left outer join universe_stations sta on (sta.station_id = ca.location_id)
where ca.type_id = 28352
