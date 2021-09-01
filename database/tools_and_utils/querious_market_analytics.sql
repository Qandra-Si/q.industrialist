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
  foo.persistence as "persistence, %"
from (
  select
    mha.type_id,
    ceil(mha.volume*week_activity/24.0) as weekly_volume,
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
        emrh_region_id = 10000050 and
        emrh_date >= '2021-02-15' and emrh_date <= '2021-08-01'
      group by 1, 2
      ) as mh
    group by 1
    ) mha
  ) foo
  left outer join qi.eve_sde_type_ids tid on (foo.type_id = tid.sdet_type_id)
-- order by 2 -- закладка "Все товары"
-- where foo.weekly_demand >= 1.0 order by foo.weekly_demand desc, foo.persistence desc, foo.weekly_volume desc -- закладка "Еженедельные сделки (популярность)"
where foo.weekly_demand >= 1.0 order by foo.weekly_volume desc  -- закладка "Еженедельные сделки (объём)"
