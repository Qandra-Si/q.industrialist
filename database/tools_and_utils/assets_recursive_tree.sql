select
  root.id,
  root.loc,
  root.flag,
  root.where,
  root.type,
  case root.where
    when 'solar_system' then root.loc
    when 'station' then (select ets_system_id from qi.esi_tranquility_stations where ets_station_id = root.loc)
    else
      case root.flag
        when 'OfficeFolder' then (select solar_system_id from qi.esi_corporation_offices where location_id = root.loc)
        else null
      end
  end as solar_system_id
from (
  with recursive containers as (
    select
      1 as lvl,
      eca_item_id as id,
      eca_location_id as loc,
      eca_location_flag as flag,
      eca_location_type as where,
      eca_type_id as type
    from esi_corporation_assets
    where eca_item_id = 1035914379323 -- 1035784633882 -- 1032904414432 -- 1035914811151 -- 1035774772132
    union
      select
        lvl+1,
        a.eca_item_id,
        a.eca_location_id,
        a.eca_location_flag,
        eca_location_type,
        a.eca_type_id
      from esi_corporation_assets as a
      inner join containers c on c.loc = a.eca_item_id
  ) select * from containers
  order by 1 desc
  limit 1
) root
-- select distinct eca_location_flag from qi.esi_corporation_assets
-- select distinct eca_location_type from qi.esi_corporation_assets