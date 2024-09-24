--- eve_sde_blueprint_products

ALTER TABLE qi.eve_sde_blueprint_products
  ADD CONSTRAINT pk_sdebp PRIMARY KEY (sdebp_blueprint_type_id,sdebp_activity,sdebp_product_id);

CREATE UNIQUE INDEX idx_sdebp_pk
    ON qi.eve_sde_blueprint_products USING btree
    (sdebp_blueprint_type_id ASC NULLS LAST, sdebp_activity ASC NULLS LAST, sdebp_product_id ASC NULLS LAST)
TABLESPACE pg_default;

--- conveyor_formulas

DROP PROCEDURE IF EXISTS qi.cfc_full_calculus;

DROP VIEW IF EXISTS qi.conveyor_formulas_industry_costs;
DROP VIEW IF EXISTS qi.conveyor_formulas_products_prices;
DROP VIEW IF EXISTS qi.conveyor_formulas_market_routes;
DROP VIEW IF EXISTS qi.conveyor_formulas_jobs_costs;
DROP VIEW IF EXISTS qi.conveyor_formulas_purchase_materials;
DROP VIEW IF EXISTS qi.conveyor_formulas_transfer_cost;

DROP FUNCTION IF EXISTS qi.eve_ceiling(double precision);
DROP FUNCTION IF EXISTS qi.eve_ceiling_change_by_point(double precision, integer);
DROP FUNCTION IF EXISTS qi.nitrogen_isotopes_price();

DROP INDEX IF EXISTS qi.idx_cfc_formula_best_choice;
DROP INDEX IF EXISTS qi.idx_cfc_market_route;
DROP INDEX IF EXISTS qi.idx_cfc_market_hub;
DROP INDEX IF EXISTS qi.idx_cfc_pk;
DROP TABLE IF EXISTS qi.conveyor_formula_calculus;

DROP INDEX IF EXISTS qi.idx_cfj_blueprint_type_id;
DROP INDEX IF EXISTS qi.idx_cfj_formula;
DROP TABLE IF EXISTS qi.conveyor_formula_jobs;

DROP INDEX IF EXISTS qi.idx_cfp_formula_material;
DROP INDEX IF EXISTS qi.idx_cfp_formula;
DROP TABLE IF EXISTS qi.conveyor_formula_purchase;

DROP INDEX IF EXISTS qi.idx_cf_decryptor_type_id;
DROP INDEX IF EXISTS qi.idx_cf_product_type_id;
DROP INDEX IF EXISTS qi.idx_unq_cf4;
DROP INDEX IF EXISTS qi.idx_unq_cf3;
DROP INDEX IF EXISTS qi.idx_unq_cf2;
DROP INDEX IF EXISTS qi.idx_unq_cf1;
DROP INDEX IF EXISTS qi.idx_cf_pk;
DROP TABLE IF EXISTS qi.conveyor_formulas;
DROP SEQUENCE IF EXISTS qi.seq_cf;

DROP TYPE  IF EXISTS qi.esi_formulas_relics;


--------------------------------------------------------------------------------
-- расчёт эффективности производства на основе производственных формул
--------------------------------------------------------------------------------
CREATE TYPE qi.esi_formulas_relics AS ENUM ('intact','malfunctioning','wrecked','unused');

CREATE SEQUENCE qi.seq_cf
    INCREMENT 1
    START 1000
    MINVALUE 1
    MAXVALUE 2147483647
    CACHE 1;

ALTER SEQUENCE qi.seq_cf OWNER TO qi_user;

CREATE TABLE qi.conveyor_formulas
(
    cf_formula INTEGER NOT NULL DEFAULT NEXTVAL('qi.seq_cf'::regclass), -- идентификатор формулы
    cf_blueprint_type_id INTEGER NOT NULL,
    cf_activity INTEGER NOT NULL,
    cf_product_type_id INTEGER NOT NULL,
    cf_customized_runs INTEGER NOT NULL,
    cf_decryptor_type_id INTEGER,
    cf_ancient_relics qi.esi_formulas_relics NOT NULL DEFAULT 'unused',
    cf_prior_blueprint_type_id INTEGER, -- Capital Hull Repairer II делается из разных bpc/bpo
    cf_material_efficiency INTEGER, -- если не указано, то подразумевается значение 0 (нужно для обратного вычисления кода декриптора)
    cf_time_efficiency INTEGER, -- если не указано, то подразумевается значение 0 (нужно для обратного вычисления кода декриптора)
    CONSTRAINT pk_cf PRIMARY KEY (cf_formula),
    CONSTRAINT fk_cf_product_type_id FOREIGN KEY (cf_product_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cf_decryptor_type_id FOREIGN KEY (cf_decryptor_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cf_blueprint_product FOREIGN KEY (cf_blueprint_type_id, cf_activity, cf_product_type_id)
        REFERENCES qi.eve_sde_blueprint_products(sdebp_blueprint_type_id, sdebp_activity, sdebp_product_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.conveyor_formulas OWNER TO qi_user;

CREATE UNIQUE INDEX idx_cf_pk
    ON qi.conveyor_formulas USING btree
    (cf_formula ASC NULLS LAST)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_unq_cf1
    ON qi.conveyor_formulas USING btree
    (cf_blueprint_type_id, cf_activity, cf_product_type_id, cf_customized_runs, cf_ancient_relics, cf_decryptor_type_id, cf_prior_blueprint_type_id)
    WHERE ((cf_decryptor_type_id IS NOT NULL) AND (cf_prior_blueprint_type_id IS NOT NULL));

CREATE UNIQUE INDEX idx_unq_cf2
    ON qi.conveyor_formulas USING btree
    (cf_blueprint_type_id, cf_activity, cf_product_type_id, cf_customized_runs, cf_ancient_relics, cf_prior_blueprint_type_id)
    WHERE ((cf_decryptor_type_id IS NULL) AND (cf_prior_blueprint_type_id IS NOT NULL));

CREATE UNIQUE INDEX idx_unq_cf3
    ON qi.conveyor_formulas USING btree
    (cf_blueprint_type_id, cf_activity, cf_product_type_id, cf_customized_runs, cf_ancient_relics, cf_decryptor_type_id)
    WHERE ((cf_decryptor_type_id IS NOT NULL) AND (cf_prior_blueprint_type_id IS NULL));

CREATE UNIQUE INDEX idx_unq_cf4 -- по сути это вариант для T1 продукции у которой меняется ME без декриптора
    ON qi.conveyor_formulas USING btree
    (cf_blueprint_type_id, cf_activity, cf_product_type_id, cf_customized_runs, cf_material_efficiency) -- cf_ancient_relics
    WHERE ((cf_decryptor_type_id IS NULL) AND (cf_prior_blueprint_type_id IS NULL) AND (cf_material_efficiency IS NOT NULL));

CREATE INDEX idx_cf_product_type_id
    ON qi.conveyor_formulas USING btree
    (cf_product_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cf_decryptor_type_id
    ON qi.conveyor_formulas USING btree
    (cf_decryptor_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cf_blueprint_product
    ON qi.conveyor_formulas USING btree
    (cf_blueprint_type_id ASC NULLS LAST, cf_activity ASC NULLS LAST, cf_product_type_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- материалы, задействованные в производстве по conveyor-формулам
--------------------------------------------------------------------------------
CREATE TABLE qi.conveyor_formula_purchase
(
    cfp_formula INTEGER NOT NULL,
    cfp_material_type_id INTEGER NOT NULL,
    cfp_quantity DOUBLE PRECISION NOT NULL,
    CONSTRAINT fk_cfp_formula FOREIGN KEY (cfp_formula)
        REFERENCES qi.conveyor_formulas(cf_formula) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cfp_material_type_id FOREIGN KEY (cfp_material_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.conveyor_formula_purchase OWNER TO qi_user;

CREATE INDEX idx_cfp_formula
    ON qi.conveyor_formula_purchase USING btree
    (cfp_formula ASC NULLS LAST)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_cfp_formula_material
    ON qi.conveyor_formula_purchase USING btree
    (cfp_formula ASC NULLS LAST, cfp_material_type_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- работы, задействованные в производстве по conveyor-формулам
--------------------------------------------------------------------------------
CREATE TABLE qi.conveyor_formula_jobs
(
    cfj_formula INTEGER NOT NULL,
    cfj_usage_chain DOUBLE PRECISION NOT NULL, -- доля работы относительно предыдущих уровней вложенности
    cfj_solar_system_id INTEGER NOT NULL, -- солнечная система в которой планируется работа
    cfj_blueprint_type_id INTEGER NOT NULL, -- type_id чертежа
    cfj_planned_blueprints INTEGER NOT NULL, -- количество чертежей
    cfj_planned_runs INTEGER NOT NULL, -- количество прогонов
    cfj_activity_code INTEGER NOT NULL, -- activity_code (1, 5, 8, 9)
    cfj_activity_eiv INTEGER NOT NULL, -- [reaction] -> reaction; [manufacturing, copying, invention] -> manufacturing
    cfj_job_cost_base_multiplier DOUBLE PRECISION NOT NULL, -- [manufacturing, reaction] -> 1.0; [copying, invention] -> 0.2
    cfj_role_bonus_job_cost DOUBLE PRECISION NOT NULL, -- ролевой бонус структуры для выбранного activity_code
    cfj_rigs_bonus_job_cost DOUBLE PRECISION NOT NULL, -- бонусы модификаторов для выбранного activity_code
    cfj_scc_surcharge DOUBLE PRECISION NOT NULL, -- дополнительный сбор от CCP, фиксирован 0.04
    cfj_facility_tax DOUBLE PRECISION NOT NULL, -- налог на структуре (фиксированный налог на NPC структурах 0.0025; на структурах игроков устанавливается владельцем)
    CONSTRAINT fk_cfj_formula FOREIGN KEY (cfj_formula)
        REFERENCES qi.conveyor_formulas(cf_formula) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cfj_blueprint_type_id FOREIGN KEY (cfj_blueprint_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.conveyor_formula_jobs OWNER TO qi_user;

CREATE INDEX idx_cfj_formula
    ON qi.conveyor_formula_jobs USING btree
    (cfj_formula ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cfj_blueprint_type_id
    ON qi.conveyor_formula_jobs USING btree
    (cfj_blueprint_type_id ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- предвариетльные расчёты conveyor-формул (расчёты выполняются долго, и потому
-- результаты кешируются до момента следующего обновления зависимостей)
--------------------------------------------------------------------------------
CREATE TABLE qi.conveyor_formula_calculus
(
    cfc_formula INTEGER NOT NULL,
    -- вычисляемые и кешированные данные формулы
    cfc_products_per_single_run INTEGER NOT NULL, -- кешируется: количество продукции, производимой за один прогон (из таблицы eve_sde_blueprint_products)
    cfc_products_num INTEGER NOT NULL, -- вычисляется: количество продукции, производимой формулой (как произведение customized_runs и products_per_single_run)
    cfc_best_choice BOOLEAN NOT NULL DEFAULT FALSE, -- вычисляется: наилучшая формула (наиболее прибыльный вариант) производства выбранного продукта
    -- производстенные и торговые локации
    cfc_industry_hub BIGINT NOT NULL, -- ожидается 1 вариант: фабрика, где расположено основное производство (откуда идёт торговый маршрут и куда привозятся материалы из Jita)
    cfc_trade_hub BIGINT NOT NULL, -- вариантность: торговый хаб, где продаются произведённые продукты
    cfc_trader_corp INTEGER NOT NULL, -- вариантность: корпорация, которая торгует в торговом хабе
    -- налоги и брокерские комиссии
    cfc_buying_brokers_fee FLOAT(25) NOT NULL, -- кешируется: брокерский налог на закупку материалов в Jita (из таблицы market_hubs для Jita)
    cfc_sales_brokers_fee FLOAT(25) NOT NULL, -- кешируется: брокерский налог на продажу продукции в торговом хабе (из таблицы market_hubs для хаба)
    cfc_sales_tax FLOAT(25) NOT NULL, -- кешируется: налог с продаж продукции в торговом хабе (из таблицы market_hubs для хаба)
    -- Rhea с 3x ORE Expanded Cargohold имеет 386'404.0 куб.м
    -- из Jita дистанция 35.6 свет.лет со всеми скилами в 5 понадобится сжечь 88'998 Nitrogen Isotopes (buy 545.40 ISK)
    cfc_fuel_price_isk DOUBLE PRECISION NOT NULL, -- кешируется: стоимость топляка джампака (по баям с налогами, либо усреднённая цена, либо по селам без налогов)
    -- подробности закупки сырых материалов
    cfc_materials_cost DOUBLE PRECISION NOT NULL, -- вычисляется: стоимость закупа в Jita сырых матариалов по формуле
    cfc_materials_cost_with_fee DOUBLE PRECISION NOT NULL, -- кешируется: стоимость закупа в жита с учётом комиссии (произведение buying_brokers_fee и materials_cost)
    cfc_purchase_volume DOUBLE PRECISION NOT NULL, -- вычисляется: объём сырых материалов закупаемых по формуле
    cfc_materials_transfer_cost DOUBLE PRECISION NOT NULL, -- вычисляется: стоимость перевозки сырых материалов из Jita в пересчёте на стоимость топляка
    -- стоимость запуска работ
    cfc_jobs_cost DOUBLE PRECISION NOT NULL, -- вычисляется: стоимость запуска работ по формуле
    -- подробности сбыта готовой продукции
    cfc_ready_volume DOUBLE PRECISION NOT NULL, -- кешируется: объём продукции произведённой по формуле в упакованном виде (из таблицы eve_sde_type_ids)
    cfc_ready_transfer_cost DOUBLE PRECISION NOT NULL, -- вычисляется: стоимость перевозки готовой продукции (общее кол-во, произведённой по формуле) в торговый хаб
    cfc_products_recommended_price DOUBLE PRECISION, -- вычисляется: рекомендованная стоимость (общее кол-во по формуле) готовой продукции индивидуально для торгового хаба (по совокупности известных цен)
    cfc_products_sell_fee_and_tax DOUBLE PRECISION, -- вычисляется: ориентировочные комиссии и налоги относительно рекомендованной стоимости
    cfc_single_product_price_wo_fee_tax DOUBLE PRECISION, -- вычисляется: прибыль от продажи партии продуктов по рекомендованной цене в торговом хабе
    -- сводные данные по производству по формуле
    cfc_total_gross_cost DOUBLE PRECISION NOT NULL, -- вычисляется: итоговая стоимость производственного проекта по формуле с транспортировкой до торгового хаба
    cfc_single_product_cost DOUBLE PRECISION NOT NULL, -- кешируется: стоимость производства одной единицы продукции (частное от total_gross_cost и products_num)
    cfc_product_mininum_price DOUBLE PRECISION NOT NULL, -- кешируется: минимально-рекомендованная цена выставления продукции в торговом хабе (total_gross_cost + products_sell_fee_and_tax) / products_num
    cfc_single_product_profit DOUBLE PRECISION, -- кешируется: профит от производства и продажи одонго экземпляра продукта (cfc_single_product_price_wo_fee_tax-cfc_single_product_cost)
    -- дата/время актуализации сведений о стоимости производства по формуле
    cfc_created_at TIMESTAMP,
    cfc_updated_at TIMESTAMP,
    CONSTRAINT pk_cfc PRIMARY KEY (cfc_formula, cfc_industry_hub, cfc_trade_hub, cfc_trader_corp),
    CONSTRAINT fk_cfc_formula FOREIGN KEY (cfc_formula)
        REFERENCES qi.conveyor_formulas(cf_formula) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cfc_market_route FOREIGN KEY (cfc_industry_hub, cfc_trade_hub)
        REFERENCES qi.market_routes(mr_src_hub, mr_dst_hub) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cfc_market_hub FOREIGN KEY (cfc_trade_hub, cfc_trader_corp)
        REFERENCES qi.market_hubs(mh_hub_id, mh_trader_corp) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.conveyor_formula_calculus OWNER TO qi_user;

CREATE UNIQUE INDEX idx_cfc_pk
    ON qi.conveyor_formula_calculus USING btree
    (cfc_formula ASC NULLS LAST, cfc_industry_hub ASC NULLS LAST, cfc_trade_hub ASC NULLS LAST, cfc_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cfc_formula_best_choice
    ON qi.conveyor_formula_calculus USING btree
    (cfc_formula ASC NULLS LAST, cfc_best_choice ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cfc_market_route
    ON qi.conveyor_formula_calculus USING btree
    (cfc_industry_hub ASC NULLS LAST, cfc_trade_hub ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cfc_market_hub
    ON qi.conveyor_formula_calculus USING btree
    (cfc_trade_hub ASC NULLS LAST, cfc_trader_corp ASC NULLS LAST)
TABLESPACE pg_default;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- утилиты для работы с market-центами
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION qi.eve_ceiling(isk double precision)
 RETURNS double precision
 LANGUAGE plpgsql
 IMMUTABLE STRICT
AS $function$
begin
 if isk is null then return null;
 elsif isk < 100.0 then isk = round(isk::numeric, 2);
 elsif isk < 1000.0 then isk = ceil(isk * 10.0) / 10.0;
 elsif isk < 10000.0 then isk = ceil(isk);
 elsif isk < 100000.0 then isk = round(isk::numeric, -1);
 elsif isk < 1000000.0 then isk = round(isk::numeric, -2);
 elsif isk < 10000000.0 then isk = round(isk::numeric, -3);
 elsif isk < 100000000.0 then isk = round(isk::numeric, -4); -- 25990000.00 -> 25990000.00
 elsif isk < 1000000000.0 then isk = round(isk::numeric, -5);
 elsif isk < 10000000000.0 then isk = round(isk::numeric, -6);
 elsif isk < 100000000000.0 then isk = round(isk::numeric, -7);
 elsif isk < 1000000000000.0 then isk = round(isk::numeric, -8);
 elsif isk < 10000000000000.0 then isk = round(isk::numeric, -9);
 else assert false, 'too much isk at time';
 end if;
 return isk;
end;
$function$
;

CREATE OR REPLACE FUNCTION qi.eve_ceiling_change_by_point(isk double precision, points integer)
 RETURNS double precision
 LANGUAGE plpgsql
 IMMUTABLE STRICT
AS $function$
declare 
 pip double precision;
begin
 assert points = +1 or points = -1, 'incorrect points for eve ceiling change';
 if isk is null then return null;
 elsif isk < 100.0 then pip = 0.01; -- 99.99 -> 0.01
 elsif isk < 1000.0 then pip = 0.1; -- 999.90 -> 0.1
 elsif isk < 10000.0 then pip = 1.0; -- 9999 -> 1
 elsif isk < 100000.0 then pip = 10.0; -- 99990 -> 10
 elsif isk < 1000000.0 then pip = 100.0; -- 999900 -> 100
 elsif isk < 10000000.0 then pip = 1000.0; -- 9999000 -> 1000
 elsif isk < 100000000.0 then pip = 10000.0; -- ...
 elsif isk < 1000000000.0 then pip = 100000.0;
 elsif isk < 10000000000.0 then pip = 1000000.0;
 elsif isk < 100000000000.0 then pip = 10000000.0;
 elsif isk < 1000000000000.0 then pip = 100000000.0;
 elsif isk < 10000000000000.0 then pip = 1000000000.0;
 else assert false, 'too much isk at time';
 end if;
 return qi.eve_ceiling((isk + pip * points)::numeric);
end;
$function$
;

CREATE OR REPLACE FUNCTION qi.nitrogen_isotopes_price()
 RETURNS double precision
 LANGUAGE sql
 STABLE
AS $function$
   select coalesce(
           x.buy,
           (select emp_average_price as average_price from esi_markets_prices universe where emp_type_id = 17888),
           x.sell,
           545.40) -- hardcoded price (august 2024)
   from (
    select
     qi.eve_ceiling_change_by_point(ethp_buy,1) * 1.0132 as buy, -- TODO: Jita 1.32 fee
     ethp_sell as sell
    from esi_trade_hub_prices
    where ethp_location_id = 60003760 and ethp_type_id = 17888 -- Nitrogen Isotopes
   ) x
  $function$
;

--------------------------------------------------------------------------------
-- представления для расчёта стоимости проектов по conveyor-формулам
--------------------------------------------------------------------------------
create or replace view qi.conveyor_formulas_transfer_cost as
  select
   -- formula
   raw_materials.formula,
   ready_products.products_per_single_run,
   ready_products.customized_runs,
   -- raw_materials
   raw_materials.purchase_volume,
   -- ready_products
   ready_products.product_packed,
   ready_products.product_packed * ready_products.products_per_single_run * ready_products.customized_runs as ready_volume
  from
   (select
     x.formula,
     sum(x.quantity * x.material_packed) as purchase_volume
    from (
     select
      f.cf_formula as formula,
      --p.cfp_material_type_id as material_type_id,
      p.cfp_quantity as quantity,
      tp.sdet_packaged_volume as material_packed
     from
      qi.conveyor_formulas f,
      qi.conveyor_formula_purchase p
       left outer join qi.eve_sde_type_ids tp on (tp.sdet_type_id=p.cfp_material_type_id)
     where f.cf_formula=p.cfp_formula
    ) x
    group by x.formula
   ) raw_materials,
   (select
    f.cf_formula as formula,
    f.cf_customized_runs as customized_runs,
    --f.cf_blueprint_type_id,
    --f.cf_product_type_id,
    tf.sdet_packaged_volume as product_packed,
    p.sdebp_activity as activity,
    p.sdebp_quantity as products_per_single_run
   from
    qi.conveyor_formulas f,
    qi.eve_sde_type_ids tf,
    qi.eve_sde_blueprint_products p
   where
    f.cf_product_type_id=tf.sdet_type_id and
    f.cf_product_type_id=p.sdebp_product_id and
    f.cf_blueprint_type_id=p.sdebp_blueprint_type_id and
    f.cf_activity=p.sdebp_activity --and f.cf_formula=9028
   ) ready_products
  where raw_materials.formula=ready_products.formula;

create or replace view qi.conveyor_formulas_purchase_materials as
  select 
   x.formula,
   sum(x.quantity * coalesce(x.jita_buy, x.average_price, x.jita_sell)) as materials_cost
  from (
   select
    f.cf_formula as formula,
    -- cfp_material_type_id as material_type_id,
    cfp_quantity as quantity,
    jita.sell as jita_sell,
    --jita.buy as jita_buy,
    qi.eve_ceiling_change_by_point(jita.buy,1) as jita_buy,
    universe.emp_average_price as average_price
   from
    conveyor_formulas f,
    conveyor_formula_purchase p
     left outer join (
      select ethp_type_id, ethp_sell as sell, ethp_buy as buy
      from esi_trade_hub_prices
      where ethp_location_id = 60003760
     ) jita on (p.cfp_material_type_id = jita.ethp_type_id)
     left outer join esi_markets_prices universe on (p.cfp_material_type_id = universe.emp_type_id)
   where f.cf_formula=p.cfp_formula
  ) x
  group by x.formula;

create or replace view qi.conveyor_formulas_jobs_costs as
  select
   z.formula,
   sum(z.job_cost) as job_cost
  from (
   select
    w.cfj_formula as formula,
    (w.cfj_usage_chain * w.cfj_planned_blueprints * w.cfj_planned_runs) * (w.system_cost + w.structure_role_bonus + w.structure_rigs_bonus + w.tax_scc_surcharge + w.tax_facility) as job_cost,
    w.cfj_blueprint_type_id as blueprint_type_id,
    -- (select sdet_type_name from eve_sde_type_ids t where t.sdet_type_id=w.cfj_blueprint_type_id) as blueprint_name,
    w.cfj_activity_code,
    -- case cfj_activity_code
    --  when 1 then 'manufacturing'
    --  when 5 then 'copying'
    --  when 8 then 'invention'
    --  when 9 then 'reaction'
    -- end activity,
    w.cfj_planned_blueprints as planned_blueprints,
    w.cfj_planned_runs as planned_runs,
    w.estimated_items_value,
    w.system_cost + w.structure_role_bonus + w.structure_rigs_bonus as total_job_gross_cost,
    w.tax_scc_surcharge + w.tax_facility as total_taxes
   from (
    select
     x.cfj_formula,
     x.cfj_blueprint_type_id,
     x.cfj_activity_code,
     x.cfj_usage_chain,
     x.cfj_planned_blueprints,
     x.cfj_planned_runs,
     x.estimated_items_value,
     x.system_cost,
     ceil(x.system_cost * x.cfj_role_bonus_job_cost) as structure_role_bonus, -- system_cost, role_bonus_job_cost
     ceil(x.system_cost * x.cfj_rigs_bonus_job_cost) as structure_rigs_bonus, -- system_cost, rigs_bonus_job_cost
     ceil(x.job_cost_base * x.cfj_scc_surcharge) as tax_scc_surcharge,  -- job_cost_base, scc_surcharge
     ceil(x.job_cost_base * x.cfj_facility_tax) as tax_facility -- job_cost_base, facility_tax
    from (
     select
      cfj_formula,
      cfj_blueprint_type_id,
      cfj_activity_code,
      cfj_usage_chain,
      cfj_planned_blueprints,
      cfj_planned_runs,
      m.eiv as estimated_items_value, -- sum(material.quantity * material.adjusted_price)
      m.eiv * cfj_job_cost_base_multiplier as job_cost_base, -- estimated_items_value, job_cost_base_multiplier
      ci.cost_index as cost_index, -- industry_cost_index
      ceil(m.eiv * cfj_job_cost_base_multiplier * ci.cost_index) as system_cost, -- job_cost_base, cost_index
      cfj_role_bonus_job_cost,
      cfj_rigs_bonus_job_cost,
      cfj_scc_surcharge,
      cfj_facility_tax
     from
      conveyor_formula_jobs j
       left outer join (
        select sdebm_blueprint_type_id, sdebm_activity, sum(sdebm_quantity * emp_adjusted_price) as eiv
        from eve_sde_blueprint_materials, esi_markets_prices
        where sdebm_material_id=emp_type_id
        group by 1, 2
       ) as m on (m.sdebm_blueprint_type_id=j.cfj_blueprint_type_id and m.sdebm_activity=j.cfj_activity_eiv),
      esi_industry_cost_indices ci
     where ci.system_id=j.cfj_solar_system_id and ci.activity=j.cfj_activity_code
    ) x
   ) w
   --where w.cfj_formula=1029
   --order by 5, w.cfj_usage_chain desc
  ) z
  group by z.formula
  ;

create or replace view qi.conveyor_formulas_market_routes as
  select
   -- input and output locations
   trnsfr_from_jita.industry_hub,
   trnsfr_to_market.trade_hub,
   trnsfr_to_market.trader_corp,
   -- sales and buying fee and taxes
   trnsfr_from_jita.buying_brokers_fee,
   trnsfr_to_market.sales_brokers_fee,
   trnsfr_to_market.sales_tax,
   -- Rhea с 3x ORE Expanded Cargohold имеет 386'404.0 куб.м
   -- из Jita дистанция 35.6 свет.лет со всеми скилами в 5 понадобится сжечь 88'998 Nitrogen Isotopes (buy 545.40 ISK)
   fuel_price.isk as fuel_price_isk,
   -- raw material buying details
   trnsfr_from_jita.input_fuel_quantity,
   (trnsfr_from_jita.input_fuel_quantity * fuel_price.isk) / 386404 as input_m3_cost,
   -- ready product selling details
   trnsfr_to_market.output_fuel_quantity,
   (trnsfr_to_market.output_fuel_quantity * fuel_price.isk) / 386404 as output_m3_cost
  from
   (select qi.nitrogen_isotopes_price() as isk) as fuel_price, -- ожидается одна строка, вызов будет однократный
   (select
     r.mr_src_hub as industry_hub,
     r.mr_isotopes_dst_src as input_fuel_quantity,
     h.mh_brokers_fee as buying_brokers_fee
    from
     qi.market_routes r, qi.market_hubs h
    where
     r.mr_dst_hub=60003760 and
     h.mh_hub_id=60003760 and 
     not h.mh_archive
   ) trnsfr_from_jita,
   (select
     r.mr_src_hub as industry_hub,
     r.mr_dst_hub as trade_hub,
     h.mh_trader_corp as trader_corp,
     r.mr_isotopes_src_dst as output_fuel_quantity,
     h.mh_brokers_fee as sales_brokers_fee,
     h.mh_trade_hub_tax as sales_tax
    from qi.market_routes r, qi.market_hubs h
    where
     r.mr_dst_hub=h.mh_hub_id and
     --r.mr_dst_hub<>60003760 and
     not h.mh_archive
   ) trnsfr_to_market
  where
   trnsfr_from_jita.industry_hub=trnsfr_to_market.industry_hub
;

create or replace view qi.conveyor_formulas_products_prices as
  select
   type_id,
   trade_hub,
   case when hub_sell is not null then qi.eve_ceiling_change_by_point(hub_sell, -1)
        when jita_sell is not null then jita_sell
        when average_price is not null then qi.eve_ceiling(average_price)
        when jita_buy is not null then qi.eve_ceiling_change_by_point(jita_buy * (1.0+0.02+0.025+0.036), 1)
        when hub_buy is not null then qi.eve_ceiling_change_by_point(hub_buy * (1.0+0.02+0.025+0.036), 1)
        else null
   end hub_recommended_price,
   case when hub_sell is not null then hub_sell_volume else 0 end hub_sell_volume
   ,jita_sell
   ,jita_sell_volume
   ,jita_buy
   ,jita_buy_volume
   ,hub_sell
   ,hub_buy
   --,hub_sell_volume
   ,hub_buy_volume
   ,average_price
  from (
   select
    x.type_id,
    x.trade_hub,
    hub.sell hub_sell,
    hub.buy hub_buy,
    hub.sell_volume hub_sell_volume,
    hub.buy_volume hub_buy_volume,
    jita.sell jita_sell,
    jita.buy jita_buy,
    jita.sell_volume jita_sell_volume,
    jita.buy_volume jita_buy_volume,
    universe.emp_average_price average_price
   from
    (select distinct f.cf_product_type_id as type_id, r.trade_hub
     from conveyor_formulas f, qi.conveyor_formulas_market_routes r
     --where f.cf_product_type_id=40560
    ) x
     -- цены на продукт производства в торговом хабе прямо сейчас
     left outer join (
       select ethp_type_id as type_id, ethp_location_id as trade_hub, ethp_sell as sell, ethp_buy as buy, ethp_sell_volume as sell_volume, ethp_buy_volume as buy_volume
       from qi.esi_trade_hub_prices
     ) hub on (hub.type_id=x.type_id and hub.trade_hub=x.trade_hub)
     -- цены на продукт производства в jita прямо сейчас
     left outer join (
       select ethp_type_id as type_id, ethp_sell as sell, ethp_buy as buy, ethp_sell_volume as sell_volume, ethp_buy_volume as buy_volume
       from qi.esi_trade_hub_prices
       where ethp_location_id=60003760
     ) jita on (jita.type_id=x.type_id)
     -- усреднённые цены на продукт производства во вселенной
     left outer join esi_markets_prices universe on (emp_type_id=x.type_id)
   ) prices;


create or replace view qi.conveyor_formulas_industry_costs as
 select
  y.*,
  y.single_product_price_wo_fee_tax - single_product_cost as single_product_profit
 from (
  select
   z.*,
   z.total_gross_cost / (z.customized_runs*z.products_per_single_run) as single_product_cost,
   qi.eve_ceiling((z.total_gross_cost * (1 + z.sales_brokers_fee + z.sales_tax)) / (z.customized_runs*z.products_per_single_run)) as product_mininum_price
  from (
   select
    w.*,
    (w.products_recommended_price - w.products_sell_fee_and_tax) / (w.customized_runs*w.products_per_single_run) as single_product_price_wo_fee_tax,
    ( w.materials_cost_with_fee +
      w.jobs_cost + 
      w.materials_transfer_cost + 
      w.ready_transfer_cost
    ) as total_gross_cost
   from (
    select
     -- input and output locations
     r.industry_hub,
     r.trade_hub,
     r.trader_corp,
     -- sales and buying fee and taxes
     r.buying_brokers_fee,
     r.sales_brokers_fee,
     r.sales_tax,
     -- formula
     x.formula,
     x.product_type_id,
     x.customized_runs,
     x.products_per_single_run,
     x.decryptor_type_id,
     x.ancient_relics,
     -- Rhea с 3x ORE Expanded Cargohold имеет 386'404.0 куб.м
     -- из Jita дистанция 35.6 свет.лет со всеми скилами в 5 понадобится сжечь 88'998 Nitrogen Isotopes (buy 545.40 ISK)
     r.fuel_price_isk,
     -- raw material buying details
     --r.input_fuel_quantity,
     x.materials_cost,
     x.materials_cost * (1.0 + r.buying_brokers_fee) as materials_cost_with_fee,
     x.purchase_volume,
     x.purchase_volume * r.input_m3_cost as materials_transfer_cost,
     -- jobs cost
     x.jobs_cost,
     -- ready product selling details
     --r.output_fuel_quantity,
     x.ready_volume,
     case when x.ready_volume <= 386404
      then x.ready_volume * r.output_m3_cost
      else 0
     end ready_transfer_cost,
     x.products_recommended_price,
     x.products_recommended_price * (r.sales_brokers_fee + r.sales_tax) as products_sell_fee_and_tax
    from (
     select
      p.trade_hub,
      cf.cf_formula as formula,
      cf.cf_product_type_id as product_type_id,
      cf.cf_customized_runs as customized_runs,
      t.products_per_single_run as products_per_single_run,
      cf.cf_decryptor_type_id as decryptor_type_id,
      cf.cf_ancient_relics as ancient_relics,
      m.materials_cost,
      j.job_cost as jobs_cost,
      t.purchase_volume,
      t.ready_volume,
      p.hub_recommended_price * cf.cf_customized_runs * t.products_per_single_run as products_recommended_price
     from
      qi.conveyor_formulas cf
       left outer join qi.conveyor_formulas_products_prices p on (p.type_id=cf.cf_product_type_id),
      qi.conveyor_formulas_purchase_materials m,
      qi.conveyor_formulas_jobs_costs j,
      qi.conveyor_formulas_transfer_cost t
     where
      cf.cf_formula=m.formula and
      cf.cf_formula=j.formula and
      cf.cf_formula=t.formula --and cf_formula=2332
     ) x,
     qi.conveyor_formulas_market_routes r
     where x.trade_hub=r.trade_hub --and formula=2332
   ) w
  ) z
 ) y
 --where z.formula in (1157,1189)
 --where z.formula in (2332)
 ;
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- обновляет содержимое предварительно рассчитанного кеша с результатами
-- информации о производстве по conveyor-формулам
--------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE qi.cfc_full_calculus()
LANGUAGE sql
AS $procedure$
  INSERT INTO qi.conveyor_formula_calculus(
   cfc_formula,
   cfc_products_per_single_run,
   cfc_products_num,
   cfc_industry_hub,
   cfc_trade_hub,
   cfc_trader_corp,
   cfc_buying_brokers_fee,
   cfc_sales_brokers_fee,
   cfc_sales_tax,
   cfc_fuel_price_isk,
   cfc_materials_cost,
   cfc_materials_cost_with_fee,
   cfc_purchase_volume,
   cfc_materials_transfer_cost,
   cfc_jobs_cost,
   cfc_ready_volume,
   cfc_ready_transfer_cost,
   cfc_products_recommended_price,
   cfc_products_sell_fee_and_tax,
   cfc_single_product_price_wo_fee_tax,
   cfc_total_gross_cost,
   cfc_single_product_cost,
   cfc_product_mininum_price,
   cfc_single_product_profit,
   cfc_created_at,
   cfc_updated_at)
      SELECT
       formula,
       products_per_single_run,
       products_per_single_run * customized_runs,
       industry_hub,
       trade_hub,
       trader_corp,
       buying_brokers_fee,
       sales_brokers_fee,
       sales_tax,
       fuel_price_isk,
       materials_cost,
       materials_cost_with_fee,
       purchase_volume,
       materials_transfer_cost,
       jobs_cost,
       ready_volume,
       ready_transfer_cost,
       products_recommended_price,
       products_sell_fee_and_tax,
       single_product_price_wo_fee_tax,
       total_gross_cost,
       single_product_cost,
       product_mininum_price,
       single_product_profit,
       CURRENT_TIMESTAMP AT TIME ZONE 'GMT',
       CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
      FROM qi.conveyor_formulas_industry_costs
      --WHERE formula=1782
  ON CONFLICT ON CONSTRAINT pk_cfc DO UPDATE SET
   --pk:cfc_formula = excluded.cfc_formula,
   cfc_products_per_single_run = excluded.cfc_products_per_single_run,
   cfc_products_num = excluded.cfc_products_num,
   --pk:cfc_industry_hub = excluded.cfc_industry_hub,
   --pk:cfc_trade_hub = excluded.cfc_trade_hub,
   --pk:cfc_trader_corp = excluded.cfc_trader_corp,
   cfc_buying_brokers_fee = excluded.cfc_buying_brokers_fee,
   cfc_sales_brokers_fee = excluded.cfc_sales_brokers_fee,
   cfc_sales_tax = excluded.cfc_sales_tax,
   cfc_fuel_price_isk = excluded.cfc_fuel_price_isk,
   cfc_materials_cost = excluded.cfc_materials_cost,
   cfc_materials_cost_with_fee = excluded.cfc_materials_cost_with_fee,
   cfc_purchase_volume = excluded.cfc_purchase_volume,
   cfc_materials_transfer_cost = excluded.cfc_materials_transfer_cost,
   cfc_jobs_cost = excluded.cfc_jobs_cost,
   cfc_ready_volume = excluded.cfc_ready_volume,
   cfc_ready_transfer_cost = excluded.cfc_ready_transfer_cost,
   cfc_products_recommended_price = excluded.cfc_products_recommended_price,
   cfc_products_sell_fee_and_tax = excluded.cfc_products_sell_fee_and_tax,
   cfc_single_product_price_wo_fee_tax = excluded.cfc_single_product_price_wo_fee_tax,
   cfc_total_gross_cost = excluded.cfc_total_gross_cost,
   cfc_single_product_cost = excluded.cfc_single_product_cost,
   cfc_product_mininum_price = excluded.cfc_product_mininum_price,
   cfc_single_product_profit = excluded.cfc_single_product_profit,
   --once:cfc_created_at = excluded.cfc_created_at,
   cfc_updated_at = CASE WHEN
     conveyor_formula_calculus.cfc_products_per_single_run = excluded.cfc_products_per_single_run and
     conveyor_formula_calculus.cfc_products_num = excluded.cfc_products_num and
     conveyor_formula_calculus.cfc_buying_brokers_fee = excluded.cfc_buying_brokers_fee and
     conveyor_formula_calculus.cfc_sales_brokers_fee = excluded.cfc_sales_brokers_fee and
     conveyor_formula_calculus.cfc_sales_tax = excluded.cfc_sales_tax and
     conveyor_formula_calculus.cfc_fuel_price_isk = excluded.cfc_fuel_price_isk and
     conveyor_formula_calculus.cfc_materials_cost = excluded.cfc_materials_cost and
     conveyor_formula_calculus.cfc_materials_cost_with_fee = excluded.cfc_materials_cost_with_fee and
     conveyor_formula_calculus.cfc_purchase_volume = excluded.cfc_purchase_volume and
     conveyor_formula_calculus.cfc_materials_transfer_cost = excluded.cfc_materials_transfer_cost and
     conveyor_formula_calculus.cfc_jobs_cost = excluded.cfc_jobs_cost and
     conveyor_formula_calculus.cfc_ready_volume = excluded.cfc_ready_volume and
     conveyor_formula_calculus.cfc_ready_transfer_cost = excluded.cfc_ready_transfer_cost and
     conveyor_formula_calculus.cfc_products_recommended_price = excluded.cfc_products_recommended_price and
     conveyor_formula_calculus.cfc_products_sell_fee_and_tax = excluded.cfc_products_sell_fee_and_tax and
     conveyor_formula_calculus.cfc_single_product_price_wo_fee_tax = excluded.cfc_single_product_price_wo_fee_tax and
     conveyor_formula_calculus.cfc_total_gross_cost = excluded.cfc_total_gross_cost and
     conveyor_formula_calculus.cfc_single_product_cost = excluded.cfc_single_product_cost and
     conveyor_formula_calculus.cfc_product_mininum_price = excluded.cfc_product_mininum_price and
     conveyor_formula_calculus.cfc_single_product_profit = excluded.cfc_single_product_profit
   THEN conveyor_formula_calculus.cfc_updated_at ELSE excluded.cfc_updated_at END;
  --- --- ---
  UPDATE qi.conveyor_formula_calculus
  SET cfc_best_choice = false;
  --- --- ---
  UPDATE qi.conveyor_formula_calculus
  SET cfc_best_choice = true
  FROM (
   SELECT best_formula.formula
   FROM
    -- поиск минимальных цен на продукты в разных хабах
    (SELECT
      c.cfc_trade_hub trade_hub,
      c.cfc_trader_corp trader_corp,
      f.cf_product_type_id product_type_id,
      min(c.cfc_single_product_cost) min_product_cost
     FROM
      qi.conveyor_formula_calculus c,
      qi.conveyor_formulas f
     WHERE f.cf_formula=c.cfc_formula
     GROUP BY c.cfc_trade_hub, c.cfc_trader_corp, f.cf_product_type_id
    ) min_price
     -- поиск формулы с минимальной стоимостью производства
     LEFT OUTER JOIN (
      SELECT
       f.cf_formula formula,
       c.cfc_trade_hub trade_hub,
       c.cfc_trader_corp trader_corp,
       f.cf_product_type_id product_type_id,
       c.cfc_single_product_cost product_cost
      FROM
       qi.conveyor_formula_calculus c,
       qi.conveyor_formulas f
      WHERE f.cf_formula=c.cfc_formula
     ) best_formula ON (min_price.trade_hub=best_formula.trade_hub AND min_price.trader_corp=best_formula.trader_corp AND min_price.min_product_cost=best_formula.product_cost)
  ) best_formula
  WHERE cfc_formula = best_formula.formula;
$procedure$
;
--------------------------------------------------------------------------------

--call cfc_full_calculus();
