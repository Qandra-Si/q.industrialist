DROP VIEW IF EXISTS  qi.eve_sde_solar_systems;
DROP INDEX IF EXISTS qi.idx_sdeii_type_id;
DROP INDEX IF EXISTS qi.idx_sdeii_location_id;
DROP INDEX IF EXISTS qi.idx_sdeii_pk;
DROP TABLE IF EXISTS qi.eve_sde_items;

CREATE TABLE qi.eve_sde_items
(
    sdeii_item_id INTEGER NOT NULL,
    sdeii_location_id INTEGER NOT NULL,
    sdeii_type_id INTEGER NOT NULL,
    CONSTRAINT pk_sdeii PRIMARY KEY (sdeii_item_id)
)
TABLESPACE pg_default;

ALTER TABLE qi.eve_sde_items OWNER TO qi_user;

CREATE UNIQUE INDEX idx_sdeii_pk
    ON qi.eve_sde_items USING btree
    (sdeii_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_sdeii_location_id
    ON qi.eve_sde_items USING btree
    (sdeii_location_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_sdeii_type_id
    ON qi.eve_sde_items USING btree
    (sdeii_type_id ASC NULLS LAST)
TABLESPACE pg_default;

create or replace view qi.eve_sde_solar_systems as
  select
   constellation.sdeii_location_id as region_id,
   solar_system.sdeii_location_id as constellation_id,
   solar_system.sdeii_item_id as solar_system_id,
   region_name.sden_name as region,
   constellation_name.sden_name as constellation,
   solar_system_name.sden_name as solar_system
  from
   qi.eve_sde_items solar_system
    left outer join qi.eve_sde_names as solar_system_name on (solar_system_name.sden_category=3 and solar_system_name.sden_id=solar_system.sdeii_item_id)
    left outer join qi.eve_sde_items as constellation on (constellation.sdeii_type_id=4 and solar_system.sdeii_location_id=constellation.sdeii_item_id)
    left outer join qi.eve_sde_names as constellation_name on (constellation_name.sden_category=3 and constellation_name.sden_id=constellation.sdeii_item_id)
    left outer join qi.eve_sde_names as region_name on (region_name.sden_category=3 and region_name.sden_id=constellation.sdeii_location_id)
  where solar_system.sdeii_type_id=5;

