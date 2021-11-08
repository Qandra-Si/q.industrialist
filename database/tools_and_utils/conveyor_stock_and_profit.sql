select
  foo.dt as date,
  foo.buy as stock,
  foo.sell - foo.buy as profit
from ( select
         x.ecj_start_date::date as dt,
         -- x.ecj_product_type_id,
         -- x.ecj_runs*p.sdebp_quantity,
         -- t.sdet_type_name,
         sum(x.ecj_runs*p.sdebp_quantity*jita.buy) as buy,
         sum(x.ecj_runs*p.sdebp_quantity*jita.sell) as sell
       from
         qi.esi_corporation_industry_jobs x,
         qi.eve_sde_type_ids t
           -- цены в жите прямо сейчас
           left outer join (
             select ethp_type_id, ethp_sell as sell, ethp_buy as buy
             from qi.esi_trade_hub_prices
             where ethp_location_id = 60003760
           ) jita on (t.sdet_type_id = jita.ethp_type_id),
         qi.eve_sde_blueprint_products p
       WHERE ecj_blueprint_location_id in (
               1035579167162,
               1035960770272,
               1036120482432,
               1036199500006,
               1036235492309,
               1036600242614,
               1036639613431,
               1036663824232,
               1036670735494,
               1036693490333,
               1037459693195,
               1037459705900) and
         x.ecj_product_type_id = t.sdet_type_id  and
         x.ecj_activity_id in (1) and
         p.sdebp_activity = x.ecj_activity_id and
         p.sdebp_blueprint_type_id = x.ecj_blueprint_type_id
       group by 1
       order by 1 desc) as foo;


select
  foo.ye as year,
  foo.mn as month,
  foo.buy as stock,
  foo.sell - foo.buy as profit
from ( select
         extract(year from x.ecj_start_date::date) as ye,
         extract(month from x.ecj_start_date::date) as mn,
         -- x.ecj_product_type_id,
         -- x.ecj_runs*p.sdebp_quantity,
         -- t.sdet_type_name,
         sum(x.ecj_runs*p.sdebp_quantity*jita.buy) as buy,
         sum(x.ecj_runs*p.sdebp_quantity*jita.sell) as sell
       from
         qi.esi_corporation_industry_jobs x,
         qi.eve_sde_type_ids t
           -- цены в жите прямо сейчас
           left outer join (
             select ethp_type_id, ethp_sell as sell, ethp_buy as buy
             from qi.esi_trade_hub_prices
             where ethp_location_id = 60003760
           ) jita on (t.sdet_type_id = jita.ethp_type_id),
         qi.eve_sde_blueprint_products p
       WHERE ecj_blueprint_location_id in (
               1035579167162,
               1035960770272,
               1036120482432,
               1036199500006,
               1036235492309,
               1036600242614,
               1036639613431,
               1036663824232,
               1036670735494,
               1036693490333,
               1037459693195,
               1037459705900) and
         x.ecj_product_type_id = t.sdet_type_id  and
         x.ecj_activity_id in (1) and
         p.sdebp_activity = x.ecj_activity_id and
         p.sdebp_blueprint_type_id = x.ecj_blueprint_type_id
       group by 1, 2
       order by 1 desc, 2 desc) as foo;