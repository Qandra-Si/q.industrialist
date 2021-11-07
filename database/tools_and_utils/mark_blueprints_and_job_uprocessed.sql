update esi_blueprint_costs set ebc_job_id = null
WHERE ebc_id IN (SELECT * FROM UNNEST(ARRAY[98746,98745,98744,98743])); -- 
update esi_blueprint_costs set ebc_transaction_type = 'f' where ebc_id = 98661;