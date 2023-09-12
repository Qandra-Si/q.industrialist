-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы для учёта торговых сделок в расплодившихся маркетах

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;


---
DROP INDEX IF EXISTS qi.idx_mr_dst_hub;
DROP INDEX IF EXISTS qi.idx_mr_src_hub;
DROP INDEX IF EXISTS qi.idx_pk_mr;
DROP TABLE IF EXISTS qi.market_routes;

DROP INDEX IF EXISTS qi.idx_mh_trader_corp;
DROP INDEX IF EXISTS qi.idx_mh_hub_id;
DROP INDEX IF EXISTS qi.idx_mh_pk;
DROP TABLE IF EXISTS qi.market_hubs;

--------------------------------------------------------------------------------
-- список систем/станций в системах, в которых ведётся торговля
--------------------------------------------------------------------------------
CREATE TABLE qi.market_hubs
(
    mh_hub_id BIGINT NOT NULL,
    mh_trader_corp INTEGER NOT NULL,
    mh_trader_id BIGINT,
    mh_brokers_fee FLOAT(25) NOT NULL,
    mh_trade_hub_tax FLOAT(25) NOT NULL,
    mh_default_profit FLOAT(25) NOT NULL DEFAULT 0.010,
    mh_manufacturing_possible BOOL NOT NULL DEFAULT FALSE,
    mh_invent_possible BOOL NOT NULL DEFAULT FALSE,
    mh_archive BOOL NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_mh PRIMARY KEY (mh_hub_id,mh_trader_corp),
    CONSTRAINT fk_mh_trader_corp FOREIGN KEY (mh_trader_corp)
        REFERENCES qi.esi_corporations(eco_corporation_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.market_hubs OWNER TO qi_user;

CREATE UNIQUE INDEX idx_mh_pk
    ON qi.market_hubs USING btree
    (mh_hub_id ASC NULLS LAST, mh_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_mh_hub_id
    ON qi.market_hubs USING btree
    (mh_hub_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_mh_trader_corp
    ON qi.market_hubs USING btree
    (mh_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;

--------------------------------------------------------------------------------
-- список торговых маршрутов между маркетами
--------------------------------------------------------------------------------
CREATE TABLE qi.market_routes
(
    mr_src_hub BIGINT NOT NULL,
    mr_dst_hub BIGINT NOT NULL,
    mr_lightyears_src_dst FLOAT(25) NOT NULL,
    mr_lightyears_dst_src FLOAT(25),
    mr_isotopes_src_dst INTEGER NOT NULL,
    mr_isotopes_dst_src INTEGER,
    mr_route_src_dst TEXT NOT NULL,
    mr_route_dst_src TEXT,
    CONSTRAINT pk_mr PRIMARY KEY (mr_src_hub,mr_dst_hub)
)
TABLESPACE pg_default;

ALTER TABLE qi.market_routes OWNER TO qi_user;

CREATE UNIQUE INDEX idx_pk_mr
    ON qi.market_routes USING btree
    (mr_src_hub ASC NULLS LAST, mr_dst_hub ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_mr_src_hub
    ON qi.market_routes USING btree
    (mr_src_hub ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_mr_dst_hub
    ON qi.market_routes USING btree
    (mr_dst_hub ASC NULLS LAST)
TABLESPACE pg_default;

--------------------------------------------------------------------------------
-- заполнение таблиц с торговыми хабами и маршрутами
-- R Initiative 4: 98615601, R Strike: 98553333, R Industry: 98677876
--------------------------------------------------------------------------------
INSERT INTO qi.market_hubs VALUES(60003760,      98553333, 1156031323, 0.02,   0.036, 0.00, TRUE,  FALSE, FALSE); -- Jita (R Strike, olegez)
--INSERT INTO qi.market_hubs VALUES(1036603570630, 98677876, 2116129465, 0.01,   0.036, 0.05, TRUE,  TRUE,  FALSE); -- B2J-5N (R Industry, Qandra Si)
--INSERT INTO qi.market_hubs VALUES(1038457641673, 98677876, 697675571,  0.01,   0.036, 0.15, FALSE, FALSE, FALSE); -- MJ-5F9 (R Industry, Samurai Fruitblow)
--INSERT INTO qi.market_hubs VALUES(1022822609240, 98677876, 93798438,   0.025,  0.036, 0.15, FALSE, FALSE, FALSE); -- NSI-MW (R Industry, Zaratustra Meranus)
--INSERT INTO qi.market_hubs VALUES(1024506767695, 98677876, 2121584976, 0.01,   0.036, 0.15, FALSE, FALSE, FALSE); -- P3X-TN (R Industry, Old Berg)
--INSERT INTO qi.market_hubs VALUES(1032853274346, 98677876, 2112444815, 0.01,   0.036, 0.15, FALSE, FALSE, FALSE); -- W5-205 (R Industry, Uncle Fermer)
--- forbidden market hubs
--INSERT INTO qi.market_hubs VALUES(1035466617946, 98615601, 2112444815, 0.025,  0.036, 0.15, FALSE, FALSE, TRUE); -- 4-HWWF (R Initiative 4, Uncle Fermer)
--INSERT INTO qi.market_hubs VALUES(1036732971380, 98677876, 1156031323, 0.0495, 0.02,  0.15, FALSE, FALSE, TRUE); -- F9-FUV (R Industry, olegez)
--INSERT INTO qi.market_hubs VALUES(1036176306541, 98615601, NULL,       0.01,   0.036, 0.10, FALSE, FALSE, TRUE); -- FH-TTC (R Initiative 4, ?)
--INSERT INTO qi.market_hubs VALUES(60015073,      98553333, 874053567,  0.0048, 0.036, 0.10, FALSE, FALSE, TRUE); -- Nisuwa (R Strike, DarkFman)
--INSERT INTO qi.market_hubs VALUES(1036927076065, 98615601, 2116129465, 0.02,   0.036, 0.05, FALSE, FALSE, TRUE); -- 3-FKCZ (R Initiative 4, Qandra Si)
--INSERT INTO qi.market_hubs VALUES(1034323745897, 98615601, 2116129465, 0.02,   0.036, 0.05, FALSE, FALSE, TRUE); -- P-ZMZV (R Initiative 4, Qandra Si)

--- поиск трейдеров:
--select j.ecwj_second_party_id, c.ech_name, count(1)
--from esi_corporation_wallet_transactions t, esi_corporation_wallet_journals j, esi_characters c
--where
-- t.ecwt_location_id=1034323745897 and
-- t.ecwt_journal_ref_id=j.ecwj_reference_id and
-- j.ecwj_ref_type='market_transaction' and
-- not t.ecwt_is_buy and
-- j.ecwj_second_party_id=c.ech_character_id
--group by j.ecwj_second_party_id, c.ech_name
--order by 3 desc;

insert into qi.market_routes values(1036603570630, 60003760,
  27.884, 35.6, 69708, 88998,
  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:O-LJOO:HKYW-T:Oijanen',
  'https://evemaps.dotlan.net/jump/Rhea,555/Jita:Oijanen:HKYW-T:O-LJOO:B2J-5N');
--insert into qi.market_routes values(1036603570630, 1038457641673,
--  4.863, 4.863, 12157, 12157,
--  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:MJ-5F9',
--  'https://evemaps.dotlan.net/jump/Rhea,555/MJ-5F9:B2J-5N');
--insert into qi.market_routes values(1036603570630, 1022822609240,
--  4.416, 4.416, 11040, 11040,
--  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:NSI-MW9',
--  'https://evemaps.dotlan.net/jump/Rhea,555/NSI-MW:B2J-5N');
--insert into qi.market_routes values(1036603570630, 1024506767695,
--  5.280, 5.280, 13199, 13199,
--  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:P3X-TN',
--  'https://evemaps.dotlan.net/jump/Rhea,555/P3X-TN:B2J-5N');
--insert into qi.market_routes values(1036603570630, 1032853274346,
--  4.072, 4.072, 10179, 10179,
--  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:W5-205',
--  'https://evemaps.dotlan.net/jump/Rhea,555/W5-205:B2J-5N');

--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.
