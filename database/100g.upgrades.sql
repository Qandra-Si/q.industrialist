DROP INDEX IF EXISTS qi.idx_cl_trade_hub;
DROP INDEX IF EXISTS qi.idx_cl_trader_corp;
DROP INDEX IF EXISTS qi.idx_cl_pk;
DROP TABLE IF EXISTS qi.conveyor_limits;

CREATE TABLE qi.conveyor_limits
(
    cl_type_id INTEGER NOT NULL,
    cl_trade_hub BIGINT NOT NULL,
    cl_trader_corp INTEGER NOT NULL,
    cl_approximate INTEGER NOT NULL,
    CONSTRAINT pk_cl PRIMARY KEY (cl_type_id,cl_trade_hub),
    CONSTRAINT fk_cl_type_id FOREIGN KEY (cl_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cl_trader_corp FOREIGN KEY (cl_trader_corp)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cl_trade_hub_corp FOREIGN KEY (cl_trade_hub,cl_trader_corp)
        REFERENCES qi.market_hubs(mh_hub_id,mh_trader_corp) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.conveyor_limits OWNER TO qi_user;

CREATE UNIQUE INDEX idx_cl_pk
    ON qi.conveyor_limits USING btree
    (cl_type_id ASC NULLS LAST, cl_trade_hub ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cl_trader_corp
    ON qi.conveyor_limits USING btree
    (cl_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cl_trade_hub_corp
    ON qi.conveyor_limits USING btree
    (cl_trade_hub ASC NULLS LAST, cl_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;

--------------------------------------------------------------------------------

-- select *
-- from (
--  select
--   x.type_id,
--   x.market_id,
--   x.orders,
--   x.total_sum,
--   x.remain_sum,
--   t.sdet_type_name,
--   m.solar_system_name as trade_hub,
--   case when x.total_sum >= 1000000 then (x.total_sum / 100000)::numeric * 100000
--        when x.total_sum >=  500000 then (x.total_sum / 50000)::numeric * 50000
--        when x.total_sum >=  100000 then (x.total_sum / 10000)::numeric * 10000
--        when x.total_sum >=   50000 then (x.total_sum / 5000)::numeric * 5000
--        when x.total_sum >=   10000 then (x.total_sum / 1000)::numeric * 1000
--        when x.total_sum >=    5000 then (x.total_sum / 500)::numeric * 500
--        when x.total_sum >=    1000 then (x.total_sum / 100)::numeric * 100
--        when x.total_sum >=     500 then (x.total_sum / 50)::numeric * 50
--        when x.total_sum >=     100 then (x.total_sum / 10)::numeric * 10
--        when x.total_sum >=      90 then 100
--        when x.total_sum >=      30 then (x.total_sum / 10)::numeric * 10
--        when x.total_sum >=      26 then 30
--        when x.total_sum >=      15 then (x.total_sum / 5)::numeric * 5
--        when x.total_sum >=      11 then 15
--        else x.total_sum
--   end approximate
--  from (
--   select
--    x.ecor_type_id as type_id,
--    x.ecor_location_id as market_id,
--    count(1) as orders,
--    sum(x.ecor_volume_total) as total_sum,
--    sum(x.ecor_volume_remain) as remain_sum
--   FROM qi.esi_corporation_orders x
--   where not x.ecor_is_buy_order and not x.ecor_history
--   group by 1, 2
--  ) x
--   left outer join qi.eve_sde_type_ids t on (t.sdet_type_id=x.type_id)
--   left outer join qi.esi_known_stations m on (m.location_id=x.market_id)
-- ) x
-- order by x.trade_hub, x.approximate desc;

insert into qi.conveyor_limits
  select *
  from (
   select
    x.type_id,
    x.market_id,
    case when x.market_id = 60003760 then 98553333
         when x.market_id = 1038457641673 then 98677876
    end trader_corp,
    --x.orders,
    --x.total_sum,
    --x.remain_sum,
    --t.sdet_type_name,
    --m.solar_system_name as trade_hub,
    case when x.total_sum >= 1000000 then (x.total_sum / 100000)::numeric * 100000
         when x.total_sum >=  500000 then (x.total_sum / 50000)::numeric * 50000
         when x.total_sum >=  100000 then (x.total_sum / 10000)::numeric * 10000
         when x.total_sum >=   50000 then (x.total_sum / 5000)::numeric * 5000
         when x.total_sum >=   10000 then (x.total_sum / 1000)::numeric * 1000
         when x.total_sum >=    5000 then (x.total_sum / 500)::numeric * 500
         when x.total_sum >=    1000 then (x.total_sum / 100)::numeric * 100
         when x.total_sum >=     500 then (x.total_sum / 50)::numeric * 50
         when x.total_sum >=     100 then (x.total_sum / 10)::numeric * 10
         when x.total_sum >=      90 then 100
         when x.total_sum >=      30 then (x.total_sum / 10)::numeric * 10
         when x.total_sum >=      26 then 30
         when x.total_sum >=      15 then (x.total_sum / 5)::numeric * 5
         when x.total_sum >=      11 then 15
         else x.total_sum
    end approximate
   from (
    select
     x.ecor_type_id as type_id,
     x.ecor_location_id as market_id,
     count(1) as orders,
     sum(x.ecor_volume_total) as total_sum,
     sum(x.ecor_volume_remain) as remain_sum
    FROM qi.esi_corporation_orders x
    where not x.ecor_is_buy_order and not x.ecor_history
    group by 1, 2
   ) x
    left outer join qi.eve_sde_type_ids t on (t.sdet_type_id=x.type_id)
    left outer join qi.esi_known_stations m on (m.location_id=x.market_id)
  ) x
  where x.market_id in (60003760,1038457641673)
  order by x.market_id, x.approximate desc;
