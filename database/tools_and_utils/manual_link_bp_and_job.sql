update qi.esi_blueprint_costs set (
 ebc_job_id,
 ebc_job_corporation_id,
 ebc_job_activity,
 ebc_job_runs,
 ebc_job_product_type_id,
 ebc_job_successful_runs,
 ebc_job_time_efficiency,
 ebc_job_material_efficiency,
 ebc_job_cost,
 ebc_industry_payment,
 ebc_tax,
 ebc_created_at,
 ebc_updated_at) =
(select
  ebc_job_id,
  ebc_job_corporation_id,
  ebc_job_activity,
  ebc_job_runs,
  ebc_job_product_type_id,
  ebc_job_successful_runs,
  ebc_job_time_efficiency,
  ebc_job_material_efficiency,
  ebc_job_cost,
  ebc_industry_payment,
  ebc_tax,
  ebc_created_at,
  CURRENT_TIMESTAMP AT TIME ZONE 'GMT'
 from
  qi.esi_blueprint_costs
 where
  ebc_job_id = 453608972 and ebc_blueprint_id is null
)
where ebc_blueprint_id = 1035847911915
