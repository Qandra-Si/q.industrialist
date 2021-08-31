select
  tid.sdet_type_name as item_name,
  jt.type_id,
  round(jt.wk_volume::numeric, 1) as wk_volume,
  case
    when mp.emp_average_price is null or (mp.emp_average_price < 0.001) then mp.emp_adjusted_price
    else mp.emp_average_price
  end as universe_price,
  ( select emrh_average
    from qi.esi_markets_region_history
    where emrh_region_id=10000002 and jt.type_id=emrh_type_id -- The Forge
    order by emrh_date desc
    limit 1
  ) as jita_price, -- нужна подгрузка рыночных цен
  round((tid.sdet_volume * 1212.66)::numeric, 2) as import_price, -- нужно загрузить в БД сведения о параметрах модулей
  null as "3-fkcz price", -- нужна подгрузка маркета
  so.avg_sell_price as "our price", -- нужна подгрузка ордеров
  null as markup,
  null as "+10% price",
  null as "+10% profit"
from (
    select
      jt.ecwt_type_id as type_id,
      max(jt.ecwt_quantity) as wk_volume
    from (
      select
        date_trunc('week', j.ecwj_date)::date as ecwj_date,
        t.ecwt_type_id,
        CASE WHEN sign(j.ecwj_amount) < 0 THEN 'buy'
                                          ELSE 'sell'
                                          END as deal,
        sum(t.ecwt_unit_price*t.ecwt_quantity) as ecwt_price,
        sum(t.ecwt_quantity) as ecwt_quantity
      from
        qi.esi_corporation_wallet_journals j
          left outer join qi.esi_corporation_wallet_transactions t on (j.ecwj_context_id = t.ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
      where
        ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
            ecwj_second_party_id in (2116129465,2116746261,2116156168) and -- Qandra Si, Kekuit Void, Qunibbra Do
            ecwj_division = 1) or -- главный кошелёк
          ( ecwj_corporation_id in (98553333) and -- R Strike
            ecwj_second_party_id in (95858524) and -- Xatul' Madan
            ecwj_division = 7)
        ) and
        ecwj_context_id_type = 'market_transaction_id' and
        ecwj_date > '2021-08-15'
      group by 1, 2, 3
      ) jt
    where jt.deal = 'sell'
    group by 1
  ) jt
  left outer join qi.eve_sde_type_ids tid on (jt.type_id = tid.sdet_type_id)
  left outer join (
    select
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
        ecor_corporation_id=98615601 and  -- R Initiative 4
        ecor_location_id=1036927076065 and  -- станка рынка
        not ecor_is_buy_order and
        not ecor_history
      group by ecor_type_id
      ) o
    order by 1
  ) so on (jt.type_id = so.type_id)
  left outer join qi.esi_markets_prices mp on (jt.type_id = mp.emp_type_id)
order by 1
