DROP INDEX IS EXISTS qi.idx_ecor_corporation_location_id;

CREATE INDEX qi.idx_ecor_corporation_location_id
    ON qi.esi_corporation_orders USING btree
    (ecor_corporation_id ASC NULLS LAST, ecor_location_id ASC NULLS LAST)
TABLESPACE pg_default;
