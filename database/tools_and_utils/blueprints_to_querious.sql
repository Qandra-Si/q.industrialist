select
 tt.type_id,
 (select typeName from invTypes where typeID = tt.type_id) as blueprint,
 berg.cnt as "Berg Bee",
 ri.cnt as "R Industry"
from (
 select distinct t.type_id as type_id
 from (
  select
   b.type_id
  from character_blueprints b
  where
   b.location_id not in (60003688,60014659) and
   b.character_id in (2114256252) and
   b.quantity = -2
  union
  select
   b.type_id
  from corporation_blueprints b
  where
   b.corporation_id in (98677876) and
   b.quantity = -2
 ) t
) tt
 left outer join (
   select type_id, count(1) as cnt
   from character_blueprints
   where
    quantity = -2 and
    character_id in (2114256252) and
    location_id not in (60003688,60014659)
   group by 1
 ) berg on (tt.type_id = berg.type_id)
 left outer join (
   select type_id, count(1) as cnt
   from corporation_blueprints
   where
    quantity = -2 and
    corporation_id in (98677876)
   group by 1
 ) ri on (tt.type_id = ri.type_id)
group by tt.type_id
order by 2;

select
 -- ci.name as pilot,
 -- ca.name as place,
 b.type_id,
 (select t.typeName from invTypes t where t.typeID = b.type_id) as blueprint,
 count(1) as quantity
 -- , b.type_id
 -- , b.location_flag
 -- , b.location_id
 -- , b.*
from
 character_blueprints b
   left outer join (
     select character_id, name, item_id, type_id
     from character_assets
   ) ca on (b.character_id = ca.character_id and b.location_id = ca.item_id)
   left outer join character_infos ci on (b.character_id = ci.character_id)
where
 b.location_id not in (60003688,60014659) and
 b.character_id in (2114256252 /*,2116129465,2116746261*/) and
 b.quantity = -2
group by 1, 2 /*b.location_id,*/
order by 2;


create table qi.t1 (
  tid integer not null,
  berg integer,
  ri4 integer
);



insert into t1 (tid,berg,ri4)
values
(28281  ,null    ,1         ),
(43914  ,null    ,1         ),
(28263  ,null    ,2         ),
(28271  ,null    ,3         ),
(28275  ,null    ,3         ),
(28279  ,null    ,63        ),
(28283  ,null    ,3         ),
(28287  ,null    ,5         ),
(28295  ,null    ,6         ),
(28299  ,null    ,36        ),
(28303  ,null    ,3         ),
(28307  ,null    ,11        ),
(33701  ,null    ,6         ),
(33521  ,null    ,6         ),
(33523  ,null    ,2         ),
(41242  ,null    ,5         ),
(11294  ,null    ,7         ),
(20346  ,1       ,3         ),
(12067  ,null    ,31        ),
(12069  ,254     ,null      ),
(12057  ,null    ,9         ),
(12059  ,18      ,55        ),
(819    ,2       ,1         ),
...


select
 '|'||m.name as "market group",
 bp.sdet_type_name as "product name",
 bp.sdet_meta_group_id as "product meta",
 bp.sdebp_product_id as "product id",
 bp.blueprint_type_id as "blueprints id",
 m.id as "market group id",
 bp.berg as "Berg Bee",
 bp.ri4 as "R Initiative"
from
 -- справочник по маркету в древовидном виде
 ( select
    rpad('          ',(m.depth-1)*2)||m.name as name,
    m.id
   from
    qi.eve_sde_market_groups_tree_sorted m
   order by m.rnum
 ) as m
   left outer join (
    select
     tid.sdet_type_name,
     tid.sdet_meta_group_id,
     b.sdebp_product_id,
     t1.tid as blueprint_type_id,
     tid.sdet_market_group_id,
     t1.berg,
     t1.ri4
    from
     qi.t1,
     qi.eve_sde_blueprint_products b,
     qi.eve_sde_type_ids tid
    where
     b.sdebp_blueprint_type_id = t1.tid and 
     b.sdebp_activity = 1 and
     b.sdebp_product_id = tid.sdet_type_id
   ) as bp on (bp.sdet_market_group_id = m.id);

select
 m.name,
 tid.sdet_type_name as "product name",
 tid.sdet_meta_group_id as "product meta",
 b.sdebp_product_id as "product id",
 t1.tid as "blueprints id",
 tid.sdet_market_group_id as "market group id",
 t1.berg as "Berg Bee",
 t1.ri4 as "R Initiative"
from
 qi.t1,
 qi.eve_sde_blueprint_products b,
 qi.eve_sde_type_ids tid,
 qi.eve_sde_market_groups_tree_sorted m
where
 b.sdebp_blueprint_type_id = t1.tid and 
 b.sdebp_activity = 1 and
 b.sdebp_product_id = tid.sdet_type_id and
 m.id = tid.sdet_market_group_id
order by m.rnum;