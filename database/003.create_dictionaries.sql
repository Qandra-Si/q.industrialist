-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы, секвенторы, индексы
-- Категории:
--  0 = NAMES =    fsd/metaGroups.yaml
--  1 = NAMES =    fsd/typeIDs.yaml
--  2 = NAMES =    fsd/marketGroups.yaml
--  3 = NAMES =    bsd/invNames.yaml
--  4 = NAMES =    industry jobs activity_id
--  5 = INTEGERS = fsd/blueprints.yaml (activities | manufacturing | products | quantity)
--  6 = INTEGERS = fsd/blueprints.yaml (activities | invention | products | quantity)
--  7 = INTEGERS = fsd/blueprints.yaml (activities | reaction | products | quantity)


CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;

DROP INDEX IF EXISTS qi.idx_sdei_pk;
DROP TABLE IF EXISTS qi.eve_sde_integers;

DROP INDEX IF EXISTS qi.idx_sden_pk;
DROP TABLE IF EXISTS qi.eve_sde_names;


--------------------------------------------------------------------------------
-- EVE Static Data Interface (Names)
-- список произвольных key:value пар, являющимися наименованиями
--------------------------------------------------------------------------------
CREATE TABLE qi.eve_sde_names
(
    sden_category INTEGER NOT NULL,
    sden_id INTEGER NOT NULL,
    sden_name CHARACTER VARYING(255),
    CONSTRAINT pk_sden PRIMARY KEY (sden_category,sden_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.eve_sde_names OWNER TO qi_user;

CREATE UNIQUE INDEX idx_sden_pk
    ON qi.eve_sde_names USING btree
    (sden_category ASC NULLS LAST, sden_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- EVE Static Data Interface (Integers)
-- список произвольных key:value пар, являющимися числами
--------------------------------------------------------------------------------
CREATE TABLE qi.eve_sde_integers
(
    sdei_category INTEGER NOT NULL,
    sdei_id INTEGER NOT NULL,
    sdei_number INTEGER NOT NULL,
    CONSTRAINT pk_sdei PRIMARY KEY (sdei_category,sdei_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.eve_sde_integers OWNER TO qi_user;

CREATE UNIQUE INDEX idx_sdei_pk
    ON qi.eve_sde_integers USING btree
    (sdei_category ASC NULLS LAST, sdei_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.