select
  cnr_route_id,
  idx,
  cnr_path[idx]
from
  qi.cyno_network_routes,
  lateral generate_subscripts(cnr_path, 1) as idx
order by 1, 2;