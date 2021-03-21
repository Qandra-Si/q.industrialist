select
 (select sden_name from qi.eve_sde_names where sden_category = 3 and sden_id = ebc_system_id) as system,
 ebc_id as id,
 ebc_blueprint_id as bpc_id,
 -- ebc_blueprint_type_id as bpo_type,
 ebc_blueprint_runs as bp_runs,
 ebc_time_efficiency as te,
 ebc_material_efficiency as me,
 ebc_job_id as job_id,
 ecj_blueprint_id as job_bp,
 -- ebc_job_product_type_id as bpc_type,
 ecj_runs as job_runs,
 ebc_job_time_efficiency as job_te,
 ebc_job_material_efficiency as job_me,
 ebc_created_at as dt
from
 qi.esi_blueprint_costs
   left outer join qi.esi_corporation_industry_jobs on (ebc_job_id = ecj_job_id)
where
 -- ebc_created_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '40 hours') and
 ( ebc_blueprint_id is not null and ebc_job_id is null and ebc_blueprint_type_id = 35772 or
   ebc_job_id is not null and ebc_blueprint_id is null and ebc_job_activity = 5 and ebc_job_product_type_id = 35772
 )
order by ebc_created_at desc