<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


function __dump_assets_group_begin(&$market_group) {
?>
<tr><td><?=$market_group?>
<?php
}
function __dump_assets_group_end($sum_price) {
?>
</td><td><?=number_format($sum_price,0,'.',',')?> <?=get_clipboard_copy_button($sum_price)?></td></tr>
<?php
}

function __dump_assets(&$assets) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="text-align: right;">Market Group</th>
  <th style="text-align: right;">Assets Price</th>
 </tr>
</thead>
<tbody>
<?php
    $last_corporation_name = null;
    $last_market_group = null;
    $summary_group_price = 0;
    if ($assets)
    {
        foreach ($assets as &$items)
        {
            $corporation_name = $items['corp'];
            $market_group = $items['mg'];
            $universe_price = $items['up'];
            $base_price = $items['bp'];
            $jita_sell = $items['js'];
            $jita_buy = $items['jb'];

            $summary_order_prices += $universe_price;

            if ($last_corporation_name != $corporation_name)
            {
                if (!is_null($last_market_group))
                {
                    __dump_assets_group_end($summary_group_price);
                    $last_market_group = null;
                    $summary_order_prices = 0;
                }
                $last_corporation_name = $corporation_name;
                ?><tr><td class="active" colspan="2"><strong><?=$corporation_name?></strong></tr><?php
            }
            if ($last_market_group != $market_group)
            {
                if (!is_null($last_market_group))
                {
                    __dump_assets_group_end($summary_group_price);
                }
                __dump_assets_group_begin($market_group);
                $last_market_group = $market_group;
                $summary_order_prices = 0;
            }
        }
        if (!is_null($last_market_group))
        {
            __dump_assets_group_end($summary_group_price);
        }
    }
?>
</tbody>
</table>
<?php
}


function __dump_market_orders(&$market_orders, $is_buy_orders) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="text-align: right;">Corporation</th>
  <th style="text-align: right;">Sum Order Prices</th>
 </tr>
</thead>
<tbody>
<?php
    $summary_order_prices = 0;
    if ($market_orders)
        foreach ($market_orders as &$orders)
        {
            $buy = $orders['buy'];
            if ($is_buy_orders != $buy) continue;
            $corporation_name = $orders['corp'];
            $sum_price = $orders['price'];

            $summary_order_prices += $sum_price;
?>
<tr>
 <td align="right"><?=$corporation_name?></td>
 <td align="right"><?=number_format($sum_price,0,'.',',')?> <?=get_clipboard_copy_button($sum_price)?></td>
</tr>
<?php
        }
?>
<tr style="font-weight:bold;">
 <td colspan="2" align="right">Summary: <?=number_format($summary_order_prices,0,'.',',')?> <?=get_clipboard_copy_button($summary_order_prices)?></td>
</tr>
</tbody>
</table>
<?php
}



    __dump_header("Accounting", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 i.eco_name as corp,
 mg.name as mg,
 a.eca_type_id,
 ceil(sum(a.eca_quantity * universe.price)) as up,
 ceil(sum(a.eca_quantity * jita.sell)) as js,
 ceil(sum(a.eca_quantity * jita.buy)) as jb,
 ceil(sum(a.eca_quantity * t.sdet_base_price)) as bp
from
 qi.esi_corporation_assets a,
 qi.esi_corporations i,
 qi.eve_sde_type_ids t
    -- усреднённые цены по евке прямо сейчас
    left outer join (
      select
        emp_type_id,
        case
          when emp_average_price is null or (emp_average_price < 0.001) then emp_adjusted_price
          else emp_average_price
        end as price
      from qi.esi_markets_prices
    ) universe on (t.sdet_type_id = universe.emp_type_id)
    -- цены в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell as sell, ethp_buy as buy
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (t.sdet_type_id = jita.ethp_type_id)
 ,
 qi.eve_sde_market_groups_semantic mg
where
 a.eca_corporation_id in (98553333, 98615601, 98677876) and
 a.eca_corporation_id = i.eco_corporation_id and
 a.eca_type_id = t.sdet_type_id and
 t.sdet_market_group_id = mg.id and
 mg.semantic_id <> 2 -- without blueprints
group by 1, 2, 3
order by 1, 2, 3;
EOD;
    $assets_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $assets = pg_fetch_all($assets_cursor);
    //---
    $query = <<<EOD
select
 o.ecor_is_buy_order as buy,
 i.eco_name as corp,
 ceil(sum(o.ecor_price * o.ecor_volume_remain)) as price
 -- ,ceil(sum(o.ecor_escrow)) as escrow
from
 qi.esi_corporation_orders o,
 qi.esi_corporations i
where
  o.ecor_corporation_id in (98553333, 98615601, 98677876) and
  o.ecor_corporation_id = i.eco_corporation_id and
  not o.ecor_history
group by 1, 2
order by 1, 2;
EOD;
    $market_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $market = pg_fetch_all($market_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>Assets</h2>
<?php  __dump_assets($assets); ?>

<h2>Sell Market Orders</h2>
<?php  __dump_market_orders($market, 'f'); ?>
<h2>Buy Market Orders</h2>
<?php __dump_market_orders($market, 't'); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
<?php __dump_copy_to_clipboard_javascript() ?>
