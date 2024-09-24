select
 b.sdebp_blueprint_type_id as blueprint_type_id,
 b.sdebp_product_id as product_type_id,
 bpt.sdet_type_name as blueprint,
 pt.sdet_type_name as product
from
 eve_sde_blueprint_products b,
 eve_sde_type_ids bpt,
 eve_sde_type_ids pt
where
 b.sdebp_activity=1 and
 b.sdebp_blueprint_type_id in (
  select sdebp_blueprint_type_id --,count(1)
  from eve_sde_blueprint_products
  group by sdebp_blueprint_type_id
  having count(1)=1
 ) and
 b.sdebp_blueprint_type_id not in (
  select distinct sdebp_product_id
  from eve_sde_blueprint_products
 ) and
 b.sdebp_blueprint_type_id=bpt.sdet_type_id and
 bpt.sdet_published and
 b.sdebp_product_id=pt.sdet_type_id and
 pt.sdet_published
;