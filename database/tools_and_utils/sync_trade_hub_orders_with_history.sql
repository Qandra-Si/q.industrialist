insert into qi.esi_trade_hub_history
 select
  o.etho_location_id,
  o.etho_order_id,
  o.etho_type_id,
  o.etho_is_buy,
  o.etho_issued,
  o.etho_price,
  o.etho_volume_remain,
  o.etho_volume_total,
  null
 from
  esi_trade_hub_orders o,
  ( select etho_location_id as loc, etho_order_id as oid from esi_trade_hub_orders
    where etho_location_id=60003760
     except
    select ethh_location_id, ethh_order_id from esi_trade_hub_history
    where ethh_location_id=60003760
  ) keys -- те пары loc:order, которых нет в history
 where
  o.etho_location_id=60003760 and
  keys.loc=o.etho_location_id and
  keys.oid=o.etho_order_id;

select etho_location_id as loc, etho_order_id as oid, etho_volume_remain as rem, etho_volume_total tot from esi_trade_hub_orders
where etho_location_id=60003760
 except
select ethh_location_id, ethh_order_id, ethh_volume_remain, ethh_volume_total from esi_trade_hub_history
where ethh_location_id=60003760;


select
 keys.loc, keys.oid
 , o.etho_volume_remain as remain, h.ethh_volume_remain as remain
 , o.etho_price, h.ethh_price
 , o.etho_issued , h.ethh_issued
from
 esi_trade_hub_orders o, esi_trade_hub_history h,
 ( select etho_location_id as loc, etho_order_id as oid from esi_trade_hub_orders
   where etho_location_id=60003760
    intersect
   select ethh_location_id, ethh_order_id from esi_trade_hub_history
   where ethh_location_id=60003760
 ) keys
where
 o.etho_location_id=60003760 and
 h.ethh_location_id=60003760 and
 keys.loc=o.etho_location_id and
 keys.oid=o.etho_order_id and
 keys.loc=h.ethh_location_id and
 keys.oid=h.ethh_order_id and
 ( o.etho_price <> h.ethh_price or o.etho_volume_remain <> h.ethh_volume_remain );

update esi_trade_hub_history set
 ethh_volume_remain=o.remain,
 ethh_price=o.price
from
 ( select 
    keys.loc,
    keys.oid,
    o.etho_volume_remain as remain,
    o.etho_price as price
   from
    esi_trade_hub_orders o,
    ( select etho_location_id as loc, etho_order_id as oid from esi_trade_hub_orders
      where etho_location_id=60003760
       intersect
      select ethh_location_id, ethh_order_id from esi_trade_hub_history
      where ethh_location_id=60003760
    ) keys -- те пары loc:order, которые есть в history
   where
    o.etho_location_id=60003760 and
    keys.loc=o.etho_location_id and
    keys.oid=o.etho_order_id
 ) o
where
 ethh_location_id=60003760 and
 o.loc=ethh_location_id and
 o.oid=ethh_order_id and
 ( o.price <> ethh_price or o.remain <> ethh_volume_remain );
 
update esi_trade_hub_history set
 ethh_done=CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
from
 ( select ethh_location_id loc, ethh_order_id oid from esi_trade_hub_history
   where ethh_location_id=60003760
    except
   select etho_location_id as loc, etho_order_id as oid from esi_trade_hub_orders
   where etho_location_id=60003760
 ) keys -- те пары loc:order, которых нет в orders
where
 ethh_location_id=60003760 and
 keys.loc=ethh_location_id and
 keys.oid=ethh_order_id and
 ethh_done is null;
