DROP INDEX IF EXISTS qi.idx_eis_pk;
DROP TABLE IF EXISTS qi.esi_industry_systems;

CREATE TABLE qi.esi_industry_systems
(
    eis_system_id BIGINT NOT NULL,
    eis_manufacturing DOUBLE PRECISION NOT NULL DEFAULT 0.0001,
    eis_research_te DOUBLE PRECISION NOT NULL DEFAULT 0.0001,
    eis_research_me DOUBLE PRECISION NOT NULL DEFAULT 0.0001,
    eis_copying DOUBLE PRECISION NOT NULL DEFAULT 0.0001,
    eis_invention DOUBLE PRECISION NOT NULL DEFAULT 0.0001,
    eis_reaction DOUBLE PRECISION NOT NULL DEFAULT 0.0001,
    eis_created_at TIMESTAMP,
    eis_updated_at TIMESTAMP,
    CONSTRAINT pk_eis PRIMARY KEY (eis_system_id)
)
TABLESPACE pg_default;

CREATE UNIQUE INDEX idx_eis_pk
    ON qi.esi_industry_systems USING btree
    (eis_system_id ASC NULLS LAST)
TABLESPACE pg_default;

create or replace view qi.esi_industry_cost_indices as
  select
    eis_system_id as system_id,
    unnest(array[1, 5, 8, 9]) AS activity,
    unnest(array[eis_manufacturing, eis_copying, eis_invention, eis_reaction]) AS cost_index
  from qi.esi_industry_systems;
