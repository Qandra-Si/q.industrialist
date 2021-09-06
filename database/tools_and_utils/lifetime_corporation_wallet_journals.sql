--SET intervalstyle = 'postgres_verbose';
select
  wj.corporation_id as id,
  wj.division as d,
  wj.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - wj.updated_at)::interval as ui,
  wj.quantity as q,
  wj_stat.rows_appear as ra,
  c.eco_name as nm
from (
    select
      ecwj_corporation_id as corporation_id,
      ecwj_division as division,
      max(ecwj_created_at) as updated_at,
      count(1) as quantity
    from qi.esi_corporation_wallet_journals
    group by 1, 2
  ) wj
  left outer join qi.esi_corporations c on (c.eco_corporation_id = wj.corporation_id)
  left outer join (
    select
      ecwj_corporation_id as corporation_id,
      ecwj_division as division,
      count(1) as rows_appear
    from qi.esi_corporation_wallet_journals
    where ecwj_created_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '60 minutes')
    group by 1, 2
  ) wj_stat on (wj_stat.corporation_id = wj.corporation_id and wj_stat.division = wj.division)
order by c.eco_name, wj.division;
