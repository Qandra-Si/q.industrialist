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


-- получаем справку в конце выполнения всех запросов
\d+ qi.