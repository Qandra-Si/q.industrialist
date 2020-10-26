-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы, секвенторы, индексы

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;

DROP INDEX IF EXISTS qi.idx_wij_bp_tid;
DROP INDEX IF EXISTS qi.idx_wij_bp_id;
DROP INDEX IF EXISTS qi.idx_wij_pk;
DROP TABLE IF EXISTS qi.workflow_industry_jobs;

DROP INDEX IF EXISTS qi.idx_wfc_pk;
DROP TABLE IF EXISTS qi.workflow_factory_containers;

DROP INDEX IF EXISTS qi.idx_wmj_pk;
DROP TABLE IF EXISTS qi.workflow_monthly_jobs;
DROP SEQUENCE IF EXISTS qi.seq_wmj;

DROP INDEX IF EXISTS qi.idx_ms_unq_module_key;
DROP INDEX IF EXISTS qi.idx_ms_fk_module;
DROP TABLE IF EXISTS qi.modules_settings;

DROP INDEX IF EXISTS qi.idx_ml_pk;
DROP TABLE IF EXISTS qi.modules_list;
DROP SEQUENCE IF EXISTS qi.seq_ml;


--------------------------------------------------------------------------------
-- modules_list
-- справочник со списком модулей
--------------------------------------------------------------------------------
CREATE SEQUENCE qi.seq_ml
    INCREMENT 1
    START 1000
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE qi.seq_ml OWNER TO qi_user;

CREATE TABLE qi.modules_list
(
    ml_id INTEGER NOT NULL DEFAULT NEXTVAL('qi.seq_ml'::regclass),
    ml_name CHARACTER VARYING(63) NOT NULL, -- наименование модуля программного обеспечения Q.Industrialist
    CONSTRAINT pk_ml PRIMARY KEY (ml_id),
    CONSTRAINT unq_ml_name UNIQUE (ml_name)
)
TABLESPACE pg_default;

ALTER TABLE qi.modules_list OWNER TO qi_user;

CREATE UNIQUE INDEX idx_ml_pk
    ON qi.modules_list USING btree
    (ml_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- modules_settings
-- список произвольных key:value пар, являющимися настройками работы модулей
--------------------------------------------------------------------------------
CREATE TABLE qi.modules_settings
(
    ms_module INTEGER NOT NULL,
    ms_key CHARACTER VARYING(63) NOT NULL, -- ключ
    ms_val CHARACTER VARYING(1023), -- значение
    CONSTRAINT fk_ms_module FOREIGN KEY (ms_module)
        REFERENCES qi.modules_list(ml_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
TABLESPACE pg_default;

ALTER TABLE qi.modules_settings OWNER TO qi_user;

CREATE INDEX idx_ms_fk_module
    ON qi.modules_settings USING btree
    (ms_module ASC NULLS LAST)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_ms_unq_module_key
    ON qi.modules_settings USING btree
    (ms_module ASC NULLS LAST, ms_key ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- workflow_monthly_jobs
-- список фитов, запланированных к ежемесячному производству
--------------------------------------------------------------------------------
CREATE SEQUENCE qi.seq_wmj
    INCREMENT 1
    START 1000
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE qi.seq_wmj OWNER TO qi_user;

CREATE TABLE qi.workflow_monthly_jobs
(
    wmj_id INTEGER NOT NULL DEFAULT NEXTVAL('qi.seq_wmj'::regclass),
    wmj_active BOOLEAN NOT NULL DEFAULT TRUE, -- фит запланирован к производству (запись активна), иначе по ней план не составляется
    wmj_quantity INTEGER NOT NULL, -- кол-во кораблей (фитов) запланированных для ежемесячного производства
    wmj_eft CHARACTER VARYING(16383), -- 16 Кб для текстового представления фита (очень много всего в карго?)
    wmj_remarks CHARACTER VARYING(127), -- дополнительная информация
    wmj_conveyor NOT NULL DEFAULT FALSE, -- признак того, что список модулей предназначаен для производства на конвейере
    CONSTRAINT pk_wmj PRIMARY KEY (wmj_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.workflow_monthly_jobs OWNER TO qi_user;

CREATE UNIQUE INDEX idx_wmj_pk
    ON qi.workflow_monthly_jobs USING btree
    (wmj_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- workflow_factory_containers
-- список контейнеров в которых выполняется поиск чертежей
--------------------------------------------------------------------------------
CREATE TABLE qi.workflow_factory_containers
(
    wfc_id BIGINT NOT NULL, -- идентификатор контейнера
    wfc_name CHARACTER VARYING(63), -- наименование контейнера (может устаревать, нужен для сигнализации)
    wfc_active BOOLEAN NOT NULL DEFAULT TRUE, -- признак использования контейнера (отключенные нужны для наблюдения содержимого заданных ангаров)
    wfc_disabled BOOLEAN NOT NULL DEFAULT FALSE, -- признак отсутствия контейнера в ангаре (был перемещён, и актуализирован как "сейчас отсутствует")
    CONSTRAINT pk_wfc PRIMARY KEY (wfc_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.workflow_factory_containers OWNER TO qi_user;

CREATE UNIQUE INDEX idx_wfc_pk
    ON qi.workflow_factory_containers USING btree
    (wfc_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- workflow_industry_jobs
-- список работ по производству, которые выполнены корпорацией
--------------------------------------------------------------------------------
CREATE TABLE qi.workflow_industry_jobs
(
    wij_job_id INTEGER NOT NULL,            -- job_id*                integer($int32)
    wij_activity_id INTEGER NOT NULL,       -- activity_id*           integer($int32)
    wij_cost DOUBLE PRECISION,              -- cost                   number($double)
    wij_duration INTEGER NOT NULL,          -- duration*              integer($int32)
    wij_runs INTEGER NOT NULL,              -- runs*                  integer($int32)
                                            -- licensed_runs          integer($int32)
                                            -- successful_runs        integer($int32)
    wij_product_tid INTEGER,                -- product_type_id        integer($int32)
    wij_bp_id BIGINT NOT NULL,              -- blueprint_id*          integer($int64)
    wij_bp_tid INTEGER NOT NULL,            -- blueprint_type_id*     integer($int32)
    wij_bp_lid BIGINT NOT NULL,             -- blueprint_location_id* integer($int64)
    wij_lid BIGINT NOT NULL,                -- location_id*           integer($int64)
    wij_out_lid BIGINT NOT NULL,            -- output_location_id*    integer($int64)
    wij_facility_id BIGINT NOT NULL,        -- facility_id*           integer($int64)
    wij_installer_id BIGINT NOT NULL,       -- installer_id*          integer($int32)
                                            -- completed_character_id integer($int32)
                                            -- completed_date         string($date-time)
    wij_start_date TIMESTAMP NOT NULL,      -- start_date*            string($date-time)
                                            -- pause_date             string($date-time)
    wij_end_date TIMESTAMP NOT NULL,        -- end_date*              string($date-time)
                                            -- probability            number($float)
                                            -- status*                string
    CONSTRAINT pk_wij PRIMARY KEY (wij_job_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.workflow_industry_jobs OWNER TO qi_user;

CREATE UNIQUE INDEX idx_wij_pk
    ON qi.workflow_industry_jobs USING btree
    (wij_job_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_wij_bp_id
    ON qi.workflow_industry_jobs USING btree
    (wij_bp_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_wij_bp_tid
    ON qi.workflow_industry_jobs USING btree
    (wij_bp_tid ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


-- получаем справку в конце выполнения всех запросов
\d+ qi.