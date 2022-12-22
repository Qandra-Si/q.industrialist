DROP INDEX IF EXISTS qi.idx_epb_location_id;
DROP INDEX IF EXISTS qi.idx_epb_type_id;
DROP INDEX IF EXISTS qi.idx_epb_item_id;
DROP INDEX IF EXISTS qi.idx_epb_character_id;
DROP INDEX IF EXISTS qi.idx_epb_pk;
DROP TABLE IF EXISTS qi.esi_pilot_blueprints;

DROP INDEX IF EXISTS qi.idx_epj_pers_status_activity_id;
DROP INDEX IF EXISTS qi.idx_epj_pers_activity_id;
DROP INDEX IF EXISTS qi.idx_epj_pers_status;
DROP INDEX IF EXISTS qi.idx_epj_blueprint_id;
DROP INDEX IF EXISTS qi.idx_epj_station_id;
DROP INDEX IF EXISTS qi.idx_epj_installer_id;
DROP INDEX IF EXISTS qi.idx_epj_corporation_id;
DROP INDEX IF EXISTS qi.idx_epj_pk;
DROP TABLE IF EXISTS qi.esi_pilot_industry_jobs;


--------------------------------------------------------------------------------

CREATE TABLE qi.esi_pilot_industry_jobs
(
    epj_character_id BIGINT NOT NULL,
    epj_job_id BIGINT NOT NULL,
    epj_installer_id BIGINT NOT NULL,
    epj_facility_id BIGINT NOT NULL,
    epj_station_id BIGINT NOT NULL,
    epj_activity_id INTEGER NOT NULL,
    epj_blueprint_id BIGINT NOT NULL,
    epj_blueprint_type_id INTEGER NOT NULL,
    epj_blueprint_location_id BIGINT NOT NULL,
    epj_output_location_id BIGINT NOT NULL,
    epj_runs INTEGER NOT NULL,
    epj_cost DOUBLE PRECISION,
    epj_licensed_runs INTEGER,
    epj_probability DOUBLE PRECISION,
    epj_product_type_id INTEGER,
    epj_status qi.esi_job_status NOT NULL,
    epj_duration INTEGER NOT NULL,
    epj_start_date TIMESTAMP NOT NULL,
    epj_end_date TIMESTAMP NOT NULL,
    epj_pause_date TIMESTAMP,
    epj_completed_date TIMESTAMP,
    epj_completed_character_id INTEGER,
    epj_successful_runs INTEGER,
    epj_created_at TIMESTAMP,
    epj_updated_at TIMESTAMP,
    CONSTRAINT pk_epj PRIMARY KEY (epj_job_id),
    CONSTRAINT fk_epj_character_id FOREIGN KEY (epj_character_id)
        REFERENCES qi.esi_characters(ech_character_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_pilot_industry_jobs OWNER TO qi_user;

CREATE UNIQUE INDEX idx_epj_pk
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_job_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_character_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_installer_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_installer_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_station_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_station_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_blueprint_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_blueprint_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_pers_status
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST, epj_status ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_pers_activity_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST, epj_activity_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epj_pers_status_activity_id
    ON qi.esi_pilot_industry_jobs USING btree
    (epj_character_id ASC NULLS LAST, epj_status ASC NULLS LAST, epj_activity_id ASC NULLS LAST)
TABLESPACE pg_default;

--------------------------------------------------------------------------------

CREATE TABLE qi.esi_pilot_blueprints
(
    epb_character_id BIGINT NOT NULL,
    epb_item_id BIGINT NOT NULL,
    epb_type_id INTEGER NOT NULL,
    epb_location_id BIGINT NOT NULL,
    epb_location_flag CHARACTER VARYING(255) NOT NULL,
    epb_quantity INTEGER NOT NULL,
    epb_time_efficiency SMALLINT NOT NULL,
    epb_material_efficiency SMALLINT NOT NULL,
    epb_runs INTEGER NOT NULL,
    epb_created_at TIMESTAMP,
    epb_updated_at TIMESTAMP,
    CONSTRAINT pk_epb PRIMARY KEY (epb_character_id,epb_item_id),
    CONSTRAINT fk_epb_character_id FOREIGN KEY (epb_character_id)
        REFERENCES qi.esi_characters(ech_character_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)
TABLESPACE pg_default;

ALTER TABLE qi.esi_pilot_blueprints OWNER TO qi_user;

CREATE UNIQUE INDEX idx_epb_pk
    ON qi.esi_pilot_blueprints USING btree
    (epb_character_id ASC NULLS LAST, epb_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_character_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_character_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_item_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_item_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_type_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_type_id ASC NULLS LAST)
TABLESPACE pg_default;

CREATE INDEX idx_epb_location_id
    ON qi.esi_pilot_blueprints USING btree
    (epb_location_id ASC NULLS LAST)
TABLESPACE pg_default;
