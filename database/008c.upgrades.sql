ALTER TABLE qi.eve_sde_type_ids ADD sdet_group_id integer NOT NULL DEFAULT 0;

-- run:
-- python eve_sde_tools.py --cache_dir=./.q_industrialist
-- python q_dictionaries.py --category=type_ids --cache_dir=./.q_industrialist

CREATE INDEX idx_sdet_group_id
    ON qi.eve_sde_type_ids USING btree
    (sdet_group_id ASC NULLS LAST)
TABLESPACE pg_default;

-- run:
-- python q_universe_preloader.py --category=goods --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

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
