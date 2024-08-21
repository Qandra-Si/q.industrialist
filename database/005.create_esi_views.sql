-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных вьюшки
-- табличное представление здесь эквивалентно ESI Swagger Interface
-- см. https://esi.evetech.net/ui/

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;




--------------------------------------------------------------------------------
-- esi_corporation_offices
-- список корпоративных офисов
--------------------------------------------------------------------------------
create or replace view qi.esi_corporation_offices as
    select
        s.corporation_id,
        s.location_id,
        s.name,
        s.system_id as solar_system_id,
        s.type_id as station_type_id,
        sol.sden_name as solar_system_name,
        strct.sden_name as station_type_name,
        coalesce(s.forbidden,false) as forbidden
    from (
        select
            a.eca_corporation_id as corporation_id,
            a.eca_location_id as location_id,
            s.ets_name as name,
            s.ets_system_id as system_id,
            s.ets_type_id as type_id,
            false as forbidden
        from
            qi.esi_corporation_assets a
                left outer join qi.esi_tranquility_stations s on (a.eca_location_id = s.ets_station_id)
        where
            a.eca_type_id = 27 and -- Office
            -- a.eca_corporation_id = 98615601 and -- RI4
            a.eca_location_id < 1000000000
      union
        select
            a.eca_corporation_id,
            a.eca_location_id,
            s.eus_name,
            s.eus_system_id,
            s.eus_type_id,
            s.eus_forbidden
        from
            qi.esi_corporation_assets a
                left outer join qi.esi_universe_structures s on (a.eca_location_id = s.eus_structure_id)
        where
            a.eca_type_id = 27 and -- Office
            -- a.eca_corporation_id = 98615601 and -- RI4
            a.eca_location_id >= 1000000000
    ) s
    left outer join qi.eve_sde_names sol on (sol.sden_category = 3 and sol.sden_id = s.system_id) -- cat:3 invNames
    left outer join qi.eve_sde_names strct on (strct.sden_category = 1 and strct.sden_id = s.type_id); -- cat:1 typeIDs
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- esi_known_stations
-- список известных станций и структур (хранятся в БД)
--------------------------------------------------------------------------------
create or replace view qi.esi_known_stations as
    select
        s.location_id,
        s.name,
        s.system_id as solar_system_id,
        s.type_id as station_type_id,
        sol.sden_name as solar_system_name,
        strct.sden_name as station_type_name,
        s.forbidden as forbidden
    from (
        select
            s.ets_station_id as location_id,
            s.ets_name as name,
            s.ets_system_id as system_id,
            s.ets_type_id as type_id,
            false as forbidden
        from qi.esi_tranquility_stations s
      union
        select
            s.eus_structure_id,
            s.eus_name,
            s.eus_system_id,
            s.eus_type_id,
            s.eus_forbidden
        from qi.esi_universe_structures s
    ) s
    left outer join qi.eve_sde_names sol on (sol.sden_category = 3 and sol.sden_id = s.system_id) -- cat:3 invNames
    left outer join qi.eve_sde_names strct on (strct.sden_category = 1 and strct.sden_id = s.type_id); -- cat:1 typeIDs
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_sde_market_groups_tree
-- древовидное представление market groups
--------------------------------------------------------------------------------
create or replace view qi.eve_sde_market_groups_tree as
  with recursive r as (
    select
      sdeg_group_id as id,
      sdeg_parent_id as parent,
      sdeg_group_name as name
    from qi.eve_sde_market_groups
    where sdeg_parent_id is null
    union all
    select
      branch.sdeg_group_id,
      branch.sdeg_parent_id,
      branch.sdeg_group_name
    from qi.eve_sde_market_groups as branch
      join r on branch.sdeg_parent_id = r.id
  )
  select r.* from r;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_sde_market_groups_tree_sorted
-- древовидное представление market groups (сортировка по названиям с учётом
-- вложенности)
--------------------------------------------------------------------------------
-- select max(length(g.sdeg_group_name)) from qi.eve_sde_market_groups g
-- 43
-- max depth = 5
-- max length of sort_str=43*5=215
--------------------------------------------------------------------------------
create or replace view qi.eve_sde_market_groups_tree_sorted as
  select
    rr.*,
    row_number() OVER () as rnum
  from (
    with recursive r as (
      select
        sdeg_group_id as id,
        sdeg_parent_id as parent,
        sdeg_group_name as name,
        1 as depth,
        sdeg_group_name::varchar(255) as sort_str
      from qi.eve_sde_market_groups
      where sdeg_parent_id is null
      union all
      select
        branch.sdeg_group_id,
        branch.sdeg_parent_id,
        branch.sdeg_group_name,
        r.depth+1,
        (r.sort_str || '|' || branch.sdeg_group_name)::varchar(255)
      from qi.eve_sde_market_groups as branch
        join r on branch.sdeg_parent_id = r.id
    )
    select r.id, r.parent, r.name, r.depth from r
    --select r.* from r
    order by r.sort_str
  ) rr;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_sde_market_groups_semantic
-- семантические группы market групп/подгрупп (все виды патронов, например,
-- выбираются как "Ammunition & Charges" и т.п.)
--------------------------------------------------------------------------------
create or replace view qi.eve_sde_market_groups_semantic as
  select
    g.sdeg_group_id as id,
    sg.sdeg_group_id as semantic_id,
    sg.sdeg_group_name as name
  from
    qi.eve_sde_market_groups g
      join (
        select sdeg_group_id, sdeg_group_name
        from qi.eve_sde_market_groups
      ) sg on (sg.sdeg_group_id = g.sdeg_semantic_id);
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_sde_workable_blueprints
-- список чертежей, связанных с продуктами, которые можно использовать (и
-- чертежи, и продукты являются published)
--------------------------------------------------------------------------------
create or replace view qi.eve_sde_workable_blueprints as
  select
    sdeb_blueprint_type_id as blueprint_type_id,
    sdeb_activity as activity_id,
    sdeb_time as time,
    sdebp_product_id as product_type_id,
    sdebp_quantity as quantity,
    sdebp_probability as probability
  from (
    select b.* from qi.eve_sde_blueprints b
      inner join qi.eve_sde_type_ids bt on (bt.sdet_type_id=sdeb_blueprint_type_id and bt.sdet_published)
  ) b
    left outer join (
      select p.* from qi.eve_sde_blueprint_products p
        inner join qi.eve_sde_type_ids bt on (bt.sdet_type_id=sdebp_product_id and bt.sdet_published)
    ) p on (sdebp_blueprint_type_id=sdeb_blueprint_type_id AND sdebp_activity=sdeb_activity);
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_sde_available_blueprint_materials
-- список материалов, связанных доступными чертежами, которые можно использовать
-- (и чертежи, и продукты, и материалы являются published)
--------------------------------------------------------------------------------
create or replace view qi.eve_sde_available_blueprint_materials as
  select
    blueprint_type_id,
    activity_id,
    m.sdebm_material_id as material_type_id,
    m.sdebm_quantity as quantity
  from
    (select distinct blueprint_type_id, activity_id from qi.eve_sde_workable_blueprints) b
      inner join qi.eve_sde_blueprint_materials m on (m.sdebm_blueprint_type_id=b.blueprint_type_id and m.sdebm_activity=b.activity_id)
      inner join qi.eve_sde_type_ids on (m.sdebm_material_id = sdet_type_id and sdet_published);
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_ri4_personal_containers
-- список контейнеров, в которых хранятся личные ассеты и ассеты общака
--------------------------------------------------------------------------------
create or replace view qi.eve_ri4_personal_containers as
  select a.eca_corporation_id as corporation_id, a.eca_item_id as container_id
   --, a.eca_name as name
   --, eca_location_flag as hangar
   --, (select name from esi_known_stations where location_id in (select x.eca_location_id from qi.esi_corporation_assets x where x.eca_item_id=a.eca_location_id)) as station
   --, (select sdet_type_name from eve_sde_type_ids where sdet_type_id=a.eca_type_id) as nm
  from qi.esi_corporation_assets a
  where
   eca_location_type='item' and eca_location_flag like 'CorpSAG%' and eca_is_singleton and 
   ( select substring(eca_location_flag,8,1) in ('1','7') or -- CorpSAG1, CorpSAG7
     (eca_name like '{pers}%' or eca_name like '.{nf}%') -- остальные ангары
   );
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_ri4_manufacturing_containers
-- список контейнеров, в которых находятся чертежи для производства
--------------------------------------------------------------------------------
create or replace view qi.eve_ri4_manufacturing_containers as
  select a.eca_corporation_id as corporation_id, a.eca_item_id as container_id
   --, a.eca_name as name
   --, eca_location_flag as hangar
   --, (select name from esi_known_stations where location_id in (select x.eca_location_id from esi_corporation_assets x where x.eca_item_id=a.eca_location_id)) as station
   -- , (select sdet_type_name from eve_sde_type_ids where sdet_type_id=a.eca_type_id) as nm
  from qi.esi_corporation_assets a
  where
   eca_location_type='item' and eca_location_flag like 'CorpSAG%' and eca_is_singleton and 
   ( select substring(eca_location_flag,8,1) not in ('1','7') and -- не в CorpSAG1, CorpSAG7
     (eca_name like '[prod%') -- остальные ангары
   );
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_ri4_stock_containers
-- список контейнеров, в которых находится сток для производства
--------------------------------------------------------------------------------
create or replace view qi.eve_ri4_stock_containers as
  select a.eca_corporation_id as corporation_id, a.eca_item_id as container_id
   --,a.eca_name as name
   --,eca_location_flag as hangar
   --,(select name from esi_known_stations where location_id in (select x.eca_location_id from esi_corporation_assets x where x.eca_item_id=a.eca_location_id)) as station
   --,(select sdet_type_name from eve_sde_type_ids where sdet_type_id=a.eca_type_id) as nm
  from qi.esi_corporation_assets a
  where
   eca_location_type='item' and eca_location_flag like 'CorpSAG%' and eca_is_singleton and 
   ( select substring(eca_location_flag,8,1) not in ('1','7') and -- не в CorpSAG1, CorpSAG7
     (eca_name like '%.stock%') -- коробки ..stock% и ...stock% в остальных ангарах
   );
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- eve_ri4_invent_containers
-- список контейнеров, из которых запускается инвент
--------------------------------------------------------------------------------
create or replace view qi.eve_ri4_invent_containers as
  select a.eca_corporation_id as corporation_id, a.eca_item_id as container_id
   --,a.eca_name as name
   --,eca_location_flag as hangar
   --,(select name from esi_known_stations where location_id in (select x.eca_location_id from esi_corporation_assets x where x.eca_item_id=a.eca_location_id)) as station
   --,(select sdet_type_name from eve_sde_type_ids where sdet_type_id=a.eca_type_id) as nm
  from qi.esi_corporation_assets a
  where
   eca_location_type='item' and eca_location_flag like 'CorpSAG%' and eca_is_singleton and 
   ( select substring(eca_location_flag,8,1) not in ('1','7') and -- не в CorpSAG1, CorpSAG7
     (eca_name like '%SCIENCE%invent%') -- коробки '.[SCIENCE] invention' в остальных ангарах
   );
--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.
