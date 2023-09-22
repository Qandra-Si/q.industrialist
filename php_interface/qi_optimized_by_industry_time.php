<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';
?>

<?php function __dump_components($components) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;">Used in</th>
  <th style="width:32px;"></th>
  <th>Material</th>
  <th>Group</th>
  <th>Category</th>
  <th>Time</th>
  <th>Min<br>Max</th>
  <th>Jita sell<br>Jita buy</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($components as &$item)
    {
        $cnt = $item['cnt'];
        $id = $item['id'];
        $nm = $item['name'];
        $grp = $item['group'];
        $cat = $item['category'];
        $gid = $item['g_id'];
        $cid = $item['c_id'];
        $tm = $item['time'];
        $min = $item['min'];
        $max = $item['max'];
        $jita_sell = $item['js'];
        $jita_buy = $item['jb'];
?>
<tr>
<td><?=$cnt?></td>
<td><img class="icn32" src="<?=__get_img_src($id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
<td><strong><?=$nm?></strong><br><span class="text-muted">(<?=$id?>)</span></td>
<td><?=$grp?><br><span class="text-muted">(<?=$gid?>)</span></td>
<td><?=$cat?><br><span class="text-muted">(<?=$cid?>)</span></td>
<td><?=is_null($tm)?'':$tm?></td>
<td><?=$min?><br><?=$max?></td>
<td><?=is_null($jita_sell)?'':number_format($jita_sell,2,'.',',')?><br><?=is_null($jita_buy)?'':number_format($jita_buy,2,'.',',')?></td>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php
    $use_times = 5;
    if (isset($_GET['times'])) {
        $_get_times = htmlentities($_GET['times']);
        if (is_numeric($_get_times))
            $use_times = get_numeric($_get_times);
    }

    __dump_header("Optimized by Industry Time", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 x.cnt,
 x.id,
 t.sdet_type_name as name,
 g.sdecg_group_name as group,
 c.sdec_category_name as category,
 g.sdecg_group_id as g_id,
 c.sdec_category_id as c_id,
 x.min,
 x.max,
 jita.sell as js,
 jita.buy as jb,
 tm.time
from (
 select
  x.sdebm_material_id as id,
  count(1) as cnt,
  min(x.sdebm_quantity) as min,
  max(x.sdebm_quantity) as max
 from eve_sde_blueprint_materials x
 where
  x.sdebm_activity = 1 and
  x.sdebm_material_id in (select z.sdebp_product_id from eve_sde_blueprint_products z)
 group by 1
) x
   left outer join qi.eve_sde_type_ids t on (t.sdet_type_id=x.id)
   left outer join qi.eve_sde_group_ids g on (t.sdet_group_id=g.sdecg_group_id)
   left outer join qi.eve_sde_category_ids c on (g.sdecg_category_id=c.sdec_category_id)
   -- цены в жите прямо сейчас
   left outer join (
    select ethp_type_id, ethp_sell as sell, ethp_buy as buy
    from qi.esi_trade_hub_prices
    where ethp_location_id = 60003760
   ) jita on (x.id = jita.ethp_type_id)
   -- длительность производства продукта
   left outer join (
    select
     --p.sdebp_blueprint_type_id,
     --p.sdebp_activity,
     p.sdebp_product_id as id,
     min(b.sdeb_time) as time
    from qi.eve_sde_blueprint_products p, qi.eve_sde_blueprints b
    where
     b.sdeb_blueprint_type_id=p.sdebp_blueprint_type_id and
     b.sdeb_activity=p.sdebp_activity and
     b.sdeb_activity=1
    group by 1
    having count(1)=1) tm on (x.id=tm.id)
where
 x.cnt >= $1 and
 g.sdecg_group_id not in (
  873, -- Capital Construction Components
  536, -- Structure Components
  913 -- Advanced Capital Construction Components
 ) and
 c.sdec_category_id not in (
  6, -- Ship
  23, -- Starbase
  18, -- Drone
  8, -- Charge
  66 -- Structure Module
 )
order by x.cnt;;
EOD;
    $params = array($use_times);
    $components_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $components = pg_fetch_all($components_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_components($components); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
