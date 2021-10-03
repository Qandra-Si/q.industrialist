select
 ci.name as "pilot",
 ca.name as "place",
 sum(case
   when b.quantity = -1 then 1
   when b.quantity > 0 then b.quantity
   else 0
 end) as bpo,
 sum(case
   when b.quantity = -2 then 1
   else 0
 end) as bpc
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
 b.character_id in (2114256252,2116129465,2116746261)
group by 1, b.location_id, 2
order by 1