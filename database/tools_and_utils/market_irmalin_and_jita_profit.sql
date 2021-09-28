select
 jita.ethp_type_id,
 tid.sdet_type_name,
 tid.sdet_packaged_volume,
 irmalin.ethp_sell as "irmalin sell",
 round(jita.ethp_buy::numeric,2) as "jita buy",
 round(jita.ethp_sell::numeric,2) as "jita sell",
 (jita.ethp_buy - irmalin.ethp_sell) / tid.sdet_packaged_volume as profit,
 --round(jita.ethp_buy::numeric*0.925,2) as "jita buy -7.5%",
 jita.ethp_buy_volume as "jita volume",
 irmalin.ethp_sell_volume as "irmalin volume" --,
 --floor(8825.3 / tid.sdet_packaged_volume) as "Sigil/T1 volume",
 --floor(8825.3 / tid.sdet_packaged_volume * jita.ethp_sell) as "Sigil/T1 price",
 --floor(floor(8825.3 / tid.sdet_packaged_volume) * (jita.ethp_buy*1.0167 - irmalin.ethp_sell)) as "Sigil/T1 profit"
from
 (select * from qi.esi_trade_hub_prices where ethp_location_id = 60003760) as jita
  left outer join qi.eve_sde_type_ids tid on (jita.ethp_type_id = tid.sdet_type_id),
 (select * from qi.esi_trade_hub_prices where ethp_location_id = 60013945) as irmalin
where
 jita.ethp_type_id = irmalin.ethp_type_id and
 --(jita.ethp_sell*1.0113) < irmalin.ethp_buy
 irmalin.ethp_sell < jita.ethp_buy
order by 7 desc
