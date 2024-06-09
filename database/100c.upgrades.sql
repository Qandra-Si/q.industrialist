ALTER TABLE qi.eve_sde_type_ids ADD sdet_group_id integer NOT NULL DEFAULT 0;
ALTER TABLE qi.eve_sde_type_ids ADD sdet_tech_level smallint NULL;

COMMENT ON COLUMN qi.eve_sde_type_ids.sdet_meta_group_id IS 'meta-группа, получаем из sde';
COMMENT ON COLUMN qi.eve_sde_type_ids.sdet_tech_level IS 'технологический уровень 1..5, получаем из esi';
COMMENT ON COLUMN qi.eve_sde_type_ids.sdet_packaged_volume IS 'm3 в упакованном виде, получаем из esi';

-- run:
-- python eve_sde_tools.py --cache_dir=./.q_industrialist
-- python q_dictionaries.py --category=type_ids --cache_dir=./.q_industrialist

CREATE INDEX idx_sdet_group_id
    ON qi.eve_sde_type_ids USING btree
    (sdet_group_id ASC NULLS LAST)
TABLESPACE pg_default;

-- run:
-- python q_universe_preloader.py --category=goods --pilot="Qandra Si" --online --cache_dir=./.q_industrialist

ALTER TABLE qi.eve_sde_type_ids ADD CONSTRAINT fk_sdet_market_group_id FOREIGN KEY (sdet_market_group_id)
REFERENCES qi.eve_sde_market_groups(sdeg_group_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE qi.eve_sde_type_ids ADD CONSTRAINT fk_sdet_group_id FOREIGN KEY (sdet_group_id)
REFERENCES qi.eve_sde_group_ids(sdecg_group_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;

ALTER TABLE qi.eve_sde_group_ids DROP CONSTRAINT fk_sdecg_category_id;
ALTER TABLE qi.eve_sde_group_ids ADD CONSTRAINT fk_sdecg_category_id FOREIGN KEY (sdecg_category_id)
REFERENCES qi.eve_sde_category_ids(sdec_category_id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION;