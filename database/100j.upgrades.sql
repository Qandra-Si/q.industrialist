ALTER TABLE qi.esi_markets_prices
  RENAME COLUMN emp_updated_at TO emp_adj_updated_at;

ALTER TABLE qi.esi_markets_prices
  ADD emp_avg_updated_at TIMESTAMP NULL;

UPDATE qi.esi_markets_prices
  SET emp_avg_updated_at = emp_adj_updated_at;
