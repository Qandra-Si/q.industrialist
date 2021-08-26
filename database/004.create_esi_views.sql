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
        strct.sden_name as station_type_name
    from (
        select
            s.ets_station_id as location_id,
            s.ets_name as name,
            s.ets_system_id as system_id,
            s.ets_type_id as type_id
        from qi.esi_tranquility_stations s
      union
        select
            s.eus_structure_id,
            s.eus_name,
            s.eus_system_id,
            s.eus_type_id
        from qi.esi_universe_structures s
    ) s
    left outer join qi.eve_sde_names sol on (sol.sden_category = 3 and sol.sden_id = s.system_id) -- cat:3 invNames
    left outer join qi.eve_sde_names strct on (strct.sden_category = 1 and strct.sden_id = s.type_id); -- cat:1 typeIDs
--------------------------------------------------------------------------------


-- получаем справку в конце выполнения всех запросов
\d+ qi.