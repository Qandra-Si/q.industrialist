-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы, секвенторы, индексы
-- табличное представление здесь эквивалентно ESI Swagger Interface
-- см. https://esi.evetech.net/ui/

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;

DROP INDEX IF EXISTS qi.idx_eca_location_flag;
DROP INDEX IF EXISTS qi.idx_eca_location_type;
DROP INDEX IF EXISTS qi.idx_eca_location_id;
DROP INDEX IF EXISTS qi.idx_eca_corporation_type_ids;
DROP INDEX IF EXISTS qi.idx_eca_corporation_id;
DROP INDEX IF EXISTS qi.idx_eca_pk;
DROP TABLE IF EXISTS qi.esi_corporation_assets;

DROP TYPE  IF EXISTS qi.esi_location_type;

DROP INDEX IF EXISTS qi.idx_eus_type_id;
DROP INDEX IF EXISTS qi.idx_eus_system_id;
DROP INDEX IF EXISTS qi.idx_eus_pk;
DROP TABLE IF EXISTS qi.esi_universe_structures;

DROP INDEX IF EXISTS qi.idx_ecs_system_id;
DROP INDEX IF EXISTS qi.idx_ecs_type_id;
DROP INDEX IF EXISTS qi.idx_ecs_corporation_id;
DROP INDEX IF EXISTS qi.idx_ecs_pk;
DROP TABLE IF EXISTS qi.esi_corporation_structures;

DROP INDEX IF EXISTS qi.idx_ets_system_id;
DROP INDEX IF EXISTS qi.idx_ets_type_id;
DROP INDEX IF EXISTS qi.idx_ets_pk;
DROP TABLE IF EXISTS qi.esi_tranquility_stations;

DROP INDEX IF EXISTS qi.idx_ech_pk;
DROP TABLE IF EXISTS qi.esi_corporations;

DROP INDEX IF EXISTS qi.idx_eco_ceo_id;
DROP INDEX IF EXISTS qi.idx_eco_alliance_id;
DROP INDEX IF EXISTS qi.idx_eco_creator_id;
DROP INDEX IF EXISTS qi.idx_eco_home_station_id;
DROP INDEX IF EXISTS qi.idx_eco_pk;
DROP TABLE IF EXISTS qi.esi_characters;



--------------------------------------------------------------------------------
-- esi_characters
-- список персонажей (по аналогии с БД seat, откуда брались первые исходные данные)
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_characters (
    ech_character_id BIGINT NOT NULL,
    ech_name CHARACTER VARYING(255) NOT NULL,
    -- ech_description TEXT,
    ech_birthday CHARACTER VARYING(255) NOT NULL,
    -- ech_gender CHARACTER VARYING(255) NOT NULL,
    -- ech_race_id INTEGER NOT NULL,
    -- ech_bloodline_id INTEGER NOT NULL,
    -- ech_ancestry_id INTEGER,
    -- ech_security_status DOUBLE PRECISION,
    ech_created_at TIMESTAMP,
    ech_updated_at TIMESTAMP,
    CONSTRAINT pk_ech PRIMARY KEY (ech_character_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_characters OWNER TO qi_user;

CREATE UNIQUE INDEX idx_ech_pk
    ON qi.esi_characters USING btree
    (ech_character_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- esi_corporations
-- список корпораций (по аналогии с БД seat, откуда брались первые исходные данные)
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_corporations (
    eco_corporation_id BIGINT NOT NULL,
    eco_name CHARACTER VARYING(255) NOT NULL,
    eco_ticker CHARACTER VARYING(255) NOT NULL,
    eco_member_count INTEGER NOT NULL,
    eco_ceo_id BIGINT NOT NULL,
    eco_alliance_id INTEGER,
    -- eco_description TEXT,
    eco_tax_rate DOUBLE PRECISION NOT NULL,
    -- eco_date_founded TIMESTAMP,
    eco_creator_id BIGINT NOT NULL,
    -- eco_url CHARACTER VARYING(510),
    -- eco_faction_id INTEGER,
    eco_home_station_id INTEGER,
    eco_shares BIGINT,
    eco_created_at TIMESTAMP,
    eco_updated_at TIMESTAMP,
    CONSTRAINT pk_eco PRIMARY KEY (eco_corporation_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_corporations OWNER TO qi_user;

CREATE UNIQUE INDEX idx_eco_pk
    ON qi.esi_corporations USING btree
    (eco_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eco_ceo_id
    ON qi.esi_corporations USING btree
    (eco_ceo_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eco_alliance_id
    ON qi.esi_corporations USING btree
    (eco_alliance_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eco_creator_id
    ON qi.esi_corporations USING btree
    (eco_creator_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eco_home_station_id
    ON qi.esi_corporations USING btree
    (eco_home_station_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- esi_tranquility_stations
-- список станций (по аналогии с БД seat, откуда брались первые исходные данные)
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_tranquility_stations
(
    ets_station_id BIGINT NOT NULL,
    ets_type_id BIGINT NOT NULL,
    ets_name CHARACTER VARYING(255) NOT NULL,
    ets_owner_id BIGINT,
    ets_race_id BIGINT,
    ets_x DOUBLE PRECISION NOT NULL,
    ets_y DOUBLE PRECISION NOT NULL,
    ets_z DOUBLE PRECISION NOT NULL,
    ets_system_id BIGINT NOT NULL,
    ets_reprocessing_efficiency DOUBLE PRECISION NOT NULL,
    ets_reprocessing_stations_take DOUBLE PRECISION NOT NULL,
    ets_max_dockable_ship_volume DOUBLE PRECISION NOT NULL,
    ets_office_rental_cost DOUBLE PRECISION NOT NULL,
    ets_created_at TIMESTAMP,
    ets_updated_at TIMESTAMP,
    CONSTRAINT pk_ets PRIMARY KEY (ets_station_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_tranquility_stations OWNER TO qi_user;

CREATE UNIQUE INDEX idx_ets_pk
    ON qi.esi_tranquility_stations USING btree
    (ets_station_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ets_type_id
    ON qi.esi_tranquility_stations USING btree
    (ets_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ets_system_id
    ON qi.esi_tranquility_stations USING btree
    (ets_system_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- esi_universe_structures
-- список структур (по аналогии с БД seat, откуда брались первые исходные данные)
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_universe_structures
(
    eus_structure_id BIGINT NOT NULL,
    eus_name CHARACTER VARYING(255) NOT NULL,
    eus_owner_id BIGINT DEFAULT NULL,
    eus_system_id INTEGER NOT NULL,
    eus_type_id INTEGER DEFAULT NULL,
    eus_x DOUBLE PRECISION NOT NULL,
    eus_y DOUBLE PRECISION NOT NULL,
    eus_z DOUBLE PRECISION NOT NULL,
    eus_created_at TIMESTAMP NULL DEFAULT NULL,
    eus_updated_at TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT pk_eus PRIMARY KEY (eus_structure_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_universe_structures OWNER TO qi_user;

CREATE UNIQUE INDEX idx_eus_pk
    ON qi.esi_universe_structures USING btree
    (eus_structure_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eus_system_id
    ON qi.esi_universe_structures USING btree
    (eus_system_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eus_type_id
    ON qi.esi_universe_structures USING btree
    (eus_type_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- esi_corporation_structures
-- список корпоративных структур (по аналогии с БД seat, откуда брались первые
-- исходные данные)
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_corporation_structures
(
    ecs_structure_id BIGINT NOT NULL,
    ecs_corporation_id BIGINT NOT NULL,
    ecs_type_id INTEGER NOT NULL,
    ecs_system_id INTEGER NOT NULL,
    ecs_profile_id INTEGER NOT NULL,
    -- ecs_fuel_expires TIMESTAMP DEFAULT NULL,
    -- ecs_state_timer_start TIMESTAMP DEFAULT NULL,
    -- ecs_state_timer_end TIMESTAMP DEFAULT NULL,
    -- ecs_unanchors_at TIMESTAMP DEFAULT NULL,
    -- ecs_state enum('anchor_vulnerable','anchoring','armor_reinforce','armor_vulnerable','fitting_invulnerable','hull_reinforce','hull_vulnerable','online_deprecated','onlining_vulnerable','shield_vulnerable','unanchored','unknown') NOT NULL,
    -- ecs_reinforce_weekday INTEGER DEFAULT NULL,
    -- ecs_reinforce_hour INTEGER NOT NULL,
    -- ecs_next_reinforce_weekday INTEGER DEFAULT NULL,
    -- ecs_next_reinforce_hour INTEGER DEFAULT NULL,
    -- ecs_next_reinforce_apply TIMESTAMP DEFAULT NULL,
    ecs_created_at TIMESTAMP NULL DEFAULT NULL,
    ecs_updated_at TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT pk_ecs PRIMARY KEY (ecs_structure_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_corporation_structures OWNER TO qi_user;

CREATE UNIQUE INDEX idx_ecs_pk
    ON qi.esi_corporation_structures USING btree
    (ecs_structure_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecs_corporation_id
    ON qi.esi_corporation_structures USING btree
    (ecs_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecs_type_id
    ON qi.esi_corporation_structures USING btree
    (ecs_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecs_system_id
    ON qi.esi_corporation_structures USING btree
    (ecs_system_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- esi_corporation_assets
-- список корпоративных ассетов (по аналогии с БД seat, откуда брались первые
-- исходные данные)
--------------------------------------------------------------------------------
CREATE TYPE qi.esi_location_type AS ENUM ('station','solar_system','other','item');

CREATE TABLE qi.esi_corporation_assets
(
    eca_item_id BIGINT NOT NULL,
    eca_corporation_id BIGINT NOT NULL,
    eca_type_id INTEGER NOT NULL,
    eca_quantity INTEGER NOT NULL,
    eca_location_id BIGINT NOT NULL,
    eca_location_type qi.esi_location_type NOT NULL,
    eca_location_flag CHARACTER VARYING(255) NOT NULL,
    eca_is_singleton BOOLEAN NOT NULL,
    -- eca_x DOUBLE PRECISION,
    -- eca_y DOUBLE PRECISION,
    -- eca_z DOUBLE PRECISION,
    -- eca_map_id BIGINT,
    -- eca_map_name CHARACTER VARYING(255),
    eca_name CHARACTER VARYING(255),
    eca_created_at TIMESTAMP,
    eca_updated_at TIMESTAMP,
    CONSTRAINT pk_eca PRIMARY KEY (eca_item_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_corporation_assets OWNER TO qi_user;

CREATE UNIQUE INDEX idx_eca_pk
    ON qi.esi_corporation_assets USING btree
    (eca_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eca_corporation_id
    ON qi.esi_corporation_assets USING btree
    (eca_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eca_corporation_type_ids
    ON qi.esi_corporation_assets USING btree
    (eca_corporation_id ASC NULLS LAST, eca_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eca_location_id
    ON qi.esi_corporation_assets USING btree
    (eca_location_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eca_location_type
    ON qi.esi_corporation_assets USING btree
    (eca_location_type ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_eca_location_flag
    ON qi.esi_corporation_assets USING btree
    (eca_location_flag ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


-- получаем справку в конце выполнения всех запросов
\d+ qi.