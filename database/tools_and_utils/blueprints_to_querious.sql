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
order by 2