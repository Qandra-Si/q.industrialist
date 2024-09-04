DROP VIEW IF EXISTS qi.conveyor_formulas_industry_costs;
DROP VIEW IF EXISTS qi.conveyor_formulas_jobs_costs;
DROP VIEW IF EXISTS qi.conveyor_formulas_purchase_materials;

DROP INDEX IF EXISTS qi.idx_cfj_blueprint_type_id;
DROP INDEX IF EXISTS qi.idx_cfj_formula;
DROP TABLE IF EXISTS qi.conveyor_formula_jobs;

DROP INDEX IF EXISTS qi.idx_cfp_formula_material;
DROP INDEX IF EXISTS qi.idx_cfp_formula;
DROP TABLE IF EXISTS qi.conveyor_formula_purchase;

DROP INDEX IF EXISTS qi.idx_cl_trade_hub;
DROP INDEX IF EXISTS qi.idx_cl_trader_corp;
DROP INDEX IF EXISTS qi.idx_cl_pk;
DROP TABLE IF EXISTS qi.conveyor_limits;

DROP INDEX IF EXISTS qi.idx_cf_decryptor_type_id;
DROP INDEX IF EXISTS qi.idx_cf_product_type_id;
DROP INDEX IF EXISTS qi.idx_unq_cf2;
DROP INDEX IF EXISTS qi.idx_unq_cf1;
DROP INDEX IF EXISTS qi.idx_cf_pk;
DROP TABLE IF EXISTS qi.conveyor_formulas;
DROP SEQUENCE IF EXISTS qi.seq_cf;

DROP TYPE  IF EXISTS qi.esi_formulas_relics;


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
    cf_product_type_id INTEGER NOT NULL,
    cf_customized_runs INTEGER NOT NULL,
    cf_decryptor_type_id INTEGER,
    cf_ancient_relics qi.esi_formulas_relics NOT NULL DEFAULT 'unused',
	cf_prior_blueprint_type_id INTEGER, -- Capital Hull Repairer II делается из разных bpc/bpo
    CONSTRAINT pk_cf PRIMARY KEY (cf_formula),
    CONSTRAINT fk_cf_product_type_id FOREIGN KEY (cf_product_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT fk_cf_decryptor_type_id FOREIGN KEY (cf_decryptor_type_id)
        REFERENCES qi.eve_sde_type_ids(sdet_type_id) MATCH SIMPLE
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
	(cf_blueprint_type_id, cf_product_type_id, cf_customized_runs, cf_ancient_relics, cf_decryptor_type_id, cf_prior_blueprint_type_id)
    WHERE ((cf_decryptor_type_id IS NOT NULL) AND (cf_prior_blueprint_type_id IS NOT NULL));

CREATE UNIQUE INDEX idx_unq_cf2
    ON qi.conveyor_formulas USING btree
	(cf_blueprint_type_id, cf_product_type_id, cf_customized_runs, cf_ancient_relics, cf_prior_blueprint_type_id)
	WHERE ((cf_decryptor_type_id IS NULL) AND (cf_prior_blueprint_type_id IS NOT NULL));

CREATE UNIQUE INDEX idx_unq_cf3
    ON qi.conveyor_formulas USING btree
	(cf_blueprint_type_id, cf_product_type_id, cf_customized_runs, cf_ancient_relics, cf_decryptor_type_id)
    WHERE ((cf_decryptor_type_id IS NOT NULL) AND (cf_prior_blueprint_type_id IS NULL));

CREATE UNIQUE INDEX idx_unq_cf4
    ON qi.conveyor_formulas USING btree
	(cf_blueprint_type_id, cf_product_type_id, cf_customized_runs, cf_ancient_relics)
	WHERE ((cf_decryptor_type_id IS NULL) AND (cf_prior_blueprint_type_id IS NULL));

CREATE INDEX idx_cf_product_type_id
    ON qi.conveyor_formulas USING btree
    (cf_product_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cf_decryptor_type_id
    ON qi.conveyor_formulas USING btree
    (cf_decryptor_type_id ASC NULLS LAST)
TABLESPACE pg_default;


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
    CONSTRAINT fk_cfp_formula FOREIGN KEY (cfj_formula)
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

create or replace view qi.conveyor_formulas_purchase_materials as
  select 
   x.formula,
   sum(x.quantity * coalesce(x.jita_buy, coalesce(x.average_price, x.jita_sell))) as materials_cost
  from (
   select
    f.cf_formula as formula,
    -- cfp_material_type_id as material_type_id,
    cfp_quantity as quantity,
    jita.sell as jita_sell,
    jita.buy as jita_buy,
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

create or replace view qi.conveyor_formulas_industry_costs as
  select
   cf.cf_formula as formula,
   cf.cf_product_type_id as product_type_id,
   cf.cf_customized_runs as customized_runs,
   cf.cf_decryptor_type_id as decryptor_type_id,
   cf.cf_ancient_relics as ancient_relics,
   m.materials_cost,
   j.job_cost,
   (m.materials_cost+j.job_cost) / cf.cf_customized_runs as product_cost
  from
   conveyor_formulas cf,
   conveyor_formulas_purchase_materials m,
   conveyor_formulas_jobs_costs j
  where cf.cf_formula=m.formula and cf.cf_formula=j.formula
  --order by cf.cf_product_type_id, product_cost asc
  ;