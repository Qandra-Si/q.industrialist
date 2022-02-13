select -- 18152, 14866 (3,4:8330, 5: 4165 остальные 10069)
 sdeb_blueprint_type_id,
 sdeb_activity,
 sdeb_time,
 sdebp_product_id,
 sdebp_quantity,
 sdebp_probability 
from
 eve_sde_blueprints
  left outer join eve_sde_blueprint_products p on (p.sdebp_blueprint_type_id=sdeb_blueprint_type_id and p.sdebp_activity=sdeb_activity)
--where sdebp_product_id is not null and sdeb_activity not in (3,4,5)
  ;


select
 sdeb_blueprint_type_id,
 sdeb_activity,
 sdeb_time,
 sdebp_product_id,
 sdebp_quantity,
 sdebp_probability 
from (
 select b.* from eve_sde_blueprints b
  inner join eve_sde_type_ids bt on (bt.sdet_type_id=sdeb_blueprint_type_id and bt.sdet_published)
 ) b
  left outer join (
   select p.* from eve_sde_blueprint_products p
    inner join eve_sde_type_ids bt on (bt.sdet_type_id=sdebp_product_id and bt.sdet_published)
  ) p on (sdebp_blueprint_type_id=sdeb_blueprint_type_id AND sdebp_activity=sdeb_activity)
--where sdebp_product_id is not null and sdeb_activity in (3,4,5)
--where sdeb_activity!=8 and sdebp_probability is not null
;

select -- 5877, 5144
 sdebp_product_id,
 sdebp_quantity,
 sdebp_probability 
from
 eve_sde_blueprint_products
  inner join eve_sde_type_ids bt on (bt.sdet_type_id=sdebp_product_id and bt.sdet_published)
;

select
 sdeb_blueprint_type_id,
 sdeb_activity,
 sdeb_time,
 sdebp_product_id,
 sdebp_quantity,
 sdebp_probability,
 bt.sdet_published,
 pt.sdet_type_name,
 pt.sdet_published 
from
 eve_sde_blueprints,
 eve_sde_type_ids bt,
 eve_sde_blueprint_products,
 eve_sde_type_ids pt
  left outer join eve_sde_type_ids pt on () -- and pt.sdet_published)
where not pt.sdet_published and
 sdeb_blueprint_type_id=bt.sdet_type_id and bt.sdet_published and
 sdebp_product_id=pt.sdet_type_id and
 sdebp_blueprint_type_id=sdeb_blueprint_type_id AND sdebp_activity=sdeb_activity and
;

