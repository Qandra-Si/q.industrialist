select
  nm.sden_name,
  o.ecor_type_id as type_id,
  round((o.sum_price / o.sum_remain)::numeric, 2) as avg_sell_price
  -- ,o.sum_price,
  -- o.sum_remain
from (
  select
    ecor_type_id,
    sum(ecor_price*ecor_volume_remain) as sum_price,
    sum(ecor_volume_remain) as sum_remain
    --ecor_price,
    --ecor_volume_total,
    --ecor_volume_remain
  from qi.esi_corporation_orders
  where
    --ecor_type_id=2205 and
    ecor_corporation_id=98615601 and
    ecor_location_id=1036927076065 and
    not ecor_is_buy_order and
    not ecor_history
  group by ecor_type_id
  ) o
  left outer join qi.eve_sde_names nm on (nm.sden_category = 1 and o.ecor_type_id = nm.sden_id)
order by 1