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


DROP INDEX IF EXISTS qi.idx_sdebm_fk;
DROP TABLE IF EXISTS qi.eve_sde_blueprint_materials;
DROP INDEX IF EXISTS qi.idx_sdebp_fk;
DROP TABLE IF EXISTS qi.eve_sde_blueprint_products;
DROP INDEX IF EXISTS qi.idx_sdeb_pk;
DROP TABLE IF EXISTS qi.eve_sde_blueprints;

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

--------------------------------------------------------------------------------
-- EVE Static Data Interface (Blueprints)
-- сведения о запуске производственных работ, из blueprints.yaml
--------------------------------------------------------------------------------
CREATE TABLE qi.eve_sde_blueprints
(
    sdeb_blueprint_type_id INTEGER NOT NULL,
    sdeb_activity SMALLINT NOT NULL,
    sdeb_time INTEGER NOT NULL,
    CONSTRAINT pk_sdeb PRIMARY KEY (sdeb_blueprint_type_id,sdeb_activity)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_sdeb_pk
    ON qi.eve_sde_blueprints USING btree
    (sdeb_blueprint_type_id ASC NULLS LAST, sdeb_activity ASC NULLS LAST)
TABLESPACE pg_default;


CREATE TABLE qi.eve_sde_blueprint_products
(
    sdebp_blueprint_type_id INTEGER NOT NULL,
    sdebp_activity SMALLINT NOT NULL,
    sdebp_product_id INTEGER NOT NULL,
    sdebp_quantity INTEGER NOT NULL,
    sdebp_probability DOUBLE PRECISION,
    CONSTRAINT fk_sdebp FOREIGN KEY (sdebp_blueprint_type_id,sdebp_activity)
        REFERENCES qi.eve_sde_blueprints(sdeb_blueprint_type_id,sdeb_activity) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

CREATE INDEX idx_sdebp_fk
    ON qi.eve_sde_blueprint_products USING btree
    (sdebp_blueprint_type_id ASC NULLS LAST, sdebp_activity ASC NULLS LAST)
TABLESPACE pg_default;


CREATE TABLE qi.eve_sde_blueprint_materials
(
    sdebm_blueprint_type_id INTEGER NOT NULL,
    sdebm_activity SMALLINT NOT NULL,
    sdebm_material_id INTEGER NOT NULL,
    sdebm_quantity INTEGER NOT NULL,
    CONSTRAINT fk_sdebm FOREIGN KEY (sdebm_blueprint_type_id,sdebm_activity)
        REFERENCES qi.eve_sde_blueprints(sdeb_blueprint_type_id,sdeb_activity) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

CREATE INDEX idx_sdebm_fk
    ON qi.eve_sde_blueprint_materials USING btree
    (sdebm_blueprint_type_id ASC NULLS LAST, sdebm_activity ASC NULLS LAST)
TABLESPACE pg_default;


ALTER TABLE qi.eve_sde_blueprints OWNER TO qi_user;
ALTER TABLE qi.eve_sde_blueprint_products OWNER TO qi_user;
ALTER TABLE qi.eve_sde_blueprint_materials OWNER TO qi_user;
--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.