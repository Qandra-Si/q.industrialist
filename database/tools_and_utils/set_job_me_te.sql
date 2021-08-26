update qi.esi_blueprint_costs set (ebc_job_time_efficiency, ebc_job_material_efficiency) =
( select
    -- ebc_job_id,
    -- ecj_blueprint_id,
    -- ecb_item_id,
    ecb_time_efficiency,
    ecb_material_efficiency
  from
    qi.esi_corporation_industry_jobs
      left outer join qi.esi_corporation_blueprints on (ecj_blueprint_id = ecb_item_id)
  where
    ebc_job_time_efficiency is null and
    ebc_job_id = ecj_job_id
)

-- select
--   ebc_job_id,
--   ecj_blueprint_id,
--   ecb_item_id,
--   ecb_time_efficiency,
--   ecb_material_efficiency
-- from
--   qi.esi_blueprint_costs,
--   qi.esi_corporation_industry_jobs
--     left outer join qi.esi_corporation_blueprints on (ecj_blueprint_id = ecb_item_id)
-- where ebc_job_id  is not null and ebc_job_id = ecj_job_id
