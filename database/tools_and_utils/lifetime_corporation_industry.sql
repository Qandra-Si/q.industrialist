--SET intervalstyle = 'postgres_verbose';
select
  cj.corporation_id as id,
  cj.facility_id as fid,
  cj.updated_at as uat,
  date_trunc('seconds', CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - cj.updated_at)::interval as ui,
  cj.jobs_active as ja,
  cj_stat.jobs_changed as jc,
  c.eco_name as nm,
  ks.name as f
from (
    select
      ecj_corporation_id as corporation_id,
      ecj_facility_id as facility_id,
      max(ecj_updated_at) as updated_at,
      count(1) as jobs_active
    from qi.esi_corporation_industry_jobs
    where ecj_status = 'active'
    group by 1, 2
  ) cj
  left outer join qi.esi_corporations c on (c.eco_corporation_id = cj.corporation_id)
  left outer join qi.esi_known_stations ks on (ks.location_id = cj.facility_id)
  left outer join (
    select
      ecj_corporation_id as corporation_id,
      ecj_facility_id as facility_id,
      count(1) as jobs_changed
    from qi.esi_corporation_industry_jobs
    where ecj_updated_at >= (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' - INTERVAL '15 minutes')
    group by 1, 2
  ) cj_stat on (cj_stat.corporation_id = cj.corporation_id and cj_stat.facility_id = cj.facility_id)
order by c.eco_name, ks.name;
