--SET intervalstyle = 'postgres_verbose';
select
  cb.corporation_id as id,
  cb.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - cb.updated_at)::interval as ui,
  cb.bpc as bpc,
  cb.bpo as bpo,
  cb.quantity as q,
  cb_stat.items_changed as qc,
  c.eco_name as nm
from (
    select
      ecb_corporation_id as corporation_id,
      max(ecb_updated_at) as updated_at,
      sum(case when ecb_quantity=-2 then 1 else 0 end) as bpc,
      sum(case when ecb_quantity=-1 then 1 when ecb_quantity>0 then ecb_quantity else 0 end) as bpo,
      count(1) as quantity
    from qi.esi_corporation_blueprints
    group by 1
  ) cb
  left outer join qi.esi_corporations c on (c.eco_corporation_id = cb.corporation_id)
  left outer join (
    select
      ecb_corporation_id as corporation_id,
      count(1) as items_changed
    from qi.esi_corporation_blueprints
    where ecb_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '90 minutes')
    group by 1
  ) cb_stat on (cb_stat.corporation_id = cb.corporation_id)
