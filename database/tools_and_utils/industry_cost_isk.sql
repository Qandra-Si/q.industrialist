select
  product.sdebp_product_id as id,
  cost.sdebm_blueprint_type_id as bp_id,
  cost.jsmp as jsmp,
  cost.asmp as asmp,
  jita.ethp_sell as js,
  jita.ethp_buy as jb,
  amarr.ethp_sell as as,
  amarr.ethp_buy as ab
from
  -- продукты производства
  qi.eve_sde_blueprint_products as product
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (product.sdebp_product_id = jita.ethp_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (product.sdebp_product_id = amarr.ethp_type_id),
  -- расчёт стоимости материалов в постройке продукта
  ( select
      m.sdebm_blueprint_type_id,
      -- m.sdebm_material_id,
      -- m.sdebm_quantity,
      sum(m.sdebm_quantity * jita.ethp_sell) as jsmp, -- jita' sell materials price
      sum(m.sdebm_quantity * amarr.ethp_sell) as asmp -- amarr' sell materials price
    from
      qi.eve_sde_blueprint_materials m
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from esi_trade_hub_prices
          where ethp_location_id = 60003760
        ) jita on (m.sdebm_material_id = jita.ethp_type_id)
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from esi_trade_hub_prices
          where ethp_location_id = 60008494
        ) amarr on (m.sdebm_material_id = amarr.ethp_type_id)
    where
      -- m.sdebm_blueprint_type_id=2762 and
      m.sdebm_activity = 1
    group by m.sdebm_blueprint_type_id
  ) as cost
where
  product.sdebp_blueprint_type_id = cost.sdebm_blueprint_type_id and
  product.sdebp_activity = 1