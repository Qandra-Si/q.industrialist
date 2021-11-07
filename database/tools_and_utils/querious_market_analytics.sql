select
  foo.type_id as "id",
  tid.sdet_type_name as "name",
  foo.weekly_volume as "weekly volume",
  case when foo.weekly_orders=0 then 1 else ceil(foo.weekly_volume/foo.weekly_orders) end as "deal volume",
  foo.average,
  foo.lowest,
  foo.highest,
  foo.weekly_orders as "orders per week",
  foo.weekly_demand as "days per week",
  foo.persistence as "persistence, %",
  ri4.type_id is not null as "ri4 orders",
  frtzr.ethp_type_id is not null as "3-fkcz orders"
from (
  select
    mha.type_id,
    round(mha.volume*week_activity/24.0, 2) as weekly_volume,
    round(mha.orders*week_activity/24.0, 1) as weekly_orders,
    round(mha.average::numeric, 2) as average,
    round(mha.lowest::numeric, 2) as lowest,
    round(mha.highest::numeric, 2) as highest,
    round(mha.days_activity*week_activity/24.0, 1) as weekly_demand,
    --round(mha.days_activity * (mha.week_activity/24), 20) as weekly_demand,
    round(100*(week_activity::numeric/24.0), 1) as persistence
  from (
    select
      mh.type_id,
      avg(mh.sum_average/mh.sum_volume) as average,
      avg(mh.sum_volume) as volume,
      avg(mh.sum_orders) as orders,
      avg(mh.lowest) as lowest,
      avg(mh.highest) as highest,
      avg(mh.days_activity) as days_activity,  -- среднее кол-во дней в неделю, когда совершались сделки
      count(1) as week_activity  -- кол-во недель (X из 24 всего), когда совершались сделки
    from (
      select
        emrh_type_id as type_id,
        date_trunc('week', emrh_date)::date as week_date,
        sum(emrh_average*emrh_volume) as sum_average,
        min(emrh_lowest) as lowest,
        max(emrh_highest) as highest,
        sum(emrh_volume) as sum_volume,
        sum(emrh_order_count) as sum_orders, -- кол-во ордеров в неделю
        count(1) as days_activity -- кол-во дней в каждой из недель, когда совершались сделки
      from
        qi.esi_markets_region_history
      where
        emrh_region_id = 10000050 and -- 10000050 'Querious', 10000002 'The Forge'
        emrh_date >= '2021-02-15' and emrh_date <= '2021-08-01'
      group by 1, 2
      ) as mh
    group by 1
    ) mha
  ) foo
  left outer join qi.eve_sde_type_ids tid on (foo.type_id = tid.sdet_type_id)
  left outer join (
    select distinct type_id
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
      -- список того, что корпораци€ продавала или продаЄт
      select ecor_type_id --, 'o'::char
      from qi.esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id=1036927076065) -- станка рынка
      ) jto
    ) ri4 on (foo.type_id = ri4.type_id)
    -- цены на нашем Fortizar пр€мо сейчас
    left outer join qi.esi_trade_hub_prices frtzr on (frtzr.ethp_location_id = 1036927076065 and foo.type_id = frtzr.ethp_type_id)
order by 2 -- закладка "¬се товары"
-- where foo.weekly_demand >= 1.0 order by foo.weekly_demand desc, foo.persistence desc, foo.weekly_volume desc -- закладка "≈женедельные сделки (попул€рность)"
-- where foo.weekly_demand >= 1.0 order by foo.weekly_volume desc  -- закладка "≈женедельные сделки (объЄм)"
-- where tid.sdet_type_name like 'Capital Core Defense Field Extender I' -- тест