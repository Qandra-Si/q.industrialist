select
 i.eco_name,
 o.ecor_is_buy_order as buy,
 ceil(sum(o.ecor_price * o.ecor_volume_remain)) as price
 --,ceil(sum(o.ecor_escrow)) as escrow
from
 qi.esi_corporation_orders o,
 qi.esi_corporations i
where
  o.ecor_corporation_id in (98553333, 98615601, 98677876) and
  o.ecor_corporation_id = i.eco_corporation_id and
  not o.ecor_history
group by 1, 2
order by 2, 1