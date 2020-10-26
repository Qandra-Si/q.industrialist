ALTER TABLE qi.workflow_monthly_jobs
    ADD COLUMN wmj_conveyor boolean NOT NULL DEFAULT false;

ALTER TABLE qi.workflow_industry_jobs
    ADD COLUMN wij_quantity integer;


UPDATE qi.workflow_industry_jobs
SET wij_quantity=wij_runs*(SELECT sdei_number FROM qi.eve_sde_integers WHERE sdei_category=5 AND sdei_id=wij_bp_tid)
WHERE wij_activity_id=1; -- manufacturing

UPDATE qi.workflow_industry_jobs
SET wij_quantity=wij_runs*(SELECT sdei_number FROM qi.eve_sde_integers WHERE sdei_category=6 AND sdei_id=wij_bp_tid)
WHERE wij_activity_id=8; -- invention

UPDATE qi.workflow_industry_jobs
SET wij_quantity=wij_runs*(SELECT sdei_number FROM qi.eve_sde_integers WHERE sdei_category=7 AND sdei_id=wij_bp_tid)
WHERE wij_activity_id in (9,11); -- reaction

UPDATE qi.workflow_industry_jobs SET wij_quantity=wij_runs WHERE wij_quantity IS NULL;

SELECT
 wij_job_id,
 wij_activity_id,
 wij_product_tid,
 wij_runs,
 wij_runs*(SELECT sdei_number FROM qi.eve_sde_integers WHERE sdei_category=5 AND sdei_id=wij_bp_tid)
FROM qi.workflow_industry_jobs
WHERE wij_activity_id=1;

SELECT DISTINCT
 wij_bp_tid AS bptid,
 (SELECT sdei_number FROM eve_sde_integers WHERE sdei_id=wij_bp_tid AND sdei_category=5) AS mq,
 (SELECT sdei_number FROM eve_sde_integers WHERE sdei_id=wij_bp_tid AND sdei_category=6) AS iq,
 (SELECT sdei_number FROM eve_sde_integers WHERE sdei_id=wij_bp_tid AND sdei_category=7) AS rq
FROM workflow_industry_jobs;
