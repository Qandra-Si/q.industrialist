<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';
?>

<?php function __dump_market_orders(&$market_orders, $is_buy_orders) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Corporation<br><mark>Solar System</mark></th>
  <th style="text-align: right;">Orders<br>Quantity</th>
  <th style="text-align: right;">Remain<br>Quantity</th>
  <th style="text-align: right;">Price<br>Min / Max</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    if ($market_orders)
        foreach ($market_orders as &$product)
        {
            $buy = $product['buy'];
            if ($is_buy_orders != $buy) continue;
            $tid = $product['id'];
            $nm = $product['name'];
            $corp_name = $product['cn'];
            //$region = $product['rn'];
            $solar_system = $product['ssn'];
            $orders_count = $product['oq'];
            $min_price = $product['minp'];
            $max_price = $product['maxp'];
            $remain_quantity = $product['r'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];

            $summary_jita_sell += $jita_sell * $remain_quantity;
            $summary_jita_buy += $jita_buy * $remain_quantity;
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm.'<br><span class="text-muted">'.$tid.'</span> '?></td>
 <td align="right"><?=$corp_name.' <mark>'.$solar_system.'</mark>'?></td>
 <td align="right"><?=number_format($orders_count,0,'.',',')?></td>
 <td align="right"><?=number_format($remain_quantity,0,'.',',')?></td>
 <?php if ($orders_count == 1 || $max_price == $min_price) { ?><td align="right"><?=number_format($max_price,2,'.',',')?></td><?php } else { ?>
 <td align="right"><?=number_format($max_price,2,'.',',')?><br><?=number_format($min_price,2,'.',',')?></td>
 <?php } ?>
 <td align="right"><?=number_format($jita_sell,2,'.',',').'<br>'.number_format($jita_buy,2,'.',',')?></td>
</tr>
<?php
        }
?>
<tr style="font-weight:bold;">
 <td colspan="6" align="right">Jita Summary</td>
 <td align="right"><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
</tr>
</tbody>
</table>
<?php
} ?>



<?php
    $show_querious_sales = 0;
    if (isset($_GET['querious_sales'])) {
        $_get_querious_sales = htmlentities($_GET['querious_sales']);
        if (is_numeric($_get_querious_sales))
            $show_querious_sales = get_numeric($_get_querious_sales) ? 1 : 0;
    }

    $buy_only = 0;
    if (isset($_GET['buy_only'])) {
        $_get_buy_only = htmlentities($_GET['buy_only']);
        if (is_numeric($_get_buy_only))
            $buy_only = get_numeric($_get_buy_only) ? 1 : 0;
    }

    $sell_only = 0;
    if (isset($_GET['sell_only'])) {
        $_get_sell_only = htmlentities($_GET['sell_only']);
        if (is_numeric($_get_sell_only))
            $sell_only = get_numeric($_get_sell_only) ? 1 : 0;
    }

    __dump_header("Market Orders", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  o.is_buy as buy,
  o.type_id as id,
  tid.sdet_type_name as name,
  c.eco_name as cn,
  -- rgn.sden_name as rn,
  hub.solar_system_name as ssn,
  -- hub.name,
  -- hub.station_type_name,
  o.orders as oq,
  o.min_price as minp,
  o.max_price as maxp,
  o.remain as r,
  jita.ethp_sell as js,
  jita.ethp_buy as jb
from (
  select
    ecor_is_buy_order as is_buy,
    ecor_corporation_id as corporation_id,
    ecor_type_id as type_id,
    ecor_region_id as region_id,
    ecor_location_id as trade_hub_id,
    count(1) as orders,
    min(ecor_price) as min_price,
    max(ecor_price) as max_price,
    sum(ecor_volume_remain) as remain
  from qi.esi_corporation_orders
  where
    ecor_corporation_id in (98553333, 98677876, 98615601) and -- R Strike, R Industry, R Initiative 4
    not ecor_history and
    ( $3=0 and ecor_is_buy_order or
      $2=0 and ($1=1 or not ecor_is_buy_order and not (ecor_region_id = 10000050))
    )
  group by 1, 2, 3, 4, 5
) o
  left outer join qi.esi_corporations c on (o.corporation_id = c.eco_corporation_id)
  left outer join qi.eve_sde_type_ids tid on (o.type_id = tid.sdet_type_id)
  -- left outer join qi.eve_sde_names rgn on (o.region_id = rgn.sden_id and rgn.sden_category = 3)
  left outer join qi.esi_known_stations hub on (o.trade_hub_id = hub.location_id )
  left outer join qi.esi_trade_hub_prices jita on (o.type_id = jita.ethp_type_id and jita.ethp_location_id = 60003760)
order by tid.sdet_market_group_id, tid.sdet_type_name, c.eco_name; -- , rgn.sden_name;
EOD;
    $params = array($show_querious_sales, $buy_only, $sell_only);
    $market_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query err: '.pg_last_error());
    $market = pg_fetch_all($market_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php if (!$buy_only) { ?>
  <h2>Sell Orders</h2>
  <?php __dump_market_orders($market, 'f'); ?>
<?php } ?>

<?php if (!$sell_only) { ?>
  <h2>Buy Orders</h2>
  <?php __dump_market_orders($market, 't'); ?>
<?php } ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
