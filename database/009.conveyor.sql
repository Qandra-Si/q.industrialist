-- UTF-8 without BOM
-- скрипт выполняется от имени пользователя qi_user
-- скрипт создаёт в базе данных таблицы для настройки работы конвейера

CREATE SCHEMA IF NOT EXISTS qi AUTHORIZATION qi_user;


---
DROP INDEX IF EXISTS qi.idx_cl_trade_hub;
DROP INDEX IF EXISTS qi.idx_cl_trader_corp;
DROP INDEX IF EXISTS qi.idx_cl_pk;
DROP TABLE IF EXISTS qi.conveyor_limits;

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

DROP INDEX IF EXISTS qi.idx_cf_product_type_id;
DROP INDEX IF EXISTS qi.idx_cf_decryptor_type_id;
DROP INDEX IF EXISTS qi.idx_cf_pk;
DROP TABLE IF EXISTS qi.conveyor_formulas;
DROP SEQUENCE IF EXISTS qi.seq_cf;

DROP TYPE  IF EXISTS qi.esi_formulas_relics;



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


--------------------------------------------------------------------------------
-- расчёт эффективности производства на основе производственных формул
--------------------------------------------------------------------------------
CREATE TYPE qi.esi_formulas_relics AS ENUM ('intact','malfunctioning','wrecked');

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
    cf_product_type_id INTEGER NOT NULL,
    cf_customized_runs INTEGER NOT NULL,
    cf_decryptor_type_id INTEGER NULL,
    cf_ancient_relics qi.esi_formulas_relics NULL,
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

CREATE UNIQUE INDEX idx_unq_conveyor_formulas
    ON qi.conveyor_formulas USING btree
    (cf_product_type_id ASC NULLS LAST,
	 cf_customized_runs ASC NULLS LAST,
	 cf_decryptor_type_id ASC NULLS LAST,
	 cf_ancient_relics ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cf_product_type_id
    ON qi.conveyor_formulas USING btree
    (cf_product_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_cf_decryptor_type_id
    ON qi.conveyor_formulas USING btree
    (cf_decryptor_type_id ASC NULLS LAST)
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
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- представления для расчёта стоимости проектов по conveyor-формулам
--------------------------------------------------------------------------------
create or replace view qi.conveyor_formulas_purchase_materials as
  select
   cfp_material_type_id as material_type_id,
   cfp_quantity as quantity,
   jita.sell as jita_sell,
   jita.buy as jita_buy,
   universe.emp_average_price as average_price
  from
   conveyor_formula_purchase p
    left outer join (
     select ethp_type_id, ethp_sell as sell, ethp_buy as buy
     from esi_trade_hub_prices
     where ethp_location_id = 60003760
    ) jita on (p.cfp_material_type_id = jita.ethp_type_id)
    left outer join esi_markets_prices universe on (p.cfp_material_type_id = universe.emp_type_id);

create or replace view qi.conveyor_formulas_jobs_costs as
  select
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
  --order by 4, w.cfj_usage_chain desc
  ;
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
-- формула производства Purifier
--------------------------------------------------------------------------------
INSERT INTO qi.conveyor_formulas VALUES
  (101, 12038,10,34203,NULL);

INSERT INTO qi.conveyor_formula_purchase VALUES
  (100, 20416, 8.714596949891067),
  (100, 20421, 8.714596949891067),
  (100, 34203, 4.357298474945534),
  (100, 11399, 361.0),
  (100, 9848, 15.274070612161408),
  (100, 44, 52.186407924884826),
  (100, 3689, 52.186407924884826),
  (100, 9832, 117.35577587010683),
  (100, 16275, 260.9320396244241),
  (100, 3683, 286.8979596650984),
  (100, 16272, 2216.522213668155),
  (100, 16273, 4563.383163226758),
  (100, 17888, 3089.0376124455465),
  (100, 16637, 2093.6796858277494),
  (100, 16644, 2581.326816616639),
  (100, 16634, 1178.2871197996944),
  (100, 16635, 1606.098930297674),
  (100, 17887, 553.998157753175),
  (100, 16636, 513.1501100479798),
  (100, 16643, 303.8663922590909),
  (100, 16647, 291.46398305909094),
  (100, 17889, 312.7879288487672),
  (100, 16642, 319.3136088590909),
  (100, 16648, 319.3136088590909),
  (100, 16641, 335.0254956388889),
  (100, 16652, 1158.2392440333335),
  (100, 16650, 136.5859152),
  (100, 16649, 214.71338815000001),
  (100, 16274, 1911.2013909272437),
  (100, 16646, 1247.3622976333334),
  (100, 16651, 152.6973568),
  (100, 16633, 85.33829954999999),
  (100, 34, 227758.63136363638),
  (100, 35, 42788.91),
  (100, 36, 17837.955),
  (100, 37, 3577.3),
  (100, 3828, 285.0),
  (100, 38, 8.924090909090909),
  (100, 16653, 23.3222682);
 
 
INSERT INTO qi.conveyor_formula_jobs VALUES
  (100, 1.0, 30001115, 12041, 1, 10, 1, 1, 1.0, -0.05, 0.0, 0.04, 0.0),
  (100, 4.357298474945534, 30001115, 12041, 1, 1, 8, 1, 0.02, 0.0, 0.0, 0.04, 0.0),
  (100, 4.357298474945534, 30001115, 937, 1, 1, 5, 1, 0.02, -0.05, 0.0, 0.04, 0.0),
  (100, 0.7916666666666666, 30001113, 17349, 1, 360, 1, 1, 1.0, -0.04, 0.0, 0.04, 0.0),
  (100, 1.4500048055555557, 30001115, 46207, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.13403209148459874, 30001115, 4314, 1, 60, 1, 1, 1.0, -0.05, 0.0, 0.04, 0.0),
  (100, 1.4271845165833335, 30001113, 46178, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.8031950373549382, 30001113, 46181, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.2872324915824916, 30001115, 46210, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.024037755792648708, 30001115, 4313, 1, 60, 1, 1, 1.0, -0.05, 0.0, 0.04, 0.0),
  (100, 0.1404566883838384, 30001113, 46179, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.15635462171717174, 30001113, 46166, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.18278235505050505, 30001113, 46183, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.013571741608398804, 30001115, 4316, 1, 60, 1, 1, 1.0, -0.05, 0.0, 0.04, 0.0),
  (100, 0.07133333333333333, 30001115, 46213, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.18604890432098767, 30001113, 46174, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.034881999999999996, 30001113, 46175, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.034881999999999996, 30001113, 46172, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.05077993333333333, 30001113, 46184, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.7916666666666666, 30001113, 17334, 2, 360, 1, 1, 1.0, -0.04, 0.0, 0.04, 0.0),
  (100, 0.18034814814814815, 30001115, 46211, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.14636222777777777, 30001113, 46177, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.08819024444444445, 30001113, 46176, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.0829262546503772, 30001115, 4315, 1, 60, 1, 1, 1.0, -0.05, 0.0, 0.04, 0.0),
  (100, 1.4394012345679013, 30001115, 46216, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.7038672037037037, 30001113, 46186, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.1189611111111111, 30001115, 46209, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.05817198333333333, 30001113, 46167, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 1.0, 30001115, 937, 1, 10, 1, 1, 1.0, -0.05, 0.0, 0.04, 0.0),
  (100, 0.7916666666666666, 30001113, 17336, 2, 360, 1, 1, 1.0, -0.04, 0.0, 0.04, 0.0),
  (100, 0.08655555555555555, 30001115, 46212, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.042325666666666664, 30001113, 46180, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.0582236, 30001113, 46170, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.7907407407407407, 30001113, 17330, 3, 720, 1, 1, 1.0, -0.04, 0.0, 0.04, 0.0),
  (100, 0.013181818181818182, 30001115, 11890, 1, 22, 1, 1, 1.0, -0.05, 0.0, 0.04, 0.0),
  (100, 0.6587962962962963, 30001113, 17350, 2, 2160, 1, 1, 1.0, -0.04, 0.0, 0.04, 0.0),
  (100, 0.30913477366255143, 30001115, 46208, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.15116690432098764, 30001113, 46168, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.31666666666666665, 30001113, 17338, 1, 180, 1, 1, 1.0, -0.04, 0.0, 0.04, 0.0),
  (100, 0.03251111111111111, 30001115, 46214, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.015897933333333333, 30001113, 46173, 1, 15, 9, 9, 1.0, 0.0, 0.0, 0.04, 0.0),
  (100, 0.3972222222222222, 30001113, 17359, 1, 360, 1, 1, 1.0, -0.04, 0.0, 0.04, 0.0);
--------------------------------------------------------------------------------

-- получаем справку в конце выполнения всех запросов
\d+ qi.
