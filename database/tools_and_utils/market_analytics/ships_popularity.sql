select
  foo.type_id as "id",
  tid.sdet_type_name as "name",
  foo.weekly_volume as "weekly volume",
  case when foo.weekly_orders=0 then 1 else ceil(foo.weekly_volume/foo.weekly_orders) end as "deal volume",
  round((100.0* foo.average / jita.sell)::numeric, 1) as "profit %",
  ceil(foo.weekly_volume * (foo.average - jita.sell)) as "week profit, ISK",
  jita.sell as "jita sell",
  foo.average,
  foo.lowest,
  foo.highest,
  foo.weekly_orders as "orders per week",
  foo.weekly_demand as "days per week",
  foo.persistence as "persistence, %"
from (
  select
    mha.type_id,
    round(mha.volume*week_activity/10.0, 2) as weekly_volume,
    round(mha.orders*week_activity/10.0, 1) as weekly_orders,
    round(mha.average::numeric, 2) as average,
    round(mha.lowest::numeric, 2) as lowest,
    round(mha.highest::numeric, 2) as highest,
    round(mha.days_activity*week_activity/10.0, 1) as weekly_demand,
    --round(mha.days_activity * (mha.week_activity/10), 20) as weekly_demand,
    round(100*(week_activity::numeric/10.0), 1) as persistence
  from (
    select
      mh.type_id,
      avg(mh.sum_average/mh.sum_volume) as average,
      avg(mh.sum_volume) as volume,
      avg(mh.sum_orders) as orders,
      avg(mh.lowest) as lowest,
      avg(mh.highest) as highest,
      avg(mh.days_activity) as days_activity,  -- среднее кол-во дней в неделю, когда совершались сделки
      count(1) as week_activity  -- кол-во недель (X из 10 всего), когда совершались сделки
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
        -- 10000050 'Querious', 10000002 'The Forge', 10000015 'Venal', 10000069 'Black Rise', 10000064 'Essence', 10000042 'Metropolis'
        emrh_region_id = 10000069 and
        emrh_date >= '2021-08-23' and emrh_date <= '2021-10-31'
      group by 1, 2
      ) as mh
    group by 1
    ) mha
  ) foo
  left outer join qi.eve_sde_type_ids tid on (foo.type_id = tid.sdet_type_id)
  -- цены в жите прямо сейчас
  left outer join (
    select ethp_type_id, ethp_sell as sell
    from qi.esi_trade_hub_prices
    where ethp_location_id = 60003760
  ) jita on (foo.type_id = jita.ethp_type_id)
where
  foo.weekly_volume >= 5.0 and
  (tid.sdet_market_group_id in (select id from qi.eve_sde_market_groups_semantic where semantic_id=4))
order by -- сортировка по популярности
  foo.weekly_demand desc,
  foo.persistence desc,
  foo.weekly_volume desc
