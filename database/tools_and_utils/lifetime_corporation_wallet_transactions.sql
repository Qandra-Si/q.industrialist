--SET intervalstyle = 'postgres_verbose';
select
  wt.corporation_id as id,
  wt.division as d,
  wt.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - wt.updated_at)::interval as ui,
  wt.quantity as q,
  wt_stat.payments_appear as pa,
  c.eco_name as nm
from (
    select
      ecwt_corporation_id as corporation_id,
      ecwt_division as division,
      max(ecwt_created_at) as updated_at,
      count(1) as quantity
    from qi.esi_corporation_wallet_transactions
    group by 1, 2
  ) wt
  left outer join qi.esi_corporations c on (c.eco_corporation_id = wt.corporation_id)
  left outer join (
    select
      ecwt_corporation_id as corporation_id,
      ecwt_division as division,
      count(1) as payments_appear
    from qi.esi_corporation_wallet_transactions
    where ecwt_created_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '60 minutes')
    group by 1, 2
  ) wt_stat on (wt_stat.corporation_id = wt.corporation_id and wt_stat.division = wt.division)
order by c.eco_name, wt.division;
