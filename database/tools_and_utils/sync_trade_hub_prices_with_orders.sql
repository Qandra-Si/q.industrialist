select
 o.loc,
 o.tid,
 o.sell,
 o.buy,
 o.sell_volume,
 o.buy_volume,
 -- o.updated_at,
 p.ethp_sell as sell2,
 p.ethp_buy  as buy2,
 p.ethp_sell_volume as sv2,
 p.ethp_buy_volume as bv2
from
 qi.esi_trade_hub_prices p
  left outer join (
   select
    o.etho_location_id as loc,
    o.etho_type_id as tid,
    min(case o.etho_is_buy when true then null else o.etho_price end) as sell,
    max(case o.etho_is_buy when true then o.etho_price else null end) as buy,
    sum(case o.etho_is_buy when true then 0 else o.etho_volume_remain end) as sell_volume,
    sum(case o.etho_is_buy when true then o.etho_volume_remain else 0 end) as buy_volume,
    max(o.etho_updated_at) as updated_at
   from qi.esi_trade_hub_orders o
   group by 1, 2
  ) o on (p.ethp_location_id=o.loc and p.ethp_type_id=o.tid)
where
 o.sell_volume is not null and o.buy_volume is not null and (
  coalesce(o.sell,-1) <> coalesce(p.ethp_sell,-1) or
  coalesce(o.buy,-1) <> coalesce(p.ethp_buy,-1) -- or
  -- o.sell_volume <> p.ethp_sell_volume or
  -- o.buy_volume <> p.ethp_buy_volume
 )
 
-- 60008494	22973	| null	0.01	0	497522	| 1000.0	0.01	2072	497522
select * from t1 where t1.ethp_location_id=60008494 and t1.ethp_type_id=22973;
-- 60008494	22973	1000.0	0.01	2072	497522	2022-01-02 07:52:37.781	2022-01-11 08:23:41.000
-- 60008494	22973	null	0.01	0   	497522	2022-01-10 22:23:22.000
drop table qi.t1; create table qi.t1 as select p.* from qi.esi_trade_hub_prices p;
 
update t1 set
 ethp_sell=case o.sell_volume when 0 then ethp_sell else o.sell end,
 ethp_buy=case o.buy_volume when 0 then ethp_buy else o.buy end,
 ethp_sell_volume=o.sell_volume,
 ethp_buy_volume=o.buy_volume,
 ethp_updated_at=o.updated_at
from
 ( select
    o.etho_location_id as loc,
    o.etho_type_id as tid,
    min(case o.etho_is_buy when true then null else o.etho_price end) as sell,
    max(case o.etho_is_buy when true then o.etho_price else null end) as buy,
    sum(case o.etho_is_buy when true then 0 else o.etho_volume_remain end) as sell_volume,
    sum(case o.etho_is_buy when true then o.etho_volume_remain else 0 end) as buy_volume,
    max(o.etho_updated_at) as updated_at
   from qi.esi_trade_hub_orders o
   group by 1, 2
  ) o
where
 ethp_location_id=o.loc and ethp_type_id=o.tid
 and ethp_location_id=60008494 and ethp_type_id=22973;

select t1.ethp_location_id, t1.ethp_type_id, t1.*
from t1
 left outer join (
   select distinct o.etho_location_id,o.etho_type_id from qi.esi_trade_hub_orders o
 ) o on (ethp_location_id=o.etho_location_id and ethp_type_id=o.etho_type_id)
where o.etho_location_id is null;

update t1 set
 ethp_sell_volume=0,
 ethp_buy_volume=0,
 ethp_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
from
 ( select ethp_location_id as loc, ethp_type_id as tid
   from t1
    left outer join (
     select distinct o.etho_location_id as loc,o.etho_type_id as tid from qi.esi_trade_hub_orders o
   ) o on (ethp_location_id=o.loc and ethp_type_id=o.tid)
   where o.loc is null
 ) p
where ethp_location_id=p.loc and t1.ethp_type_id=p.tid;

select t1.ethp_location_id, t1.ethp_type_id, t1.*
from t1
 left outer join (
   select distinct o.etho_location_id,o.etho_type_id from qi.esi_trade_hub_orders o
 ) o on (ethp_location_id=o.etho_location_id and ethp_type_id=o.etho_type_id)
where o.etho_location_id is null;

select distinct o.etho_location_id as loc, o.etho_type_id as tid
from qi.esi_trade_hub_orders o
 left outer join (
  select distinct p.ethp_location_id as loc,p.ethp_type_id as tid from qi.t1 p
 ) p on (etho_location_id=p.loc and etho_type_id=p.tid)
where p.loc is null;

select * from t1 where t1.ethp_location_id=60008494 and t1.ethp_type_id=11887;

insert into t1
 select
  o.loc,
  o.tid,
  o.sell,
  o.buy,
  o.sell_volume,
  o.buy_volume,
  o.updated_at,
  o.updated_at
 from
  ( select
     o.etho_location_id as loc,
     o.etho_type_id as tid,
     min(case o.etho_is_buy when true then null else o.etho_price end) as sell,
     max(case o.etho_is_buy when true then o.etho_price else null end) as buy,
     sum(case o.etho_is_buy when true then 0 else o.etho_volume_remain end) as sell_volume,
     sum(case o.etho_is_buy when true then o.etho_volume_remain else 0 end) as buy_volume,
     max(o.etho_updated_at) as updated_at
    from qi.esi_trade_hub_orders o
     left outer join (
      select distinct p.ethp_location_id as loc,p.ethp_type_id as tid from qi.t1 p
     ) p on (etho_location_id=p.loc and etho_type_id=p.tid)
    where p.loc is null
    group by 1, 2
   ) o;
