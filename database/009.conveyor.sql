-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы для настройки работы конвейера

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;


---
DROP INDEX IF EXISTS qi.idx_cl_trade_hub;
DROP INDEX IF EXISTS qi.idx_cl_trader_corp;
DROP INDEX IF EXISTS qi.idx_cl_pk;
DROP TABLE IF EXISTS qi.conveyor_limits;


--------------------------------------------------------------------------------
-- настройка кол-ва товаров для порога "перепроизводства"
--------------------------------------------------------------------------------
CREATE TABLE qi.conveyor_limits
(
    cl_type_id INTEGER NOT NULL,
    cl_trade_hub BIGINT NOT NULL,
    cl_trader_corp INTEGER NOT NULL,
    cl_approximate INTEGER NOT NULL,
    CONSTRAINT pk_cl PRIMARY KEY (cl_type_id,cl_trade_hub),
    CONSTRAINT fk_cl_type_id FOREIGN KEY (cl_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cl_trader_corp FOREIGN KEY (cl_trader_corp)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cl_trade_hub_corp FOREIGN KEY (cl_trade_hub,cl_trader_corp)
        REFERENCES qi.market_hubs(mh_hub_id,mh_trader_corp) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.conveyor_limits OWNER TO qi_user;

CREATE UNIQUE INDEX idx_cl_pk
    ON qi.conveyor_limits USING btree
    (cl_type_id ASC NULLS LAST, cl_trade_hub ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cl_trader_corp
    ON qi.conveyor_limits USING btree
    (cl_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cl_trade_hub_corp
    ON qi.conveyor_limits USING btree
    (cl_trade_hub ASC NULLS LAST, cl_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;

--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.
