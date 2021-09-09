--SET intervalstyle = 'postgres_verbose';

-- select eca_item_id as office_id -- 1037133900408
-- from qi.esi_corporation_assets
-- where eca_location_id = 1034323745897 and eca_corporation_id = 98615601 and eca_location_flag = 'OfficeFolder';

select
  -- hangar.eca_item_id,
  hangar.eca_type_id as type_id,
  tid.sdet_type_name as name,
  hangar.eca_quantity as quantity,
  sbsq_hub.sell as "p-zmzv sell",
  to_char(jita.buy, 'FM999G999G999G999G999.90') as "jita buy",
  to_char(jita.sell, 'FM999G999G999G999G999.90') as "jita sell",
  to_char(amarr.sell, 'FM999G999G999G999G999.90') as "amarr sell",
  to_char(universe.price, 'FM999G999G999G999G999.90') as "universe price",
  case
    when (ceil(abs(universe.price - jita.sell)) - ceil(abs(universe.price - amarr.sell))) < 0 then 'jita'
    else 'amarr'
  end as "proper hub",
  round(tid.sdet_volume::numeric * 866.0, 2) as "jita import price", -- заменить на packaged_volume, считать по ESI
  hangar.eca_created_at::date as since,
  date_trunc('minutes', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - hangar.eca_updated_at)::interval as last_changed
from
  -- предметы на продажу в ангаре
  qi.esi_corporation_assets hangar
    -- сведени€ о предмете
    left outer join qi.eve_sde_type_ids tid on (hangar.eca_type_id = tid.sdet_type_id)
    -- цены в жите пр€мо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell, ethp_buy as buy
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (hangar.eca_type_id = jita.ethp_type_id)
    -- цены в амарре пр€мо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (hangar.eca_type_id = amarr.ethp_type_id)
    -- усреднЄнные цены по евке пр€мо сейчас
    left outer join (
      select
        emp_type_id,
        case
          when emp_average_price is null or (emp_average_price < 0.001) then emp_adjusted_price
          else emp_average_price
        end as price
      from qi.esi_markets_prices
    ) universe on (hangar.eca_type_id = universe.emp_type_id)
    -- ордера на данный товар на на нашей структуре
    left outer join (
      select
        ethp_type_id,
        to_char(ethp_sell, 'FM999G999G999G999.90') || ' (x' || to_char(ethp_sell_volume, 'FM999999999999999999') || ')' as sell
        --, ethp_sell, ethp_sell_volume
        --, ethp_buy, ethp_buy_volume
      from qi.esi_trade_hub_prices
      where ethp_location_id = 1034323745897
    ) sbsq_hub on (hangar.eca_type_id = sbsq_hub.ethp_type_id)
where
  hangar.eca_location_id = 1037133900408 and
  hangar.eca_location_flag = 'CorpSAG4' and
  hangar.eca_location_type = 'item' and
  not exists (select box.eca_item_id from qi.esi_corporation_assets as box where box.eca_location_id = hangar.eca_item_id)
order by tid.sdet_type_name
-- order by universe.price desc