select
  stock.type_id,
  tid.sdet_type_name as name,
  stock.quantity as "quantity",
  ceil(universe.price * stock.quantity) as "universe avg price",
  ceil(jita.sell * stock.quantity) as "jita sell",
  ceil(jita.buy * stock.quantity) as "jita buy",
  stock.since as "lie up since",
  materials_using.variations as "blueprint variations",
  materials_using.jobs_times as "using in jobs",
  materials_using.last_using as "last using",
  materials_using.using_last_1month as "last 1 month using",
  materials_using.using_last_2month as "last 2 month using",
  materials_using.using_last_3month as "last 3 month using",
  materials_using.using_last_4month as "last 4 month using",
  materials_using.quantity_last_1month as m1q, -- last 1 month quantity
  materials_using.quantity_last_2month as m2q, -- last 2 month quantity
  materials_using.quantity_last_3month as m3q, -- last 3 month quantity
  materials_using.quantity_last_4month as m4q  -- last 4 month quantity
from
  -- содержимое коробки ..stock ALL на Сотие
  ( select
      eca_type_id as type_id,
      sum(eca_quantity) as quantity,
      max(eca_created_at::date) as since
    from qi.esi_corporation_assets
    where eca_location_id = 1036612408249
    group by 1
    -- order by 1
  ) stock
    -- сведения о предмете
    left outer join qi.eve_sde_type_ids tid on (stock.type_id = tid.sdet_type_id)
    -- усреднённые цены по евке прямо сейчас
    left outer join (
      select
        emp_type_id,
        case
          when emp_average_price is null or (emp_average_price < 0.001) then emp_adjusted_price
          else emp_average_price
        end as price
      from qi.esi_markets_prices
    ) universe on (stock.type_id = universe.emp_type_id)
    -- цены в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell, ethp_buy as buy
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (stock.type_id = jita.ethp_type_id)
    -- производственные работы с обнаруженным материалом
    left outer join (
      select
        -- sdebm_blueprint_type_id,
        sdebm_material_id as material_id,
        count(1) as variations,
        sum(jobs.times) as jobs_times,
        max(jobs.last_using) as last_using,
        sum(jobs.using_last_1month) as using_last_1month,
        sum(jobs.using_last_2month) as using_last_2month,
        sum(jobs.using_last_3month) as using_last_3month,
        sum(jobs.using_last_4month) as using_last_4month,
        sum(jobs.using_last_1month*sdebm_quantity) as quantity_last_1month,
        sum(jobs.using_last_2month*sdebm_quantity) as quantity_last_2month,
        sum(jobs.using_last_3month*sdebm_quantity) as quantity_last_3month,
        sum(jobs.using_last_4month*sdebm_quantity) as quantity_last_4month
      from
        qi.eve_sde_blueprint_materials
          -- подсчёт кол-ва работ, запущенных с использованием этого типа чертежей
          left outer join (
            select
              ecj_blueprint_type_id,
              ecj_activity_id,
              count(1) as times,
              max(ecj_start_date::date) as last_using,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '30 days') then 1 else 0 end) as using_last_1month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '60 days') then 1 else 0 end) as using_last_2month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '90 days') then 1 else 0 end) as using_last_3month,
              sum(case when ecj_start_date::date >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '120 days') then 1 else 0 end) as using_last_4month
            from qi.esi_corporation_industry_jobs jobs
            where jobs.ecj_corporation_id = 98677876
            group by 1, 2
          ) jobs on (sdebm_blueprint_type_id = jobs.ecj_blueprint_type_id and sdebm_activity = jobs.ecj_activity_id)
      group by 1
      -- order by 1
    ) materials_using on (stock.type_id = materials_using.material_id)
-- where tid.sdet_market_group_id in (1334,1333,1335,1336,1337) -- планетарка в стоке
