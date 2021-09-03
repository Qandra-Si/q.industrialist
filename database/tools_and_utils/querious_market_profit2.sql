select
  market.type_id as id,
  tid.sdet_type_name as name,
  round(tid.sdet_volume::numeric * 866.0, 2) as jita_import_price, -- заменить на packaged_volume, считать по ESI
  null as "weekly volume",
  case
    when universe.emp_average_price is null or (universe.emp_average_price < 0.001) then universe.emp_adjusted_price
    else universe.emp_average_price
  end as "universe price",
  jita.sell as "jita sell",
  amarr.sell as "amarr sell",
  null as "3-fkcz price",
  null as markup,
  null as "+10% price",
  null as "+10% profit",
  null as "their price",
  weeks_passed.diff
from 
  (select (current_date - '2021-08-15'::date)/7.0 as diff) weeks_passed,
  ( select distinct type_id
    from (
      select ecwt_type_id as type_id --, 'j'::char as type
      from
        qi.esi_corporation_wallet_journals j
          left outer join qi.esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
      where
        (ecwj_date > '2021-08-15') and
        (ecwj_context_id_type = 'market_transaction_id') and
        ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
            ecwj_second_party_id in (2116129465,2116746261,2116156168) and -- Qandra Si, Kekuit Void, Qunibbra Do
            ecwj_division = 1) or
          ( ecwj_corporation_id in (98553333) and -- R Strike
            ecwj_second_party_id in (95858524) and -- Xatul' Madan
            ecwj_division = 7)
        )
      union
      select ecor_type_id --, 'o'::char
      from qi.esi_corporation_orders
      where
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id=1036927076065) and  -- станка рынка
        not ecor_is_buy_order and
        not ecor_history
      ) jto
  ) market
    left outer join qi.eve_sde_type_ids tid on (market.type_id = tid.sdet_type_id)
    left outer join (
      select ethp_type_id, ethp_sell as sell
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (market.type_id = jita.ethp_type_id)
    left outer join (
      select ethp_type_id, ethp_sell as sell
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (market.type_id = amarr.ethp_type_id)
    left outer join qi.esi_markets_prices universe on (market.type_id = universe.emp_type_id)


