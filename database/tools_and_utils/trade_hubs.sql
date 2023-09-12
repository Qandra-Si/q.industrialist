select m.type_id, m.loc, min(m.lvl) as lvl
from (
 -- список того, что корпорация продавала или продаёт
 select ecor_type_id as type_id, ecor_location_id as loc, 1 as lvl
 from esi_corporation_orders
 where not ecor_is_buy_order and
       ((ecor_corporation_id=98553333 and
         ecor_location_id=60003760) or
        (ecor_corporation_id=98677876 and -- R Initiative 4: 98615601, R Strike: 98553333, R Industry: 98677876
         ecor_location_id in (1038457641673,1024506767695,1022822609240)) -- станка рынка
       )
 union
 -- список того, что выставлено в маркете (не нами)
 select ethp_type_id, ethp_location_id, 2
 from qi.esi_trade_hub_prices
 where 0=0 and ethp_location_id in (1038457641673,1024506767695,1022822609240,60003760) -- станка рынка
) m
group by 1,2;


select
 hubs.src_loc,
 --hubs.dst_loc,
 --hubs.lightyears,
 --hubs.isotopes,
 hubs.src_trader,
 --hubs.dst_trader,
 --hubs.industry,
 sell_orders.type_id,
 sell_orders.volume_remain,
 sell_orders.price_total,
 sell_orders.price_min,
 sell_orders.price_max,
 sell_orders.orders_total
from
 ( select
    ecor_corporation_id as corp_id,
    ecor_location_id as hub_id,
    ecor_type_id as type_id,
    sum(ecor_volume_remain) as volume_remain,
    avg(ecor_price*ecor_volume_remain) as price_total,
    min(ecor_price) as price_min,
    max(ecor_price) as price_max,
    count(1) as orders_total
   from esi_corporation_orders
   where not ecor_is_buy_order and not ecor_history and ecor_corporation_id in (98677876,98553333)
   group by 1,2,3
 ) sell_orders,
 ( -- R Initiative 4: 98615601, R Strike: 98553333, R Industry: 98677876
   -- https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:O-LJOO:HKYW-T:Oijanen
   select
    0 as num,
    1036603570630 as src_loc,
    60003760 as dst_loc,
    27.884 as lightyears,
    69708 as isotopes,
    98677876 as src_trader,
    98553333 as dst_trader,
    true as industry
   -- https://evemaps.dotlan.net/jump/Rhea,555/Jita:Oijanen + HKYW-T:O-LJOO:B2J-5N
   union select 1, 60003760, 1036603570630, 35.6, 88998, 98553333, 98677876, false
   -- https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:MJ-5F9
   union select 2, 1036603570630, 1038457641673, 4.863, 12157, 98677876, 98677876, true
   union select 3, 1038457641673, 1036603570630, 4.863, 12157, 98677876, 98677876, false
   -- https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:NSI-MW
   union select 4, 1036603570630, 1022822609240, 4.416, 11040, 98677876, 98677876, true
   union select 5, 1022822609240, 1036603570630, 4.416, 11040, 98677876, 98677876, false
   -- https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:P3X-TN
   union select 6, 1036603570630, 1022822609240, 5.280, 13199, 98677876, 98677876, true
   union select 7, 1022822609240, 1036603570630, 5.280, 13199, 98677876, 98677876, false
   -- B2J-5N
   union select 8, 1036603570630, 1036603570630, 0, 0, 98677876, 98677876, true
  ) hubs
where sell_orders.corp_id=hubs.dst_trader and sell_orders.hub_id=hubs.dst_loc
order by num desc;



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
INSERT INTO qi.market_hubs VALUES(1036603570630, 98677876, 2116129465, 0.01,   0.036, 0.05, TRUE,  TRUE,  FALSE); -- B2J-5N (R Industry, Qandra Si)
INSERT INTO qi.market_hubs VALUES(1038457641673, 98677876, 697675571,  0.01,   0.036, 0.15, FALSE, FALSE, FALSE); -- MJ-5F9 (R Industry, Samurai Fruitblow)
INSERT INTO qi.market_hubs VALUES(1022822609240, 98677876, 93798438,   0.025,  0.036, 0.15, FALSE, FALSE, FALSE); -- NSI-MW (R Industry, Zaratustra Meranus)
INSERT INTO qi.market_hubs VALUES(1024506767695, 98677876, 2121584976, 0.01,   0.036, 0.15, FALSE, FALSE, FALSE); -- P3X-TN (R Industry, Old Berg)
INSERT INTO qi.market_hubs VALUES(1032853274346, 98677876, 2112444815, 0.01,   0.036, 0.15, FALSE, FALSE, FALSE); -- W5-205 (R Industry, Uncle Fermer)
--- forbidden market hubs
INSERT INTO qi.market_hubs VALUES(1035466617946, 98615601, 2112444815, 0.025,  0.036, 0.15, FALSE, FALSE, TRUE); -- 4-HWWF (R Initiative 4, Uncle Fermer)
INSERT INTO qi.market_hubs VALUES(1036732971380, 98677876, 1156031323, 0.0495, 0.02,  0.15, FALSE, FALSE, TRUE); -- F9-FUV (R Industry, olegez)
INSERT INTO qi.market_hubs VALUES(1036176306541, 98615601, NULL,       0.01,   0.036, 0.10, FALSE, FALSE, TRUE); -- FH-TTC (R Initiative 4)
INSERT INTO qi.market_hubs VALUES(60015073,      98553333, 874053567,  0.0048, 0.036, 0.10, FALSE, FALSE, TRUE); -- Nisuwa (R Strike, DarkFman)
INSERT INTO qi.market_hubs VALUES(1036927076065, 98615601, 2116129465, 0.02,   0.036, 0.05, FALSE, FALSE, TRUE); -- 3-FKCZ (R Initiative 4, Qandra Si)
INSERT INTO qi.market_hubs VALUES(1034323745897, 98615601, 2116129465, 0.02,   0.036, 0.05, FALSE, FALSE, TRUE); -- P-ZMZV (R Initiative 4, Qandra Si)
--- поиск трейдеров:
select j.ecwj_second_party_id, c.ech_name, count(1)
from esi_corporation_wallet_transactions t, esi_corporation_wallet_journals j, esi_characters c
where
 t.ecwt_location_id=1034323745897 and
 t.ecwt_journal_ref_id=j.ecwj_reference_id and
 j.ecwj_ref_type='market_transaction' and
 not t.ecwt_is_buy and
 j.ecwj_second_party_id=c.ech_character_id
group by j.ecwj_second_party_id, c.ech_name
order by 3 desc;

insert into qi.market_routes values(1036603570630, 60003760,
  27.884, 35.6, 69708, 88998,
  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:O-LJOO:HKYW-T:Oijanen',
  'https://evemaps.dotlan.net/jump/Rhea,555/Jita:Oijanen:HKYW-T:O-LJOO:B2J-5N');
insert into qi.market_routes values(1036603570630, 1038457641673,
  4.863, 4.863, 12157, 12157,
  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:MJ-5F9',
  'https://evemaps.dotlan.net/jump/Rhea,555/MJ-5F9:B2J-5N');
insert into qi.market_routes values(1036603570630, 1022822609240,
  4.416, 4.416, 11040, 11040,
  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:NSI-MW9',
  'https://evemaps.dotlan.net/jump/Rhea,555/NSI-MW:B2J-5N');
insert into qi.market_routes values(1036603570630, 1024506767695,
  5.280, 5.280, 13199, 13199,
  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:P3X-TN',
  'https://evemaps.dotlan.net/jump/Rhea,555/P3X-TN:B2J-5N');
insert into qi.market_routes values(1036603570630, 1032853274346,
  4.072, 4.072, 10179, 10179,
  'https://evemaps.dotlan.net/jump/Rhea,555/B2J-5N:W5-205',
  'https://evemaps.dotlan.net/jump/Rhea,555/W5-205:B2J-5N');

 --------------------------------------------------------------
select  co.ecor_type_id

 
 select
 mh.mh_hub_id,
 mh.mh_trader_corpб
 co.ecor_type_id
from
 qi.market_hubs mh
  left outer join qi.esi_corporation_orders as co on (co.ecor_location_id=mh.mh_hub_id and co.ecor_corporation_id=mh.mh_trader_corp);



SELECT x.* FROM qi.esi_trade_hub_prices x
where ethp_type_id=76073
order by ethp_updated_at desc;

SELECT x.* FROM qi.esi_trade_hub_orders x
where etho_type_id=76073
order by etho_updated_at desc;

select
 ethp_location_id,
 ethp_type_id,
 ethp_sell
FROM qi.esi_trade_hub_prices
where
 ethp_location_id in (select mh_hub_id from market_hubs);


----------------------------------------------------------------------------------
select
 --sell_orders.corp_id,
 sell_orders.hub_id,
 sell_orders.type_id,
 sell_orders.volume_remain as our_volume,
 round(sell_orders.price_total::numeric, 2) as price_total,
 sell_orders.price_min as our_price,
 sell_orders.price_max,
 sell_orders.orders_total,
 hub_market.total_volume as their_volume,
 hub_market.min_price as their_price
from
 -- сводная статистика по текущим ордерам в наших маркетах
 (select
  ecor_corporation_id as corp_id,
  ecor_location_id as hub_id,
  ecor_type_id as type_id,
  sum(ecor_volume_remain) as volume_remain,
  avg(ecor_price*ecor_volume_remain) as price_total,
  min(ecor_price) as price_min,
  max(ecor_price) as price_max,
  count(1) as orders_total
 from esi_corporation_orders
 where
  not ecor_is_buy_order and
  not ecor_history and
  ecor_corporation_id in (select mh_trader_corp from market_hubs)
 group by ecor_corporation_id, ecor_location_id, ecor_type_id
 ) sell_orders
  -- локальные цены в этих торговых хабах (исключая наши позиции)
  left outer join (
   select
    etho_location_id as hub_id,
    etho_type_id as type_id,
    min(etho_price) as min_price,
    sum(etho_volume_remain) as total_volume
   from esi_trade_hub_orders -- pk:location_id+oder_id
   where
    not etho_is_buy and
    etho_location_id in (select mh_hub_id from market_hubs) and
    etho_order_id not in (
     select ecor_order_id
     from market_hubs, esi_corporation_orders -- pk:corporation_id+order_id
     where ecor_corporation_id=mh_trader_corp and ecor_location_id=mh_hub_id
    )
   group by etho_location_id, etho_type_id
  ) as hub_market on (sell_orders.hub_id=hub_market.hub_id and sell_orders.type_id=hub_market.type_id)
  left outer join (
    select ethp_type_id, ethp_sell as sell, ethp_buy as buy
    from esi_trade_hub_prices
    where ethp_location_id=60003760
  ) jita_market on (sell_orders.type_id=jita_market.ethp_type_id)
;
----------------------------------------------------------------------------------
-- цены в жите прямо сейчас
select
 tid.sdet_type_id as type_id,
 tid.sdet_type_name as type_name,
 market_group.name as grp_name,
 tid.sdet_packaged_volume as packaged_volume, -- my be null
 jita_market.ethp_sell as sell,
 jita_market.ethp_buy as buy
from
 eve_sde_type_ids as tid,
 eve_sde_market_groups_semantic as market_group,
 esi_trade_hub_prices as jita_market
where
 jita_market.ethp_location_id=60003760 and
 jita_market.ethp_type_id=tid.sdet_type_id and
 market_group.id = tid.sdet_market_group_id and
 (0=0 or market_group.semantic_id not in (
   2, -- Blueprints & Reactions
   19, -- Trade Goods
   150, -- Skills
   499, -- Advanced Moon Materials
   500, -- Processed Moon Materials
   501, -- Raw Moon Materials
   1031, -- Raw Materials
   1035,65,781,1021,1147,1865,1870,1883,1908,2768, -- Components
   1332, -- Planetary Materials
   1857, -- Minerals
   1858, -- Booster Materials
   1860, -- Polymer Materials
   1861, -- Salvage Materials
   1872, -- Research Equipment
   2767 -- Molecular-Forged Materials
  ))
order by market_group.name, tid.sdet_type_name;
----------------------------------------------------------------------------------
   select
    etho_type_id as type_id,
    min(etho_price) as jita_sell_price,
    sum(etho_volume_remain) as jita_total_volume
   from esi_trade_hub_orders -- pk:location_id+oder_id
   where
    not etho_is_buy and
    etho_location_id=60003760 and
    etho_order_id not in (
     select ecor_order_id
     from esi_corporation_orders -- pk:corporation_id+order_id
     where ecor_corporation_id=98553333 and ecor_location_id=60003760 -- R Strike in Jita
    )
   group by etho_type_id;
----------------------------------------------------------------------------------
-- цены в жите прямо сейчас (v2.0)
select
 tid.sdet_type_id as type_id,
 tid.sdet_type_name as type_name,
 tid.sdet_market_group_id as market_group_id,
 tid.sdet_packaged_volume as packaged_volume, -- my be null
 jita_market.jita_sell_price as sell
from
 eve_sde_type_ids as tid,
 (select
   etho_type_id as type_id,
   min(etho_price) as jita_sell_price,
   sum(etho_volume_remain) as jita_total_volume
  from esi_trade_hub_orders -- pk:location_id+oder_id
  where
   not etho_is_buy and
   etho_location_id=60003760 and
   etho_order_id not in (
    select ecor_order_id
    from esi_corporation_orders -- pk:corporation_id+order_id
    where ecor_corporation_id=98553333 and ecor_location_id=60003760 -- R Strike in Jita
   )
  group by etho_type_id) as jita_market
where
 jita_market.type_id=tid.sdet_type_id
order by tid.sdet_type_name;
----------------------------------------------------------------------------------
select distinct semantic_id as id, name as grp
from eve_sde_market_groups_semantic as market_group
where
 (0=0 or market_group.semantic_id not in (
   2, -- Blueprints & Reactions
   19, -- Trade Goods
   150, -- Skills
   499, -- Advanced Moon Materials
   500, -- Processed Moon Materials
   501, -- Raw Moon Materials
   1031, -- Raw Materials
   1035,65,781,1021,1147,1865,1870,1883,1908,2768, -- Components
   1332, -- Planetary Materials
   1857, -- Minerals
   1858, -- Booster Materials
   1860, -- Polymer Materials
   1861, -- Salvage Materials
   1872, -- Research Equipment
   2767 -- Molecular-Forged Materials
  ))
order by name;
----------------------------------------------------------------------------------
-- цены в жите прямо сейчас (v2.0)
select
 tid.sdet_type_id as type_id,
 tid.sdet_type_name as type_name,
 tid.sdet_packaged_volume as packaged_volume, -- my be null
 market_group.semantic_id as market_group_id,
 --tid.sdet_market_group_id as market_group_id,
 --market_group.name,
 jita_market.jita_sell_price as sell
from
 eve_sde_type_ids as tid,
 eve_sde_market_groups_semantic as market_group,
 (select
   etho_type_id as type_id,
   min(etho_price) as jita_sell_price,
   sum(etho_volume_remain) as jita_total_volume
  from esi_trade_hub_orders -- pk:location_id+oder_id
  where
   not etho_is_buy and
   etho_location_id=60003760 and
   etho_order_id not in (
    select ecor_order_id
    from esi_corporation_orders -- pk:corporation_id+order_id
    where ecor_corporation_id=98553333 and ecor_location_id=60003760 -- R Strike in Jita
   )
  group by etho_type_id) as jita_market
where
 jita_market.type_id=tid.sdet_type_id and
 market_group.id=tid.sdet_market_group_id and
 market_group.semantic_id in (4)
order by market_group.name,tid.sdet_type_name;
----------------------------------------------------------------------------------
-- цены в жите прямо сейчас (v3.0)
select
 tid.sdet_type_id as type_id,
 tid.sdet_type_name as type_name,
 tid.sdet_packaged_volume as packaged_volume, -- my be null
 market_group.semantic_id as market_group_id,
 --tid.sdet_market_group_id as market_group_id,
 --market_group.name,
 jita_market.ethp_sell as sell,
 jita_market.ethp_buy as buy
from
 eve_sde_type_ids as tid,
 eve_sde_market_groups_semantic as market_group,
 esi_trade_hub_prices as jita_market
where
 jita_market.ethp_location_id=60003760 and -- Jita
 jita_market.ethp_type_id=tid.sdet_type_id and
 market_group.id=tid.sdet_market_group_id and
 market_group.semantic_id in (4)
order by market_group.name,tid.sdet_type_name;
----------------------------------------------------------------------------------

select ecor_order_id
from market_hubs, esi_corporation_orders -- pk:corporation_id+order_id
where ecor_corporation_id=mh_trader_corp and ecor_location_id=mh_hub_id;

select
 etho_location_id as hub_id,
 etho_type_id as type_id,
 min(etho_price) as min_price,
 sum(etho_volume_remain) as total_volume
from esi_trade_hub_orders -- pk:location_id+oder_id
where
 not etho_is_buy and
 etho_location_id in (select mh_hub_id from market_hubs) and
 etho_order_id not in (
  select ecor_order_id
  from market_hubs, esi_corporation_orders -- pk:corporation_id+order_id
  where ecor_corporation_id=mh_trader_corp and ecor_location_id=mh_hub_id
 )
group by etho_location_id, etho_type_id;

DROP INDEX idx_ecor_corporation_location_id;

CREATE INDEX idx_ecor_corporation_location_id
    ON qi.esi_corporation_orders USING btree
    (ecor_corporation_id ASC NULLS LAST, ecor_location_id ASC NULLS LAST)
TABLESPACE pg_default;


-----------
select
 h.mh_hub_id as hub,
 h.mh_trader_corp as co,
 h.mh_brokers_fee as fee,
 h.mh_trade_hub_tax as tax,
 h.mh_default_profit as pr,
 h.mh_manufacturing_possible as m,
 h.mh_invent_possible as i,
 h.mh_archive as a,
 --c.ech_name as tr,
 s.forbidden as f,
 s.solar_system_name as ss,
 s.station_type_name as snm,
 s.name as nm,
 r.mr_lightyears_src_dst+r.mr_lightyears_dst_src as ly,
 r.mr_isotopes_src_dst+r.mr_isotopes_dst_src as it,
 r.mr_route_src_dst as rs,
 r.mr_route_dst_src as rd
from
 market_hubs h
  --left outer join esi_characters as c on (h.mh_trader_id=c.ech_character_id)
  left outer join market_routes as r on (h.mh_hub_id=r.mr_dst_hub),
 esi_known_stations s
where h.mh_hub_id=s.location_id
order by h.mh_archive, s.forbidden;


select
 ethp_sell as js, -- jita sell
 ethp_buy as jb, -- jita buy
 round(ri_isotopes.price::numeric,2) as rib -- r initiative buy price
from
 esi_trade_hub_prices
  left outer join (
   select ri_isotopes.type_id, sum(total_price)/sum(total_volume) as price
   from
    (select
     ecor_type_id as type_id,
     ecor_volume_total-ecor_volume_remain as total_volume,
     ecor_price*(ecor_volume_total-ecor_volume_remain) * case
      when o.ecor_duration=0 then 1
      else 1+h.mh_brokers_fee
     end as total_price -- на длительных ордерах платим брокерскую комиссию
    from
     esi_corporation_orders o,
     market_hubs h
    where
     o.ecor_corporation_id=mh_trader_corp and
     o.ecor_type_id in (17888,17887,16274,17889) and
     o.ecor_is_buy_order and
     ecor_volume_total<>ecor_volume_remain
    order by ecor_issued desc
    limit 20) ri_isotopes
   group by type_id
  ) as ri_isotopes on (ri_isotopes.type_id=ethp_type_id)
where
 ethp_location_id=60003760 and -- Jita
 -- Rhea:Nitrogen Isotopes, Anshar:Oxygen Isotopes, Ark:Helium Isotopes, Nomad:Hydrogen Isotopes
 ethp_type_id in (17888,17887,16274,17889);

select ri_isotopes.type_id, sum(total_price)/sum(total_volume) as price
   from
    (select
     ecor_type_id as type_id,
     ecor_volume_total-ecor_volume_remain as total_volume,
     ecor_price*(ecor_volume_total-ecor_volume_remain) * case
      when o.ecor_duration=0 then 1
      else 1+h.mh_brokers_fee
     end as total_price -- на длительных ордерах платим брокерскую комиссию
    from
     esi_corporation_orders o,
     market_hubs h
    where
     o.ecor_corporation_id=mh_trader_corp and
     o.ecor_type_id in (17888,17887,16274,17889) and
     o.ecor_is_buy_order and
     ecor_volume_total<>ecor_volume_remain
    order by ecor_issued desc
    limit 20) ri_isotopes
   group by type_id;





