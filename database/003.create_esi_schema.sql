-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы, секвенторы, индексы
-- табличное представление здесь эквивалентно ESI Swagger Interface
-- см. https://esi.evetech.net/ui/

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;


---
DROP INDEX IF EXISTS qi.idx_ethh_updated_at;
DROP INDEX IF EXISTS qi.idx_ethh_issued;
DROP INDEX IF EXISTS qi.idx_ethh_location_is_buy;
DROP INDEX IF EXISTS qi.idx_ethh_location_type_id;
DROP INDEX IF EXISTS qi.idx_ethh_type_id;
DROP INDEX IF EXISTS qi.idx_ethh_location_id;
DROP INDEX IF EXISTS qi.idx_ethh_pk;
DROP TABLE IF EXISTS qi.esi_trade_hub_history;

DROP INDEX IF EXISTS qi.idx_etho_issued;
DROP INDEX IF EXISTS qi.idx_etho_location_is_buy;
DROP INDEX IF EXISTS qi.idx_etho_location_type_id;
DROP INDEX IF EXISTS qi.idx_etho_type_id;
DROP INDEX IF EXISTS qi.idx_etho_location_id;
DROP INDEX IF EXISTS qi.idx_etho_pk;
DROP TABLE IF EXISTS qi.esi_trade_hub_orders;

DROP INDEX IF EXISTS qi.idx_ethp_pk;
DROP TABLE IF EXISTS qi.esi_trade_hub_prices;

DROP INDEX IF EXISTS qi.idx_emrh_pk;
DROP TABLE IF EXISTS qi.esi_markets_region_history;

DROP INDEX IF EXISTS qi.idx_emp_pk;
DROP TABLE IF EXISTS qi.esi_markets_prices;

---
DROP INDEX IF EXISTS qi.idx_epwt_date;
DROP INDEX IF EXISTS qi.idx_epwt_journal_ref_id;
DROP INDEX IF EXISTS qi.idx_epwt_transaction_id;
DROP INDEX IF EXISTS qi.idx_epwt_character_id;
DROP INDEX IF EXISTS qi.idx_epwt_pk;
DROP TABLE IF EXISTS qi.esi_pilot_wallet_transactions;

DROP INDEX IF EXISTS qi.idx_epwj_date;
DROP INDEX IF EXISTS qi.idx_epwj_context_id;
DROP INDEX IF EXISTS qi.idx_epwj_reference_id;
DROP INDEX IF EXISTS qi.idx_epwj_character_id;
DROP INDEX IF EXISTS qi.idx_epwj_pk;
DROP TABLE IF EXISTS qi.esi_pilot_wallet_journals;

DROP INDEX IF EXISTS qi.idx_epb_location_id;
DROP INDEX IF EXISTS qi.idx_epb_type_id;
DROP INDEX IF EXISTS qi.idx_epb_item_id;
DROP INDEX IF EXISTS qi.idx_epb_character_id;
DROP INDEX IF EXISTS qi.idx_epb_pk;
DROP TABLE IF EXISTS qi.esi_pilot_blueprints;

DROP INDEX IF EXISTS qi.idx_epj_pers_status_activity_id;
DROP INDEX IF EXISTS qi.idx_epj_pers_activity_id;
DROP INDEX IF EXISTS qi.idx_epj_pers_status;
DROP INDEX IF EXISTS qi.idx_epj_blueprint_id;
DROP INDEX IF EXISTS qi.idx_epj_station_id;
DROP INDEX IF EXISTS qi.idx_epj_installer_id;
DROP INDEX IF EXISTS qi.idx_epj_corporation_id;
DROP INDEX IF EXISTS qi.idx_epj_pk;
DROP TABLE IF EXISTS qi.esi_pilot_industry_jobs;

---
DROP INDEX IF EXISTS qi.idx_ecor_corporation_location_id;
DROP INDEX IF EXISTS qi.idx_ecor_history;
DROP INDEX IF EXISTS qi.idx_ecor_issued_by;
DROP INDEX IF EXISTS qi.idx_ecor_issued;
DROP INDEX IF EXISTS qi.idx_ecor_wallet_division;
DROP INDEX IF EXISTS qi.idx_ecor_location_id;
DROP INDEX IF EXISTS qi.idx_ecor_type_id;
DROP INDEX IF EXISTS qi.idx_ecor_corporation_id;
DROP INDEX IF EXISTS qi.idx_ecor_pk;
DROP TABLE IF EXISTS qi.esi_corporation_orders;

DROP TYPE  IF EXISTS qi.esi_order_range;

DROP INDEX IF EXISTS qi.idx_ecwt_date;
DROP INDEX IF EXISTS qi.idx_ecwt_journal_ref_id;
DROP INDEX IF EXISTS qi.idx_ecwt_transaction_id;
DROP INDEX IF EXISTS qi.idx_ecwt_corporation_id;
DROP INDEX IF EXISTS qi.idx_ecwt_pk;
DROP TABLE IF EXISTS qi.esi_corporation_wallet_transactions;

DROP INDEX IF EXISTS qi.idx_ecwj_date;
DROP INDEX IF EXISTS qi.idx_ecwj_context_id;
DROP INDEX IF EXISTS qi.idx_ecwj_reference_id;
DROP INDEX IF EXISTS qi.idx_ecwj_corporation_id;
DROP INDEX IF EXISTS qi.idx_ecwj_pk;
DROP TABLE IF EXISTS qi.esi_corporation_wallet_journals;

DROP INDEX IF EXISTS qi.idx_ebc_created_at;
DROP INDEX IF EXISTS qi.idx_ebc_transaction_type;
DROP INDEX IF EXISTS qi.idx_ebc_job_activity;
DROP INDEX IF EXISTS qi.idx_ebc_job_product_type_id;
DROP INDEX IF EXISTS qi.idx_ebc_blueprint_type_id;
DROP INDEX IF EXISTS qi.idx_ebc_blueprint_job_ids;
DROP INDEX IF EXISTS qi.idx_ebc_job_id;
DROP INDEX IF EXISTS qi.idx_ebc_blueprint_id;
DROP INDEX IF EXISTS qi.idx_ebc_pk;
DROP TABLE IF EXISTS qi.esi_blueprint_costs;
DROP SEQUENCE IF EXISTS qi.seq_ebc;

DROP INDEX IF EXISTS qi.idx_ecj_corp_status_activity_id;
DROP INDEX IF EXISTS qi.idx_ecj_corp_activity_id;
DROP INDEX IF EXISTS qi.idx_ecj_corp_status;
DROP INDEX IF EXISTS qi.idx_ecj_blueprint_id;
DROP INDEX IF EXISTS qi.idx_ecj_location_id;
DROP INDEX IF EXISTS qi.idx_ecj_installer_id;
DROP INDEX IF EXISTS qi.idx_ecj_corporation_id;
DROP INDEX IF EXISTS qi.idx_ecj_pk;
DROP TABLE IF EXISTS qi.esi_corporation_industry_jobs;

DROP TYPE  IF EXISTS qi.esi_job_status;

DROP INDEX IF EXISTS qi.idx_ecb_location_id;
DROP INDEX IF EXISTS qi.idx_ecb_type_id;
DROP INDEX IF EXISTS qi.idx_ecb_item_id;
DROP INDEX IF EXISTS qi.idx_ecb_corporation_id;
DROP INDEX IF EXISTS qi.idx_ecb_pk;
DROP TABLE IF EXISTS qi.esi_corporation_blueprints;

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

DROP INDEX IF EXISTS qi.idx_ech_corporation_id;
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
	ech_corporation_id BIGINT NOT NULL,
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

CREATE INDEX idx_ech_corporation_id
    ON qi.esi_characters USING btree
    (ech_corporation_id ASC NULLS LAST)
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
    eus_owner_id BIGINT,
    eus_system_id INTEGER NOT NULL,
    eus_type_id INTEGER,
    eus_x DOUBLE PRECISION NOT NULL,
    eus_y DOUBLE PRECISION NOT NULL,
    eus_z DOUBLE PRECISION NOT NULL,
    eus_forbidden BOOLEAN,
    eus_created_at TIMESTAMP,
    eus_updated_at TIMESTAMP,
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
    -- ecs_fuel_expires TIMESTAMP,
    -- ecs_state_timer_start TIMESTAMP,
    -- ecs_state_timer_end TIMESTAMP,
    -- ecs_unanchors_at TIMESTAMP,
    -- ecs_state enum('anchor_vulnerable','anchoring','armor_reinforce','armor_vulnerable','fitting_invulnerable','hull_reinforce','hull_vulnerable','online_deprecated','onlining_vulnerable','shield_vulnerable','unanchored','unknown') NOT NULL,
    -- ecs_reinforce_weekday INTEGER,
    -- ecs_reinforce_hour INTEGER NOT NULL,
    -- ecs_next_reinforce_weekday INTEGER,
    -- ecs_next_reinforce_hour INTEGER,
    -- ecs_next_reinforce_apply TIMESTAMP,
    ecs_created_at TIMESTAMP,
    ecs_updated_at TIMESTAMP,
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


--------------------------------------------------------------------------------
-- esi_corporation_blueprints
-- список корпоративных чертежей
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_corporation_blueprints
(
    ecb_corporation_id BIGINT NOT NULL,
    ecb_item_id BIGINT NOT NULL,
    ecb_type_id INTEGER NOT NULL,
    ecb_location_id BIGINT NOT NULL,
    ecb_location_flag CHARACTER VARYING(255) NOT NULL,
    ecb_quantity INTEGER NOT NULL,
    ecb_time_efficiency SMALLINT NOT NULL,
    ecb_material_efficiency SMALLINT NOT NULL,
    ecb_runs INTEGER NOT NULL,
    ecb_created_at TIMESTAMP,
    ecb_updated_at TIMESTAMP,
    CONSTRAINT pk_ecb PRIMARY KEY (ecb_corporation_id,ecb_item_id),
    CONSTRAINT fk_ecb_corporation_id FOREIGN KEY (ecb_corporation_id)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_corporation_blueprints OWNER TO qi_user;

CREATE UNIQUE INDEX idx_ecb_pk
    ON qi.esi_corporation_blueprints USING btree
    (ecb_corporation_id ASC NULLS LAST, ecb_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecb_corporation_id
    ON qi.esi_corporation_blueprints USING btree
    (ecb_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecb_item_id
    ON qi.esi_corporation_blueprints USING btree
    (ecb_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecb_type_id
    ON qi.esi_corporation_blueprints USING btree
    (ecb_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecb_location_id
    ON qi.esi_corporation_blueprints USING btree
    (ecb_location_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- corporation_industry_jobs
-- список корпоративных производственных работ
--------------------------------------------------------------------------------
CREATE TYPE qi.esi_job_status AS ENUM ('active','cancelled','delivered','paused','ready','reverted');

CREATE TABLE qi.esi_corporation_industry_jobs
(
    ecj_corporation_id BIGINT NOT NULL,
    ecj_job_id BIGINT NOT NULL,
    ecj_installer_id BIGINT NOT NULL,
    ecj_facility_id BIGINT NOT NULL,
    ecj_location_id BIGINT NOT NULL,
    ecj_activity_id INTEGER NOT NULL,
    ecj_blueprint_id BIGINT NOT NULL,
    ecj_blueprint_type_id INTEGER NOT NULL,
    ecj_blueprint_location_id BIGINT NOT NULL,
    ecj_output_location_id BIGINT NOT NULL,
    ecj_runs INTEGER NOT NULL,
    ecj_cost DOUBLE PRECISION,
    ecj_licensed_runs INTEGER,
    ecj_probability DOUBLE PRECISION,
    ecj_product_type_id INTEGER,
    ecj_status qi.esi_job_status NOT NULL,
    ecj_duration INTEGER NOT NULL,
    ecj_start_date TIMESTAMP NOT NULL,
    ecj_end_date TIMESTAMP NOT NULL,
    ecj_pause_date TIMESTAMP,
    ecj_completed_date TIMESTAMP,
    ecj_completed_character_id INTEGER,
    ecj_successful_runs INTEGER,
    ecj_created_at TIMESTAMP,
    ecj_updated_at TIMESTAMP,
    CONSTRAINT pk_ecj PRIMARY KEY (ecj_job_id),
    CONSTRAINT fk_ecj_corporation_id FOREIGN KEY (ecj_corporation_id)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_corporation_industry_jobs OWNER TO qi_user;

CREATE UNIQUE INDEX idx_ecj_pk
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_job_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecj_corporation_id
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecj_installer_id
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_installer_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecj_location_id
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_location_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecj_blueprint_id
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_blueprint_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecj_corp_status
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_corporation_id ASC NULLS LAST, ecj_status ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecj_corp_activity_id
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_corporation_id ASC NULLS LAST, ecj_activity_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecj_corp_status_activity_id
    ON qi.esi_corporation_industry_jobs USING btree
    (ecj_corporation_id ASC NULLS LAST, ecj_status ASC NULLS LAST, ecj_activity_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- corporation_blueprint_costs
-- список идентификаторов чертежей и идентификаторов job-ов с получения сведений
-- о том, в результате какой работы был получен чертёж? (попытка дедуктивным
-- способом восстановить связь blueprint_id и job_id)
-- внимание! всякий job_id имеет валидное значение только в рамках corporation_id,
-- но это не означает, что чертёж принадлежит указанной корпорации, т.к. может
-- быть передан
--------------------------------------------------------------------------------
CREATE SEQUENCE qi.seq_ebc
    INCREMENT 1
    START 1000
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

ALTER SEQUENCE qi.seq_ebc OWNER TO qi_user;

CREATE TABLE qi.esi_blueprint_costs
(
    ebc_id BIGINT NOT NULL DEFAULT NEXTVAL('qi.seq_ebc'::regclass),
    ebc_system_id BIGINT,                   -- солнечная система, где была обнаружена либо работа, либо чертёж
    ebc_transaction_type CHAR(1) NOT NULL,  -- тип операции: A - just added БП, C - changed БП, D - deleted БП; f - delivered job, j - active job, d - cancelled job, p - processed job
    -- базовые сведения о чертеже, который был получен в результате копирки или инвента
    ebc_blueprint_id BIGINT,
    ebc_blueprint_type_id INTEGER NOT NULL,
    ebc_blueprint_runs INTEGER NOT NULL,    -- кол-во прогонов БП (свойство чертежа, который будет сгенерирован)
    ebc_time_efficiency SMALLINT,
    ebc_material_efficiency SMALLINT,
    -- сведения о выполненной работе, в результате которой получен чертёж
    ebc_job_id BIGINT,
    ebc_job_corporation_id BIGINT,          -- идентификатор нужен для получения уникального номера работы в рамках каждой из корпораций
    ebc_job_activity INTEGER,               -- 5: copy, 8: invent
    ebc_job_runs INTEGER,                   -- кол-во job-ов (сколько штук новых чертежей будет сгенерировано) - меняется в процессе поиска чертежей
    ebc_job_product_type_id INTEGER,        -- что именно будет получено в результате job-а
    ebc_job_successful_runs INTEGER,        -- кол-во job-ов, которые завершились успешно (от 0 до job_runs) - меняется в процессе поиска чертежей
    ebc_job_time_efficiency SMALLINT,       -- me параметр чертежа, использованного в работе job_id (невполне точный параметр, т.к. меняется несинхронно получению данных)
    ebc_job_material_efficiency SMALLINT,   -- te параметр чертежа, использованного в работе job_id (невполне точный параметр, т.к. меняется несинхронно получению данных)
    -- слагаемые стоимости выполенной работы (из журнала транзакций корпкошелька, базовая job cost берётся из журнала производства)
    ebc_industry_payment INTEGER,
    ebc_tax INTEGER,
    -- когда создана и актуализирована запись
    ebc_created_at TIMESTAMP,
    ebc_updated_at TIMESTAMP,
    CONSTRAINT pk_ebc PRIMARY KEY (ebc_id)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_ebc_pk
    ON qi.esi_blueprint_costs USING btree
    (ebc_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_blueprint_id
    ON qi.esi_blueprint_costs USING btree
    (ebc_blueprint_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_job_id
    ON qi.esi_blueprint_costs USING btree
    (ebc_job_id ASC NULLS LAST, ebc_job_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_blueprint_job_ids
    ON qi.esi_blueprint_costs USING btree
    (ebc_blueprint_id ASC NULLS LAST, ebc_job_id ASC NULLS LAST, ebc_job_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_blueprint_type_id
    ON qi.esi_blueprint_costs USING btree
    (ebc_blueprint_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_job_product_type_id
    ON qi.esi_blueprint_costs USING btree
    (ebc_job_product_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_job_activity
    ON qi.esi_blueprint_costs USING btree
    (ebc_job_activity ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_transaction_type
    ON qi.esi_blueprint_costs USING btree
    (ebc_transaction_type ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ebc_created_at
    ON qi.esi_blueprint_costs USING btree
    (ebc_created_at ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- corporation_wallet_journals
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_corporation_wallet_journals
(
    ecwj_corporation_id BIGINT NOT NULL,
    ecwj_division SMALLINT NOT NULL,
    ecwj_reference_id BIGINT NOT NULL,
    ecwj_date TIMESTAMP NOT NULL,
    ecwj_ref_type CHARACTER VARYING(255) NOT NULL,
    ecwj_first_party_id BIGINT,
    ecwj_second_party_id BIGINT,
    ecwj_amount DOUBLE PRECISION,
    ecwj_balance DOUBLE PRECISION,
    ecwj_reason TEXT,
    ecwj_tax_receiver_id BIGINT,
    ecwj_tax DOUBLE PRECISION,
    ecwj_context_id BIGINT,
    ecwj_context_id_type CHARACTER VARYING(255),
    ecwj_description CHARACTER VARYING(255) NOT NULL,
    ecwj_created_at TIMESTAMP,
    CONSTRAINT pk_ecwj PRIMARY KEY (ecwj_corporation_id, ecwj_division, ecwj_reference_id),
    CONSTRAINT fk_ecwj_corporation_id FOREIGN KEY (ecwj_corporation_id)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_ecwj_pk
    ON qi.esi_corporation_wallet_journals USING btree
    (ecwj_corporation_id ASC NULLS LAST, ecwj_division ASC NULLS LAST, ecwj_reference_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwj_corporation_id
    ON qi.esi_corporation_wallet_journals USING btree
    (ecwj_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwj_reference_id
    ON qi.esi_corporation_wallet_journals USING btree
    (ecwj_reference_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwj_context_id
    ON qi.esi_corporation_wallet_journals USING btree
    (ecwj_context_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwj_date
    ON qi.esi_corporation_wallet_journals USING btree
    (ecwj_date ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- corporation_wallet_transactions
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_corporation_wallet_transactions
(
    ecwt_corporation_id BIGINT NOT NULL,
    ecwt_division SMALLINT NOT NULL,
    ecwt_transaction_id BIGINT NOT NULL,
    ecwt_date TIMESTAMP NOT NULL,
    ecwt_type_id INTEGER NOT NULL,
    ecwt_location_id BIGINT NOT NULL,
    ecwt_unit_price DOUBLE PRECISION NOT NULL,
    ecwt_quantity INTEGER NOT NULL,
    ecwt_client_id INTEGER NOT NULL,
    ecwt_is_buy BOOLEAN NOT NULL,
    ecwt_journal_ref_id BIGINT NOT NULL,
    ecwt_created_at TIMESTAMP,
    CONSTRAINT pk_ecwt PRIMARY KEY (ecwt_corporation_id, ecwt_division, ecwt_transaction_id),
    CONSTRAINT fk_ecwt_corporation_id FOREIGN KEY (ecwt_corporation_id)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_ecwt_pk
    ON qi.esi_corporation_wallet_transactions USING btree
    (ecwt_corporation_id ASC NULLS LAST, ecwt_division ASC NULLS LAST, ecwt_transaction_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwt_corporation_id
    ON qi.esi_corporation_wallet_transactions USING btree
    (ecwt_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwt_transaction_id
    ON qi.esi_corporation_wallet_transactions USING btree
    (ecwt_transaction_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwt_journal_ref_id
    ON qi.esi_corporation_wallet_transactions USING btree
    (ecwt_journal_ref_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecwt_date
    ON qi.esi_corporation_wallet_transactions USING btree
    (ecwt_date ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- corporation_orders
--------------------------------------------------------------------------------
CREATE TYPE qi.esi_order_range AS ENUM ('station', 'region', 'solarsystem', '1', '2', '3', '4', '5', '10', '20', '30', '40');

-- у ордера с течением времени может меняться (см. табл. esi_trade_hub_orders и esi_corporation_orders):
--  1. price меняется вместе с issued (order_id остаётся прежним)
--  2. volume_remain меняется при покупке/продаже по order-у
-- при этом total не меняется, даже если remain <> total при изменении price !
--
-- с историей изменении order-а синхронизируется (см. табл. esi_trade_hub_history):
--  1. изменённая цена price
--  2. остаток непроданных товаров volume_remain
-- при этом issued не изменяется, - остаётся прежним (соответствует открытию order-а)
CREATE TABLE qi.esi_corporation_orders
(
    ecor_corporation_id BIGINT NOT NULL,
    ecor_order_id BIGINT NOT NULL,
    ecor_type_id INTEGER NOT NULL,
    ecor_region_id INTEGER NOT NULL,
    ecor_location_id BIGINT NOT NULL,
    ecor_range qi.esi_order_range NOT NULL,
    ecor_is_buy_order BOOLEAN NOT NULL,
    ecor_price DOUBLE PRECISION NOT NULL,
    ecor_volume_total INTEGER NOT NULL,
    ecor_volume_remain INTEGER NOT NULL,
    ecor_issued TIMESTAMP NOT NULL,
    ecor_issued_by BIGINT NOT NULL,
    ecor_min_volume INTEGER,
    ecor_wallet_division INTEGER,
    ecor_duration INTEGER,
    ecor_escrow DOUBLE PRECISION,
    ecor_history BOOLEAN NOT NULL,
    ecor_created_at TIMESTAMP,
    ecor_updated_at TIMESTAMP,
    CONSTRAINT pk_ecor PRIMARY KEY (ecor_corporation_id, ecor_order_id),
    CONSTRAINT fk_ecor_corporation_id FOREIGN KEY (ecor_corporation_id)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_ecor_pk
    ON qi.esi_corporation_orders USING btree
    (ecor_corporation_id ASC NULLS LAST, ecor_order_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_corporation_id
    ON qi.esi_corporation_orders USING btree
    (ecor_corporation_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_type_id
    ON qi.esi_corporation_orders USING btree
    (ecor_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_location_id
    ON qi.esi_corporation_orders USING btree
    (ecor_location_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_wallet_division
    ON qi.esi_corporation_orders USING btree
    (ecor_wallet_division ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_issued
    ON qi.esi_corporation_orders USING btree
    (ecor_issued ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_issued_by
    ON qi.esi_corporation_orders USING btree
    (ecor_issued_by ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_history
    ON qi.esi_corporation_orders USING btree
    (ecor_history ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ecor_corporation_location_id
    ON qi.esi_corporation_orders USING btree
    (ecor_corporation_id ASC NULLS LAST, ecor_location_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------




--------------------------------------------------------------------------------
-- character_industry_jobs
-- список персональных производственных работ
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_pilot_industry_jobs
(
    epj_character_id BIGINT NOT NULL,
    epj_job_id BIGINT NOT NULL,
    epj_installer_id BIGINT NOT NULL,
    epj_facility_id BIGINT NOT NULL,
    epj_station_id BIGINT NOT NULL,
    epj_activity_id INTEGER NOT NULL,
    epj_blueprint_id BIGINT NOT NULL,
    epj_blueprint_type_id INTEGER NOT NULL,
    epj_blueprint_location_id BIGINT NOT NULL,
    epj_output_location_id BIGINT NOT NULL,
    epj_runs INTEGER NOT NULL,
    epj_cost DOUBLE PRECISION,
    epj_licensed_runs INTEGER,
    epj_probability DOUBLE PRECISION,
    epj_product_type_id INTEGER,
    epj_status qi.esi_job_status NOT NULL,
    epj_duration INTEGER NOT NULL,
    epj_start_date TIMESTAMP NOT NULL,
    epj_end_date TIMESTAMP NOT NULL,
    epj_pause_date TIMESTAMP,
    epj_completed_date TIMESTAMP,
    epj_completed_character_id INTEGER,
    epj_successful_runs INTEGER,
    epj_created_at TIMESTAMP,
    epj_updated_at TIMESTAMP,
    CONSTRAINT pk_epj PRIMARY KEY (epj_job_id),
    CONSTRAINT fk_epj_character_id FOREIGN KEY (epj_character_id)
        REFERENCES qi.esi_characters(ech_character_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_pilot_industry_jobs OWNER TO qi_user;

CREATE UNIQUE INDEX idx_epj_pk
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_job_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_character_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_installer_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_installer_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_station_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_station_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_blueprint_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_blueprint_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_pers_status
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST, epj_status ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_pers_activity_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST, epj_activity_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_pers_status_activity_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST, epj_status ASC NULLS LAST, epj_activity_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- esi_character_blueprints
-- список персональных чертежей
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_pilot_blueprints
(
    epb_character_id BIGINT NOT NULL,
    epb_item_id BIGINT NOT NULL,
    epb_type_id INTEGER NOT NULL,
    epb_location_id BIGINT NOT NULL,
    epb_location_flag CHARACTER VARYING(255) NOT NULL,
    epb_quantity INTEGER NOT NULL,
    epb_time_efficiency SMALLINT NOT NULL,
    epb_material_efficiency SMALLINT NOT NULL,
    epb_runs INTEGER NOT NULL,
    epb_created_at TIMESTAMP,
    epb_updated_at TIMESTAMP,
    CONSTRAINT pk_epb PRIMARY KEY (epb_character_id,epb_item_id),
    CONSTRAINT fk_epb_character_id FOREIGN KEY (epb_character_id)
        REFERENCES qi.esi_characters(ech_character_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_pilot_blueprints OWNER TO qi_user;

CREATE UNIQUE INDEX idx_epb_pk
    ON qi.esi_pilot_blueprints USING btree
    (epb_character_id ASC NULLS LAST, epb_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_character_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_character_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_item_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_type_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_location_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_location_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- character_wallet_journals
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_pilot_wallet_journals
(
    epwj_character_id BIGINT NOT NULL,
    epwj_reference_id BIGINT NOT NULL,
    epwj_date TIMESTAMP NOT NULL,
    epwj_ref_type CHARACTER VARYING(255) NOT NULL,
    epwj_first_party_id BIGINT,
    epwj_second_party_id BIGINT,
    epwj_amount DOUBLE PRECISION,
    epwj_balance DOUBLE PRECISION,
    epwj_reason TEXT,
    epwj_tax_receiver_id BIGINT,
    epwj_tax DOUBLE PRECISION,
    epwj_context_id BIGINT,
    epwj_context_id_type CHARACTER VARYING(255),
    epwj_description CHARACTER VARYING(255) NOT NULL,
    epwj_created_at TIMESTAMP,
    CONSTRAINT pk_epwj PRIMARY KEY (epwj_character_id, epwj_reference_id),
    CONSTRAINT fk_epwj_character_id FOREIGN KEY (epwj_character_id)
        REFERENCES qi.esi_characters(ech_character_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_epwj_pk
    ON qi.esi_pilot_wallet_journals USING btree
    (epwj_character_id ASC NULLS LAST, epwj_reference_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwj_character_id
    ON qi.esi_pilot_wallet_journals USING btree
    (epwj_character_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwj_reference_id
    ON qi.esi_pilot_wallet_journals USING btree
    (epwj_reference_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwj_context_id
    ON qi.esi_pilot_wallet_journals USING btree
    (epwj_context_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwj_date
    ON qi.esi_pilot_wallet_journals USING btree
    (epwj_date ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- character_wallet_transactions
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_pilot_wallet_transactions
(
    epwt_character_id BIGINT NOT NULL,
    epwt_transaction_id BIGINT NOT NULL,
    epwt_date TIMESTAMP NOT NULL,
    epwt_type_id INTEGER NOT NULL,
    epwt_location_id BIGINT NOT NULL,
    epwt_unit_price DOUBLE PRECISION NOT NULL,
    epwt_quantity INTEGER NOT NULL,
    epwt_client_id INTEGER NOT NULL,
    epwt_is_buy BOOLEAN NOT NULL,
    epwt_is_personal BOOLEAN NOT NULL,
    epwt_journal_ref_id BIGINT NOT NULL,
    epwt_created_at TIMESTAMP,
    CONSTRAINT pk_epwt PRIMARY KEY (epwt_character_id, epwt_transaction_id),
    CONSTRAINT fk_epwt_character_id FOREIGN KEY (epwt_character_id)
        REFERENCES qi.esi_characters(ech_character_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_epwt_pk
    ON qi.esi_pilot_wallet_transactions USING btree
    (epwt_character_id ASC NULLS LAST, epwt_transaction_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwt_character_id
    ON qi.esi_pilot_wallet_transactions USING btree
    (epwt_character_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwt_transaction_id
    ON qi.esi_pilot_wallet_transactions USING btree
    (epwt_transaction_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwt_journal_ref_id
    ON qi.esi_pilot_wallet_transactions USING btree
    (epwt_journal_ref_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epwt_date
    ON qi.esi_pilot_wallet_transactions USING btree
    (epwt_date ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------




--------------------------------------------------------------------------------
-- markets_prices
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_markets_prices
(
    emp_type_id BIGINT NOT NULL,
    emp_adjusted_price DOUBLE PRECISION,
    emp_average_price DOUBLE PRECISION,
    emp_created_at TIMESTAMP,
    emp_updated_at TIMESTAMP,
    CONSTRAINT pk_emp PRIMARY KEY (emp_type_id)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_emp_pk
    ON qi.esi_markets_prices USING btree
    (emp_type_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- markets_region_history
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_markets_region_history
(
    emrh_region_id INTEGER NOT NULL,
    emrh_type_id BIGINT NOT NULL,
    emrh_date DATE NOT NULL,
    emrh_average DOUBLE PRECISION NOT NULL,
    emrh_highest DOUBLE PRECISION NOT NULL,
    emrh_lowest DOUBLE PRECISION NOT NULL,
    emrh_order_count BIGINT NOT NULL,
    emrh_volume BIGINT NOT NULL,
    CONSTRAINT pk_emrh PRIMARY KEY (emrh_region_id, emrh_type_id, emrh_date)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_emrh_pk
    ON qi.esi_markets_region_history USING btree
    (emrh_region_id ASC NULLS LAST, emrh_type_id ASC NULLS LAST, emrh_date ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- /markets/region_id/orders/
-- /markets/structures/structure_id/
--------------------------------------------------------------------------------
CREATE TABLE qi.esi_trade_hub_prices
(
    ethp_location_id BIGINT NOT NULL,
    ethp_type_id BIGINT NOT NULL,
    ethp_sell DOUBLE PRECISION,
    ethp_buy DOUBLE PRECISION,
    ethp_sell_volume BIGINT NOT NULL,
    ethp_buy_volume BIGINT NOT NULL,
    ethp_created_at TIMESTAMP,
    ethp_updated_at TIMESTAMP,
    CONSTRAINT pk_ethp PRIMARY KEY (ethp_location_id, ethp_type_id)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_ethp_pk
    ON qi.esi_trade_hub_prices USING btree
    (ethp_location_id ASC NULLS LAST, ethp_type_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------
-- у ордера с течением времени может меняться (см. табл. esi_trade_hub_orders и esi_corporation_orders):
--  1. price меняется вместе с issued (order_id остаётся прежним)
--  2. volume_remain меняется при покупке/продаже по order-у
-- при этом total не меняется, даже если remain <> total при изменении price !
--
-- с историей изменении order-а синхронизируется (см. табл. esi_trade_hub_history):
--  1. изменённая цена price
--  2. остаток непроданных товаров volume_remain
-- при этом issued не изменяется, - остаётся прежним (соответствует открытию order-а)
CREATE TABLE qi.esi_trade_hub_orders
(
    etho_location_id BIGINT NOT NULL,
    etho_order_id BIGINT NOT NULL,
    etho_type_id BIGINT NOT NULL,
    etho_duration INTEGER NOT NULL,
    etho_is_buy BOOLEAN NOT NULL,
    etho_issued TIMESTAMP NOT NULL,
    etho_min_volume INTEGER NOT NULL,
    etho_price DOUBLE PRECISION NOT NULL,
    etho_range qi.esi_order_range NOT NULL,
    etho_volume_remain INTEGER NOT NULL,
    etho_volume_total INTEGER NOT NULL,
    etho_created_at TIMESTAMP,
    etho_updated_at TIMESTAMP,
    CONSTRAINT pk_etho PRIMARY KEY (etho_location_id, etho_order_id)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_etho_pk
    ON qi.esi_trade_hub_orders USING btree
    (etho_location_id ASC NULLS LAST, etho_order_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_etho_location_id
    ON qi.esi_trade_hub_orders USING btree
    (etho_location_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_etho_type_id
    ON qi.esi_trade_hub_orders USING btree
    (etho_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_etho_location_type_id
    ON qi.esi_trade_hub_orders USING btree
    (etho_location_id ASC NULLS LAST, etho_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_etho_location_is_buy
    ON qi.esi_trade_hub_orders USING btree
    (etho_location_id ASC NULLS LAST, etho_is_buy ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_etho_issued
    ON qi.esi_trade_hub_orders USING btree
    (etho_issued ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------
-- у ордера с течением времени может меняться (см. табл. esi_trade_hub_orders и esi_corporation_orders):
--  1. price меняется вместе с issued (order_id остаётся прежним)
--  2. volume_remain меняется при покупке/продаже по order-у
-- при этом total не меняется, даже если remain <> total при изменении price !
--
-- с историей изменении order-а синхронизируется (см. табл. esi_trade_hub_history):
--  1. изменённая цена price
--  2. остаток непроданных товаров volume_remain
-- при этом issued не изменяется, - остаётся прежним (соответствует открытию order-а)
CREATE TABLE qi.esi_trade_hub_history
(
    ethh_location_id BIGINT NOT NULL,
    ethh_order_id BIGINT NOT NULL,
    ethh_type_id BIGINT NOT NULL,
    ethh_is_buy BOOLEAN NOT NULL,
    ethh_issued TIMESTAMP NOT NULL,
    ethh_price DOUBLE PRECISION NOT NULL,
    ethh_volume_remain INTEGER NOT NULL, -- esi не отдаёт историю order-ов, т.ч. если order будет отмёнён с remain<>0, то об этом
    ethh_volume_total INTEGER NOT NULL, -- ... никогда точно нельзя будет узнать (remain хранит остаток, когда order исчезнет)
    ethh_done TIMESTAMP, -- если done is not null, то order закрылся
    ethh_updated_at TIMESTAMP,
    CONSTRAINT pk_ethh PRIMARY KEY (ethh_location_id, ethh_order_id)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_ethh_pk
    ON qi.esi_trade_hub_history USING btree
    (ethh_location_id ASC NULLS LAST, ethh_order_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ethh_location_id
    ON qi.esi_trade_hub_history USING btree
    (ethh_location_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ethh_type_id
    ON qi.esi_trade_hub_history USING btree
    (ethh_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ethh_location_type_id
    ON qi.esi_trade_hub_history USING btree
    (ethh_location_id ASC NULLS LAST, ethh_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ethh_location_is_buy
    ON qi.esi_trade_hub_history USING btree
    (ethh_location_id ASC NULLS LAST, ethh_is_buy ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ethh_issued
    ON qi.esi_trade_hub_history USING btree
    (ethh_issued ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_ethh_updated_at
    ON qi.esi_trade_hub_history USING btree
    (ethh_updated_at ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.
