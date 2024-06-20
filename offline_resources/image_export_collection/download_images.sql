select sdet_type_id
from qi.eve_sde_type_ids
where sdet_created_at >= '2024-06-11'
order by sdet_created_at;