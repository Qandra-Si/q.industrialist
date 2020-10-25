-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы, секвенторы, индексы

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;

DROP INDEX IF EXISTS qi.idx_sden_pk;
DROP TABLE IF EXISTS qi.eve_sde_names;


--------------------------------------------------------------------------------
-- EVE Static Data Interface
-- Categories:
--  0 = fsd/metaGroups.yaml
--  1 = fsd/typeIDs.yaml
--  2 = fsd/marketGroups.yaml
--  3 = bsd/invNames.yaml
-- список произвольных key:value пар, являющимися наименованиями
--------------------------------------------------------------------------------
CREATE TABLE qi.eve_sde_names
(
    sden_id BIGINT NOT NULL,
    sden_category INTEGER NOT NULL,
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

-- получаем справку в конце выполнения всех запросов
\d+ qi.