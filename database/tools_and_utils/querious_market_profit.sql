select
  foo.type_id,
  foo.item_name,
  --round(foo.weekly_volume / weeks_passed.diff, 1) as "weekly volume",
  ceil(foo.weekly_volume / weeks_passed.diff) as "weekly volume",
  round(foo.import_price::numeric, 2) as "import price",
  foo.universe_price,
  foo.jita_average,
  foo."3-fkcz price",
  foo.markup,
  (foo.jita_average * 1.1 + foo.import_price + foo.markup) as "+10% price",
  foo.jita_average * 0.1 as "+10% profit",
  foo."their price"
from (
  select
    jt.type_id,
    tid.sdet_type_name as item_name,
    jt.wk_volume::numeric as weekly_volume,
    tid.sdet_volume * 866 as import_price,
    case
      when mp.emp_average_price is null or (mp.emp_average_price < 0.001) then mp.emp_adjusted_price
      else mp.emp_average_price
    end as universe_price,
    jita.emrh_average as jita_average,
    so.avg_sell_price as "3-fkcz price",
    (jita.emrh_average * (0.02+0.0113)) as markup, -- налог + брокерская комиссия
    null as "their price" -- нужна подгрузка маркета
  from (
      select
        jt.ecwt_type_id as type_id,
        avg(jt.ecwt_quantity) as wk_volume
      from (
        select
          date_trunc('week', j.ecwj_date)::date as ecwj_date,
          t.ecwt_type_id,
          CASE WHEN sign(j.ecwj_amount) < 0 THEN 'b'::char -- buy
                                            ELSE 's'::char -- sell
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
              ecwj_second_party_id in (95858524,2116746261) and -- Xatul' Madan, Kekuit Void
              ecwj_division = 7)
          ) and
          ecwj_context_id_type = 'market_transaction_id' and
          ecwj_date > '2021-08-15'
        group by 1, 2, 3
        ) jt
      where jt.deal = 's'::char
      group by 1
    ) jt
    left outer join (
      select
        o.ecor_type_id as type_id,
        round((o.sum_price / o.sum_remain)::numeric, 2) as avg_sell_price
      from (
        select
          ecor_type_id,
          sum(ecor_price*ecor_volume_remain) as sum_price, -- нельзя пользоваться avg(ecor_price)
          sum(ecor_volume_remain) as sum_remain
        from qi.esi_corporation_orders
        where
          --ecor_type_id=2205 and
          ecor_corporation_id=98615601 and  -- R Initiative 4
          ecor_location_id=1036927076065 and  -- станка рынка
          not ecor_is_buy_order and
          not ecor_history
        group by ecor_type_id
        ) o
    ) so on (jt.type_id = so.type_id)
    left outer join qi.esi_markets_prices mp on (jt.type_id = mp.emp_type_id)
    left outer join (
      select
        h.emrh_type_id,
        h.emrh_average
      from qi.esi_markets_region_history h
      where
        h.emrh_region_id=10000002 and -- The Forge
        h.emrh_date = (select max(emrh_date) from qi.esi_markets_region_history where emrh_region_id=10000002 and emrh_type_id = h.emrh_type_id)
    ) jita on (jt.type_id = jita.emrh_type_id)
    left outer join qi.eve_sde_type_ids tid on (jt.type_id = tid.sdet_type_id)
  ) foo,
  (select (current_date - '2021-08-15'::date)/7.0 as diff) weeks_passed
order by 1

