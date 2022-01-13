select
 h.*,
 o.*
from qi.esi_trade_hub_history h
 left outer join qi.esi_corporation_orders o on (ethh_location_id=o.ecor_location_id and o.ecor_order_id=ethh_order_id)
where
 h.ethh_done is not null and -- ордер удалён из trade_hub_orders и отправлен в trade_hub_history
 o.ecor_history=true and -- ордер является корпоративным и уже помечен как закрытый
 ( -- у ордера не совпадает price/remain? был закрыт с другой ценой, или реализован не полностью/полностью (это неизвестно)?
  o.ecor_price<>h.ethh_price or
  o.ecor_volume_remain<>h.ethh_volume_remain
 );

create table t1 as select * from qi.esi_trade_hub_history;

-- проверка: ордер удалён из trade_hub_orders и отправлен в trade_hub_history
-- проверка: ордер является корпоративным и уже помечен как закрытый
-- у ордера не совпадает price/remain? был закрыт с другой ценой, или реализован не полностью/полностью (это неизвестно)?
update qi.esi_trade_hub_history set
 ethh_price=co.ecor_price,
 ethh_volume_remain=co.ecor_volume_remain
from
 ( select ecor_order_id, ecor_price, ecor_volume_remain
   from qi.esi_corporation_orders
   where ecor_location_id=60003760 and ecor_history
 ) co
where
 ethh_done is not null and
 ethh_location_id=60003760 and
 ethh_order_id=co.ecor_order_id and
 (co.ecor_price<>ethh_price or co.ecor_volume_remain<>ethh_volume_remain);

update qi.esi_trade_hub_history set
 ethh_price=co.ecor_price,
 ethh_volume_remain=co.ecor_volume_remain
from
 ( select ecor_location_id, ecor_order_id, ecor_price, ecor_volume_remain
   from qi.esi_corporation_orders
   where ecor_corporation_id=98553333 and ecor_history
 ) co
where
 ethh_done is not null and
 ethh_location_id=co.ecor_location_id and
 ethh_order_id=co.ecor_order_id and
 (co.ecor_price<>ethh_price or co.ecor_volume_remain<>ethh_volume_remain);


select
 o.ecor_location_id,
 o.ecor_order_id,
 o.ecor_type_id,
 o.ecor_is_buy_order,
 o.ecor_issued,
 o.ecor_price,
 o.ecor_volume_remain,
 o.ecor_volume_total,
 o.ecor_updated_at,
 o.ecor_updated_at
from qi.esi_corporation_orders o
 left outer join qi.esi_trade_hub_history h on (ethh_location_id=o.ecor_location_id and o.ecor_order_id=ethh_order_id)
where
h.ethh_location_id is null;

insert into qi.esi_trade_hub_history
 select
  o.ecor_location_id,
  o.ecor_order_id,
  o.ecor_type_id,
  o.ecor_is_buy_order,
  o.ecor_issued,
  o.ecor_price,
  o.ecor_volume_remain,
  o.ecor_volume_total,
  o.ecor_updated_at,
  o.ecor_updated_at
 from qi.esi_corporation_orders o
  left outer join qi.esi_trade_hub_history h on (
   o.ecor_location_id=h.ethh_location_id and
   o.ecor_order_id=ethh_order_id
  )
 where
  o.ecor_location_id=60003760 and
  h.ethh_location_id is null;
 
 insert into qi.esi_trade_hub_history
 select
  o.ecor_location_id,
  o.ecor_order_id,
  o.ecor_type_id,
  o.ecor_is_buy_order,
  o.ecor_issued,
  o.ecor_price,
  o.ecor_volume_remain,
  o.ecor_volume_total,
  o.ecor_updated_at,
  o.ecor_updated_at
 from qi.esi_corporation_orders o
  left outer join qi.esi_trade_hub_history h on (
   o.ecor_location_id=h.ethh_location_id and
   o.ecor_order_id=ethh_order_id
  )
 where
  o.ecor_corporation_id=98553333 and
  h.ethh_location_id is null;