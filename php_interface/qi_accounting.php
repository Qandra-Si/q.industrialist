<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';
?>

<?php function __dump_market_orders(&$market_orders, $is_buy_orders) { ?>
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
<h2>Sell Market Orders</h2>
<?php  __dump_market_orders($market, 'f'); ?>
<h2>Sell Market Orders</h2>
<?php __dump_market_orders($market, 't'); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
<?php __dump_copy_to_clipboard_javascript() ?>
