select
 j.ethp_type_id,
 tid.sdet_type_name,
 a.ethp_sell as "amarr sell",
 round(j.ethp_buy::numeric*1.0167,2) as "jita buy",
 j.ethp_buy_volume as "jita volume",
 a.ethp_sell_volume as "amarr volume",
 floor(8825.3 / tid.sdet_volume) as "Sigil/T1 volume",
 floor(8825.3 / tid.sdet_volume * j.ethp_sell) as "Sigil/T1 price",
 floor(floor(8825.3 / tid.sdet_volume) * (j.ethp_buy*1.0167 - a.ethp_sell)) as "Sigil/T1 profit"
from
 (select * from qi.esi_trade_hub_prices where ethp_location_id = 60003760) as j
  left outer join qi.eve_sde_type_ids tid on (j.ethp_type_id = tid.sdet_type_id),
 (select * from qi.esi_trade_hub_prices where ethp_location_id = 60008494) as a
where
 j.ethp_type_id = a.ethp_type_id and
 --(j.ethp_sell*1.0113) < a.ethp_buy
 a.ethp_sell < (j.ethp_buy*1.0167)
order by 8 desc
