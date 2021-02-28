-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы, секвенторы, индексы
-- табличное представление здесь эквивалентно ESI Swagger Interface
-- см. https://esi.evetech.net/ui/

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;

DROP INDEX IF EXISTS qi.idx_eus_type_id;
DROP INDEX IF EXISTS qi.idx_eus_solar_system_id;
DROP INDEX IF EXISTS qi.idx_eus_pk;
DROP TABLE IF EXISTS qi.esi_universe_structures;

DROP INDEX IF EXISTS qi.idx_ecs_system_id;
DROP INDEX IF EXISTS qi.idx_ecs_type_id;
DROP INDEX IF EXISTS qi.idx_ecs_corporation_id;
DROP INDEX IF EXISTS qi.idx_ecs_pk;
DROP TABLE IF EXISTS qi.esi_corporation_structures;



--------------------------------------------------------------------------------
-- esi_universe_structures
-- список структур (по аналогии с БД seat, откуда брались первые исходные данные)
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_universe_structures
(
    eus_structure_id BIGINT NOT NULL,
    eus_name CHARACTER VARYING(255) NOT NULL,
    eus_owner_id BIGINT DEFAULT NULL,
    eus_solar_system_id INTEGER NOT NULL,
    eus_type_id INTEGER DEFAULT NULL,
    -- eus_x DOUBLE PRECISION NOT NULL,
    -- eus_y DOUBLE PRECISION NOT NULL,
    -- eus_z DOUBLE PRECISION NOT NULL,
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

CREATE INDEX idx_eus_solar_system_id
    ON qi.esi_universe_structures USING btree
    (eus_solar_system_id ASC NULLS LAST)
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



-- получаем справку в конце выполнения всех запросов
\d+ qi.