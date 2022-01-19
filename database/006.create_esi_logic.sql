-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных хранимую логику
-- табличное представление здесь эквивалентно ESI Swagger Interface
-- см. https://esi.evetech.net/ui/

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;



--------------------------------------------------------------------------------
-- eca_solar_system_of_asset_item
-- поиск звёздной системы по известному идентификатору предмета или локации
--------------------------------------------------------------------------------
create or replace function qi.eca_solar_system_of_asset_item(item_id bigint) returns bigint
  language PLPGSQL
  as
$$
declare
  solar_system bigint;
begin
  select
    -- root.id,
    -- root.loc,
    -- root.flag,
    -- root.where,
    -- root.type,
    case root.where
      when 'solar_system' then root.loc
      when 'station' then (select ets_system_id from qi.esi_tranquility_stations where ets_station_id = root.loc)
      else
        case root.flag
          when 'OfficeFolder' then (select distinct solar_system_id from qi.esi_corporation_offices where location_id = root.loc)
          else null
        end
    end -- as solar_system_id
  into solar_system
  from (
    with recursive containers as (
      select
        1 as lvl,
        eca_item_id as id,
        eca_location_id as loc,
        eca_location_flag as flag,
        eca_location_type as where,
        eca_type_id as type
      from qi.esi_corporation_assets
      where eca_item_id = item_id -- 1035914379323 -- 1035784633882 -- 1032904414432 -- 1035914811151 -- 1035774772132
      union
        select
          lvl+1,
          a.eca_item_id,
          a.eca_location_id,
          a.eca_location_flag,
          eca_location_type,
          a.eca_type_id
        from qi.esi_corporation_assets as a
        inner join containers c on c.loc = a.eca_item_id
    ) select * from containers
    order by 1 desc
    limit 1
  ) root;
  -- select distinct eca_location_flag from qi.esi_corporation_assets
  -- select distinct eca_location_type from qi.esi_corporation_assets
  return solar_system;
end;
$$;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- ecj_on_insert_or_update_proc
-- триггеры для esi_corporation_industry_jobs
--------------------------------------------------------------------------------
create or replace function qi.ecj_on_insert_or_update_proc()
  returns trigger 
  language PLPGSQL
  as
$$
declare
  ebc_id_exist bigint;
  system_id bigint;
  me smallint;
begin
  if new.ecj_activity_id in (5,8) then
    -- id ? system_id ? me, te ?
    select ebc_id, ebc_system_id, ebc_job_material_efficiency
    into ebc_id_exist, system_id, me
    from qi.esi_blueprint_costs
    where ebc_job_id=new.ecj_job_id and ebc_job_corporation_id=new.ecj_corporation_id;
    --
    if ebc_id_exist is null then
      insert into qi.esi_blueprint_costs (
        ebc_system_id,
        ebc_transaction_type,
        ebc_blueprint_type_id,
        ebc_blueprint_runs,
        ebc_job_id,
        ebc_job_corporation_id,
        ebc_job_activity,
        ebc_job_runs,
        ebc_job_product_type_id,
        ebc_job_successful_runs,
        ebc_job_time_efficiency,
        ebc_job_material_efficiency,
        ebc_created_at,
        ebc_updated_at
      )
      select
        (select distinct o.solar_system_id from qi.esi_corporation_offices o where new.ecj_facility_id = o.location_id),
        case new.ecj_status when 'delivered' then 'f'
                            when 'cancelled' then 'd'
                            else 'j'
        end,
        new.ecj_blueprint_type_id,
        new.ecj_licensed_runs,
        new.ecj_job_id,
        new.ecj_corporation_id,
        new.ecj_activity_id,
        new.ecj_runs,
        new.ecj_product_type_id,
        new.ecj_successful_runs,
        b.ecb_time_efficiency,
        b.ecb_material_efficiency,
        current_timestamp at time zone 'GMT',
        current_timestamp at time zone 'GMT'
      from
        (select new.ecj_blueprint_id) as bp
          left outer join qi.esi_corporation_blueprints b on (bp.ecj_blueprint_id = b.ecb_item_id);
    else
      update qi.esi_blueprint_costs set(
        ebc_transaction_type,
        ebc_job_successful_runs,
        ebc_updated_at
      )=(select
           case new.ecj_status when 'delivered' then 'f'
                               when 'cancelled' then 'd'
                               else 'j'
           end,
           new.ecj_successful_runs,
           current_timestamp at time zone 'GMT'
      )
      where ebc_id = ebc_id_exist;
      -- ebc_system_id
      if system_id is null then
        update qi.esi_blueprint_costs set(
          ebc_system_id
        )=(select distinct o.solar_system_id
           from qi.esi_corporation_offices o
           where new.ecj_facility_id = o.location_id
        )
        where ebc_id = ebc_id_exist;
      end if;
      -- ebc_job_time_efficiency
      -- ebc_job_material_efficiency
      if me is null then
        update qi.esi_blueprint_costs set(
          ebc_job_time_efficiency,
          ebc_job_material_efficiency
        )=(select ecb_time_efficiency, ecb_material_efficiency
           from qi.esi_corporation_blueprints
           where new.ecj_blueprint_id = ecb_item_id
        )
        where ebc_id = ebc_id_exist;
      end if;
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists ecj_on_insert on qi.esi_corporation_industry_jobs;
create trigger ecj_on_insert
  before insert
  on qi.esi_corporation_industry_jobs
  for each row
  execute procedure qi.ecj_on_insert_or_update_proc();

drop trigger if exists ecj_on_update on qi.esi_corporation_industry_jobs;
create trigger ecj_on_update
  before update
  on qi.esi_corporation_industry_jobs
  for each row
  execute procedure qi.ecj_on_insert_or_update_proc();
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- ecb_on_insert_proc, ecb_on_insert
-- триггеры для esi_corporation_blueprints
--------------------------------------------------------------------------------
create or replace function qi.ecb_on_insert_or_update_proc()
  returns trigger 
  language PLPGSQL
  as
$$
declare
  blueprint_exist bigint;
  blueprint_changed bool;
  old_solar_system bigint;
  new_solar_system bigint;
begin
  if (TG_OP = 'INSERT') then
    select ebc_blueprint_id into blueprint_exist
    from qi.esi_blueprint_costs
    where ebc_blueprint_id=new.ecb_item_id; -- значение ebc_transaction_type='A' проверять смысла нет
    if blueprint_exist is null then
      insert into qi.esi_blueprint_costs (
        ebc_system_id,
        ebc_transaction_type,
        ebc_blueprint_id,
        ebc_blueprint_type_id,
        ebc_blueprint_runs,
        ebc_time_efficiency,
        ebc_material_efficiency,
        ebc_created_at,
        ebc_updated_at)
      select
        qi.eca_solar_system_of_asset_item(new.ecb_location_id),
        'A',
        new.ecb_item_id,
        new.ecb_type_id,
        new.ecb_runs,
        new.ecb_time_efficiency,
        new.ecb_material_efficiency,
        current_timestamp at time zone 'GMT',
        current_timestamp at time zone 'GMT';
    end if;
  elsif (TG_OP = 'UPDATE') then
    blueprint_changed = false;
    if (new.ecb_runs != old.ecb_runs) or (new.ecb_time_efficiency != old.ecb_time_efficiency) or (new.ecb_material_efficiency != old.ecb_material_efficiency) then
      blueprint_changed = true;
      new_solar_system = qi.eca_solar_system_of_asset_item(new.ecb_location_id);
    elsif (new.ecb_location_id != old.ecb_location_id) then
      -- не всякое изменение ecb_location_id интересно, - только если сменилась solar_system
      old_solar_system = qi.eca_solar_system_of_asset_item(old.ecb_location_id);
      new_solar_system = qi.eca_solar_system_of_asset_item(new.ecb_location_id);
      blueprint_changed = (old_solar_system != new_solar_system);
    end if;
    if blueprint_changed then
      insert into qi.esi_blueprint_costs (
        ebc_system_id,
        ebc_transaction_type,
        ebc_blueprint_id,
        ebc_blueprint_type_id,
        ebc_blueprint_runs,
        ebc_time_efficiency,
        ebc_material_efficiency,
        ebc_created_at,
        ebc_updated_at)
      select
        qi.eca_solar_system_of_asset_item(new.ecb_location_id),
        'C',
        new.ecb_item_id,
        new.ecb_type_id,
        new.ecb_runs,
        new.ecb_time_efficiency,
        new.ecb_material_efficiency,
        current_timestamp at time zone 'GMT',
        current_timestamp at time zone 'GMT';
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists ecb_on_insert on qi.esi_corporation_blueprints;
create trigger ecb_on_insert
  before insert
  on qi.esi_corporation_blueprints
  for each row
  execute procedure qi.ecb_on_insert_or_update_proc();

drop trigger if exists ecb_on_update on qi.esi_corporation_blueprints;
create trigger ecb_on_update
  before update
  on qi.esi_corporation_blueprints
  for each row
  execute procedure qi.ecb_on_insert_or_update_proc();
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- ecb_on_delete_proc, ecb_on_delete
-- триггеры для esi_corporation_blueprints
--------------------------------------------------------------------------------
create or replace function qi.ecb_on_delete_proc()
  returns trigger 
  language PLPGSQL
  as
$$
begin
  insert into qi.esi_blueprint_costs (
   ebc_system_id,
   ebc_transaction_type,
   ebc_blueprint_id,
   ebc_blueprint_type_id,
   ebc_blueprint_runs,
   ebc_time_efficiency,
   ebc_material_efficiency,
   ebc_created_at,
   ebc_updated_at
  )
  select
    qi.eca_solar_system_of_asset_item(old.ecb_location_id),
    'D',
    old.ecb_item_id,
    old.ecb_type_id,
    old.ecb_runs,
    old.ecb_time_efficiency,
    old.ecb_material_efficiency,
    current_timestamp at time zone 'GMT',
    current_timestamp at time zone 'GMT';
  return old;
end;
$$;

drop trigger if exists ecb_on_delete on qi.esi_corporation_blueprints;
create trigger ecb_on_delete
  before delete
  on qi.esi_corporation_blueprints
  for each row
  execute procedure qi.ecb_on_delete_proc();
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- ethp_sync_with_etho
-- синхронизация данных в таблице esi_trade_hub_prices (с сохранением
-- накопленных данных, по сведениям из таблицы esi_trade_hub_orders)
--------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE qi.ethp_sync_with_etho(location_id BIGINT)
LANGUAGE SQL
AS $$
 update qi.esi_trade_hub_prices set
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
  ethp_location_id=location_id and
  ethp_location_id=o.loc and ethp_type_id=o.tid
 ;
 update qi.esi_trade_hub_prices set
  ethp_sell_volume=0,
  ethp_buy_volume=0,
  ethp_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
 from
  ( select ethp_location_id as loc, ethp_type_id as tid
    from qi.esi_trade_hub_prices
     left outer join (
      select distinct o.etho_location_id as loc,o.etho_type_id as tid from qi.esi_trade_hub_orders o
    ) o on (ethp_location_id=o.loc and ethp_type_id=o.tid)
    where o.loc is null
  ) p
 where
  ethp_location_id=location_id and
  ethp_location_id=p.loc and ethp_type_id=p.tid
 ;
 insert into qi.esi_trade_hub_prices
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
       select distinct p.ethp_location_id as loc,p.ethp_type_id as tid from qi.esi_trade_hub_prices p
      ) p on (etho_location_id=p.loc and etho_type_id=p.tid)
     where p.loc is null and o.etho_location_id=location_id
     group by 1, 2
    ) o
 ;
$$;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- ethh_clean_obsolete
--
-- очистка таблицы esi_trade_hub_history от устаревших записей (не храним данные
-- о истории торгов в торговом хабе более 2х недель)
--------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE qi.ethh_clean_obsolete()
LANGUAGE SQL
AS $$
 delete from esi_trade_hub_history
 where ethh_done < (current_timestamp at time zone 'GMT' - interval '14 day');
 ;
$$;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- ethh_sync_with_etho
--
-- синхронизация данных в таблице esi_trade_hub_history (с сохранением
-- накопленных данных, по сведениям из таблицы esi_trade_hub_orders)
-- у ордера с течением времени может меняться (см. табл. esi_trade_hub_orders и esi_corporation_orders):
--  1. price меняется вместе с issued (order_id остаётся прежним)
--  2. volume_remain меняется при покупке/продаже по order-у
-- при этом total не меняется, даже если remain <> total при изменении price !
--
-- с историей изменении order-а синхронизируется (см. табл. esi_trade_hub_history):
--  1. изменённая цена price
--  2. остаток непроданных товаров volume_remain
-- при этом issued не изменяется, - остаётся прежним (соответствует открытию order-а)
--------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE qi.ethh_sync_with_etho(location_id BIGINT)
LANGUAGE SQL
AS $$
 update qi.esi_trade_hub_history set
  ethh_volume_remain=o.remain,
  ethh_price=o.price,
  ethh_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
 from
  ( select 
     keys.loc,
     keys.oid,
     o.etho_volume_remain as remain,
     o.etho_price as price
    from
     qi.esi_trade_hub_orders o,
     ( select etho_location_id as loc, etho_order_id as oid from qi.esi_trade_hub_orders
       where etho_location_id=location_id
        intersect
       select ethh_location_id, ethh_order_id from qi.esi_trade_hub_history
       where ethh_location_id=location_id
     ) keys -- те пары loc:order, которые есть в history
    where
     o.etho_location_id=location_id and
     keys.loc=o.etho_location_id and
     keys.oid=o.etho_order_id
  ) o
 where
  ethh_location_id=location_id and
  o.loc=ethh_location_id and
  o.oid=ethh_order_id and
  ( o.price <> ethh_price or o.remain <> ethh_volume_remain )
 ;
 update qi.esi_trade_hub_history set
  ethh_done=CURRENT_TIMESTAMP AT TIME ZONE 'GMT',
  ethh_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
 from
  ( select ethh_location_id loc, ethh_order_id oid from qi.esi_trade_hub_history
    where ethh_location_id=location_id
     except
    select etho_location_id as loc, etho_order_id as oid from qi.esi_trade_hub_orders
    where etho_location_id=location_id
  ) keys -- те пары loc:order, которых нет в orders
 where
  ethh_location_id=location_id and
  keys.loc=ethh_location_id and
  keys.oid=ethh_order_id and
  ethh_done is null
 ;
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
   null,
   CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
  from
   qi.esi_trade_hub_orders o,
   ( select etho_location_id as loc, etho_order_id as oid from qi.esi_trade_hub_orders
     where etho_location_id=location_id
      except
     select ethh_location_id, ethh_order_id from qi.esi_trade_hub_history
     where ethh_location_id=location_id
   ) keys -- те пары loc:order, которых нет в history
  where
   o.etho_location_id=location_id and
   keys.loc=o.etho_location_id and
   keys.oid=o.etho_order_id
 ;
 call qi.ethh_clean_obsolete()
 ;
$$;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- ethh_sync_with_ecor
--
-- синхронизация данных в таблице esi_trade_hub_history (с сохранением
-- накопленных данных, по сведениям из таблицы esi_corporation_orders)
-- у ордера с течением времени может меняться (см. табл. esi_trade_hub_orders и esi_corporation_orders):
--  1. price меняется вместе с issued (order_id остаётся прежним)
--  2. volume_remain меняется при покупке/продаже по order-у
-- при этом total не меняется, даже если remain <> total при изменении price !
--
-- с историей изменении order-а синхронизируется (см. табл. esi_trade_hub_history):
--  1. изменённая цена price
--  2. остаток непроданных товаров volume_remain
-- при этом issued не изменяется, - остаётся прежним (соответствует открытию order-а)
--------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE qi.ethh_sync_with_ecor_by_loc(location_id BIGINT)
LANGUAGE SQL
AS $$
 update qi.esi_trade_hub_history set
  ethh_price=co.ecor_price,
  ethh_volume_remain=co.ecor_volume_remain
 from
  ( select ecor_order_id, ecor_price, ecor_volume_remain
    from qi.esi_corporation_orders
    where ecor_location_id=location_id and ecor_history
  ) co
 where
  ethh_done is not null and
  ethh_location_id=location_id and
  ethh_order_id=co.ecor_order_id and
  (co.ecor_price<>ethh_price or co.ecor_volume_remain<>ethh_volume_remain)
 ;
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
   o.ecor_location_id=location_id and
   o.ecor_updated_at > (current_timestamp at time zone 'GMT' - interval '14 day') and
   h.ethh_location_id is null
 ;
 call qi.ethh_clean_obsolete()
 ;
$$;
--------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE qi.ethh_sync_with_ecor_by_corp(corporation_id BIGINT)
LANGUAGE SQL
AS $$
 update qi.esi_trade_hub_history set
  ethh_price=co.ecor_price,
  ethh_volume_remain=co.ecor_volume_remain
 from
  ( select ecor_location_id, ecor_order_id, ecor_price, ecor_volume_remain
    from qi.esi_corporation_orders
    where ecor_corporation_id=corporation_id and ecor_history
  ) co
 where
  ethh_done is not null and
  ethh_location_id=co.ecor_location_id and
  ethh_order_id=co.ecor_order_id and
  (co.ecor_price<>ethh_price or co.ecor_volume_remain<>ethh_volume_remain)
 ;
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
   o.ecor_corporation_id=corporation_id and
   o.ecor_updated_at > (current_timestamp at time zone 'GMT' - interval '14 day') and
   h.ethh_location_id is null
 ;
 call qi.ethh_clean_obsolete()
 ;
$$;
--------------------------------------------------------------------------------


-- получаем справку в конце выполнения всех запросов
\d+ qi.