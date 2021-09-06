--SET intervalstyle = 'postgres_verbose';
select
  o.corporation_id as id,
  o.location_id as lid,
  o.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - o.updated_at)::interval as ui,
  o.total as t,
  o.buy as b,
  o.total-o.buy as s,
  o_stat.total as tu,
  o_stat.buy as bu,
  o_stat.total-o_stat.buy as su,
  c.eco_name as nm,
  ks.name as hub
from (
    select
      ecor_corporation_id as corporation_id,
      ecor_location_id as location_id,
      max(ecor_updated_at) as updated_at,
      count(1) as total,
      sum(ecor_is_buy_order::int) as buy
    from qi.esi_corporation_orders
    where not ecor_history
    group by 1, 2
  ) o
  left outer join qi.esi_corporations c on (c.eco_corporation_id = o.corporation_id)
  left outer join qi.esi_known_stations ks on (ks.location_id = o.location_id)
  left outer join (
    select
      ecor_corporation_id as corporation_id,
      ecor_location_id as location_id,
      count(1) as total,
      sum(ecor_is_buy_order::int) as buy
    from qi.esi_corporation_orders
    where ecor_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '60 minutes')
    group by 1, 2
  ) o_stat on (o_stat.corporation_id = o.corporation_id and o_stat.location_id = o.location_id)
order by c.eco_name, ks.name;
