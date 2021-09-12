select
  pzmzv.ethp_type_id as type_id,
  tid.sdet_type_name as name,
  pzmzv.ethp_sell as pzmzv_sell,
  jita.ethp_buy as jita_buy,
  floor(jita.ethp_buy*(1-0.0167) - pzmzv.ethp_sell) as profit
from qi.esi_trade_hub_prices pzmzv
  left outer join qi.esi_trade_hub_prices jita on (jita.ethp_type_id = pzmzv.ethp_type_id and jita.ethp_location_id = 60003760)
  left outer join qi.eve_sde_type_ids tid on (jita.ethp_type_id = tid.sdet_type_id)
where pzmzv.ethp_location_id = 1034323745897 and pzmzv.ethp_sell < jita.ethp_buy
order by 5