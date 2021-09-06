select
  market.type_id as id,
  tid.sdet_type_name as name,
  case
    when (weeks_passed.volume_sell=0) or (weeks_passed.diff<0.14) then null
    when (weeks_passed.diff < 1.14) then weeks_passed.volume_sell
    else round(weeks_passed.volume_sell/weeks_passed.diff,1)
  end as "weekly volume",
  round(transactions_stat.avg_volume, 1) as "order volume",
  orders_stat.volume_remain as "3-fkcz volume",
  round(tid.sdet_volume::numeric * 866.0, 2) as "jita import price", -- заменить на packaged_volume, считать по ESI
  jita.sell as "jita sell",
  amarr.sell as "amarr sell",
  case
    when universe.emp_average_price is null or (universe.emp_average_price < 0.001) then universe.emp_adjusted_price
    else universe.emp_average_price
  end as "universe price",
  round(orders_stat.price_remain::numeric / orders_stat.volume_remain::numeric, 2) as "3-fkcz price",
  round(jita.sell::numeric*0.0313, 2) as markup,
  case
    when jita.sell::numeric*1.1313 < 100.0 then round(ceil(jita.sell::numeric*113.13)/100.0, 2)
    when jita.sell::numeric*1.1313 < 1000.0 then round(ceil(jita.sell::numeric*11.313)/10.0, 2)
    when jita.sell::numeric*1.1313 < 10000.0 then ceil(jita.sell::numeric*1.1313)
    when jita.sell::numeric*1.1313 < 100000.0 then round(jita.sell::numeric*1.1313+5, -1)
    when jita.sell::numeric*1.1313 < 1000000.0 then round(jita.sell::numeric*1.1313+50, -2)
    when jita.sell::numeric*1.1313 < 10000000.0 then round(jita.sell::numeric*1.1313+500, -3)
    when jita.sell::numeric*1.1313 < 100000000.0 then round(jita.sell::numeric*1.1313+5000, -4)
    when jita.sell::numeric*1.1313 < 1000000000.0 then round(jita.sell::numeric*1.1313+50000, -5)
    when jita.sell::numeric*1.1313 < 10000000000.0 then round(jita.sell::numeric*1.1313+500000, -6)
    else null
  end as "jita +10% price",
  round(jita.sell::numeric*0.1, 2) as "+10% profit",
  null as "their price"
from 
  ( select distinct type_id
    from (
      -- список транзакций по покупке/продаже избранными персонажами от имени 2х корпораций
      select ecwt_type_id as type_id --, 'j'::char as type
      from
        qi.esi_corporation_wallet_journals j
          left outer join qi.esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
      where
        not ecwt_is_buy and
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
      -- список того, что корпорация продавала или продаёт
      select ecor_type_id --, 'o'::char
      from qi.esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id=1036927076065) -- станка рынка
      ) jto
  ) market
    -- сведения о предмете
    left outer join qi.eve_sde_type_ids tid on (market.type_id = tid.sdet_type_id)
    -- цены в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (market.type_id = jita.ethp_type_id)
    -- цены в амарре прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (market.type_id = amarr.ethp_type_id)
    -- усреднённые цены по евке прямо сейчас
    left outer join qi.esi_markets_prices universe on (market.type_id = universe.emp_type_id)
    -- сведения о длительности sell-ордеров и о кол-ве проданного на станке рынка
    left outer join (
      select
        ecor_type_id,
        (current_date - min(ecor_issued::date))/7.0 as diff,
        sum(ecor_volume_total - ecor_volume_remain) as volume_sell
      from qi.esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id=1036927076065)  -- станка рынка
      group by ecor_type_id
    ) weeks_passed on (market.type_id = weeks_passed.ecor_type_id)
    -- усреднённый (типовой) объём sell-ордера по продаже
    left outer join (
      select
        ecwt_type_id,
        avg(ecwt_quantity) as avg_volume
      from qi.esi_corporation_wallet_transactions
      where
        not ecwt_is_buy and
        (ecwt_corporation_id=98615601) and  -- R Initiative 4
        (ecwt_location_id=1036927076065) -- станка рынка
      group by 1
    ) transactions_stat on (market.type_id = transactions_stat.ecwt_type_id)
    -- сведения об sell-ордерах, активных прямо сейчас
    left outer join (
      select
        ecor_type_id,
        sum(ecor_volume_remain) as volume_remain,
        sum(ecor_price*ecor_volume_remain) as price_remain
      from qi.esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_volume_remain > 0) and
        not ecor_history and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id=1036927076065)  -- станка рынка
      group by 1
    ) orders_stat on (market.type_id = orders_stat.ecor_type_id)
where
  not (tid.sdet_market_group_id = 1857) and -- исключая руду
  tid.sdet_type_id not in (17715,2998) -- случайно выставил от корпы
order by 7 -- 2


