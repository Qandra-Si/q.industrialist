select
  ebc_id,
  ebc_blueprint_id,
  b.ecb_location_id,
  qi.eca_solar_system_of_asset_item(b.ecb_location_id) as solar
from
  qi.esi_blueprint_costs
    left outer join qi.esi_corporation_blueprints b on (ebc_blueprint_id = b.ecb_item_id)
where
  ebc_blueprint_id is not null and ebc_job_id is null 