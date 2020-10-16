-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя msc
-- скрипт создаёт в базе данных таблицы, секвенторы, индексы

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;

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
    CONSTRAINT pk_wfc PRIMARY KEY (wfc_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.workflow_factory_containers OWNER TO qi_user;

CREATE UNIQUE INDEX idx_wfc_pk
    ON qi.workflow_factory_containers USING btree
    (wfc_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


-- получаем справку в конце выполнения всех запросов
\d+ qi.