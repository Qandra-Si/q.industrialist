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


DROP VIEW IF EXISTS  qi.eve_sde_market_groups_semantic;
DROP VIEW IF EXISTS  qi.eve_sde_market_groups_tree_sorted;
DROP VIEW IF EXISTS  qi.eve_sde_market_groups_tree;
DROP INDEX IF EXISTS qi.idx_sdeg_group_semantic_ids;
DROP INDEX IF EXISTS qi.idx_sdeg_group_parent_ids;
DROP INDEX IF EXISTS qi.idx_sdeg_pk;
DROP TABLE IF EXISTS qi.eve_sde_market_groups;

DROP INDEX IF EXISTS qi.idx_sdet_market_group_id;
DROP INDEX IF EXISTS qi.idx_sdet_pk;
DROP TABLE IF EXISTS qi.eve_sde_type_ids;

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

--------------------------------------------------------------------------------
-- EVE Static Data Interface (typeIDs)
-- сведения о параметрах типах присутствующих в игре элементов, из typeIDs.yaml
--------------------------------------------------------------------------------
CREATE TABLE qi.eve_sde_type_ids
(
    sdet_type_id INTEGER NOT NULL,
    sdet_type_name CHARACTER VARYING(255),
    sdet_volume DOUBLE PRECISION,
    sdet_capacity DOUBLE PRECISION,
    sdet_base_price BIGINT,
    sdet_published BOOLEAN,
    sdet_market_group_id INTEGER,
    sdet_meta_group_id SMALLINT,
    sdet_icon_id INTEGER,
    -- sdet_group_id INTEGER,
    -- sdet_portion_size INTEGER,
    sdet_packaged_volume DOUBLE PRECISION,
    CONSTRAINT pk_sdet PRIMARY KEY (sdet_type_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.eve_sde_type_ids OWNER TO qi_user;

CREATE UNIQUE INDEX idx_sdet_pk
    ON qi.eve_sde_type_ids USING btree
    (sdet_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_sdet_market_group_id
    ON qi.eve_sde_type_ids USING btree
    (sdet_market_group_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- EVE Static Data Interface (marketGroups)
-- сведения о рыночных группых присутствующих в игре, из marketGroups.yaml
--
-- Например:
--  group_id  parent_id  semantic_id  group_name
--  955            NULL          955   Ship and Module Modifications
--    1111          955          955   Rigs
--      ...                        ?
---   2436          955          955   Mutaplasmids
--      ...                        ?
--    1112          955         1112   Subsystems
--      1610       1112         1112   Amarr Subsystems
--        1122     1610         1112   Amarr Core Subsystems
--        1126     1610         1112   Amarr Defensive Subsystems
--        1130     1610         1112   Amarr Offensive Subsystems
--        1134     1610         1112   Amarr Propulsion Subsystems
--      1625       1112         1112   Caldari Subsystems
--        ...                   1112
--      1626       1112         1112   Minmatar Subsystems
--        ...                   1112
--      1627       1112         1112   Gallente Subsystems
--        ...                   1112
--
-- Например:
--  group_id  parent_id  semantic_id  group_name
--  475            NULL          475  Manufacture & Research
--    533           475          533  Materials
--      1031        533          533  Raw Materials
--        54       1031          533  Standard Ores
--          512      54          533  Arkonor
--          ...      54          533  Bistot, Pyroxeres, ...
--        ...      1031          533  Ice Ores, Moon Ores, Alloys & Compounds, ...
--      ...         533          533  Gas Clouds Materials, Ice Products, ...
--    1035          475            ?  Components
--      ...                        ?  Advanced Components, Standard Capital Ship Components, Outpost Components, ...
--    1872          475            ?  Research Equipment
--      1873       1872         1872  Decryptors
--      1880       1872         1872  Datacores
--      1807       1872         1872  R.Db
--      1909       1872         1872  Ancient Relics
--
-- То есть используется "семантическое" деление на группы метариалов и
-- компонентов, которые используются в производстве. Например, все варианты
-- патронов будут относиться к патронам, а все Materials будут относиться к
-- Materials, а все варианты подсистем будут относиться к подсистемам.
--------------------------------------------------------------------------------
CREATE TABLE qi.eve_sde_market_groups
(
    sdeg_group_id INTEGER NOT NULL,    -- идентификатор market группы
    sdeg_parent_id INTEGER,            -- идентификатор родительской market группы
    sdeg_semantic_id INTEGER NOT NULL, -- идентификатор родительской "смысловой" market группы
    sdeg_group_name CHARACTER VARYING(100),
    sdeg_icon_id INTEGER,
    CONSTRAINT pk_sdeg PRIMARY KEY (sdeg_group_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.eve_sde_market_groups OWNER TO qi_user;

CREATE UNIQUE INDEX idx_sdeg_pk
    ON qi.eve_sde_market_groups USING btree
    (sdeg_group_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_sdeg_group_parent_ids
    ON qi.eve_sde_market_groups USING btree
    (sdeg_group_id ASC NULLS LAST, sdeg_parent_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_sdeg_group_semantic_ids
    ON qi.eve_sde_market_groups USING btree
    (sdeg_group_id ASC NULLS LAST, sdeg_semantic_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.