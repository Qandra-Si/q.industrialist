--SET intervalstyle = 'postgres_verbose';
select
  ca.corporation_id as id,
  ca.updated_at as uid,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - ca.updated_at)::interval as ui,
  ca.quantity as q,
  ca_stat.items_changed as qc,
  c.eco_name as nm
from (
    select
      eca_corporation_id as corporation_id,
      max(eca_updated_at) as updated_at,
      sum(eca_quantity) as quantity
    from qi.esi_corporation_assets
    group by 1
  ) ca
  left outer join qi.esi_corporations c on (c.eco_corporation_id = ca.corporation_id)
  left outer join (
    select
      eca_corporation_id as corporation_id,
      count(1) as items_changed
    from qi.esi_corporation_assets
    where eca_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '90 minutes')
    group by 1
  ) ca_stat on (ca_stat.corporation_id = ca.corporation_id)
