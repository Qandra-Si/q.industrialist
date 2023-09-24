<?php
include_once '.settings.php';

if (!extension_loaded('pgsql')) return;
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");

$query = <<<EOD
select
 sdet_type_id id,
 sdet_type_name nm
from eve_sde_type_ids
where sdet_published and sdet_market_group_id is not null
order by sdet_type_id;
EOD;
$params = array();
$tid_cursor = pg_query_params($conn, $query, $params)
        or die('pg_query err: '.pg_last_error());
$tid = pg_fetch_all($tid_cursor);
pg_close($conn);

$end = end($tid)['id'];
echo "var g_sde_max_type_id=".$end.";\n".
     "var g_sde_type_len=".count($tid).";\n".
     "var g_sde_type_ids=[";
foreach ($tid as ['id' => $id, 'nm' => $nm]) echo '['.$id.',"'.str_replace('"','\"',$nm).'"]'.(($id==$end)?"\n":',');
echo "];";
unset($tid);
?>
function getSdeItemName(t) {
 if ((t < 0) || (t > g_sde_max_type_id)) return null;
 for (var i=0; i<g_sde_type_len; ++i) {
  var ti = g_sde_type_ids[i][0];
  if (t == ti) return g_sde_type_ids[i][1];
  if (ti >= g_sde_max_type_id) break;
 }
 return null;
} //alert(getSdeItemName(47103));
function getSdeItemId(s) {
 if (!s) return null;
 for (var i=0; i<g_sde_type_len; ++i)
  if (s==g_sde_type_ids[i][1])
   return g_sde_type_ids[i][0];
 return null;
}
