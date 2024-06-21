<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include 'qi_render_products_and_orders.php';
include 'qi_render_trade_hubs.php';
include_once '.settings.php';

function __dump_blueprints_data(&$conn, &$type_ids, &$blueprints_data) {
  $query = <<<EOD
select x.bp, x.act, x.prod
from (
 select p.sdebp_blueprint_type_id as bp, 1 as act, p.sdebp_product_id as prod
 from eve_sde_blueprint_products p
 where sdebp_blueprint_type_id=any($1) and sdebp_activity=1
 union
 select p1.sdebp_blueprint_type_id, 8, p2.sdebp_product_id
 from eve_sde_blueprint_products p1, eve_sde_blueprint_products p2
 where
  p1.sdebp_blueprint_type_id=any($1) and
  p1.sdebp_activity=8 and
  p2.sdebp_blueprint_type_id=p1.sdebp_product_id and
  p2.sdebp_activity=1
 ) x
order by 1, 2, 3;
EOD;
  $params = array('{'.implode(',',$type_ids).'}');
  $blueprints_data_cursor = pg_query_params($conn, $query, $params)
          or die('pg_query err: '.pg_last_error());
  $blueprints_data = pg_fetch_all($blueprints_data_cursor);

  echo 'g_blueprints_data=[';
  if ($blueprints_data)
    foreach ($blueprints_data as &$t)
    {
      echo '['.
              $t['bp'].','. //0
              $t['act'].','. //1
              $t['prod']. //2
           "],\n";
    }
  echo "null];\n";
}

function get_product_type_ids(&$blueprints_data, &$product_type_ids)
{
  if ($blueprints_data)
    foreach ($blueprints_data as ["prod" => $prod])
    {
      $product_type_ids[] = intval($prod);
    }
  $product_type_ids = array_unique($product_type_ids, SORT_NUMERIC);
}

function __dump_praisal_menu_bar(&$market_hubs)
{
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);
?>
<style>
.dropdown-submenu { position: relative; }
.dropdown-submenu .dropdown-menu { top: 0; left: 100%; margin-top: -1px; }
</style>
<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-navbar-collapse" aria-expanded="false">
    <span class="sr-only">Настройки таблицы</span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
   </button>
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>
  </div>
  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Настройки таблицы <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a id="btnToggleJitaPrice" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowJitaPrice"></span> Показывать Jita Price</a></li>
       <li><a id="btnToggleAmarrPrice" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowAmarrPrice"></span> Показывать Amarr Price</a></li>
       <li><a id="btnToggleUniversePrice" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowUniversePrice"></span> Показывать Universe Price</a></li>
       <li class="dropdown-submenu">
        <a class="options-submenu" data-target="#" role="button">Скрыть системы <mark id="lbHiddenMarketHubs">-</mark><span class="caret"></span></a>
        <ul class="dropdown-menu" style="display: none;">
<?php
  foreach ($market_hubs as ["hub" => $hub, "a" => $a, "f" => $f, "ss" => $solar_system_name])
  {
    if ($a == 't' || $f == 't') continue; // archive or forbidden
    ?><li><a id="btnToggleHub<?=$hub?>" hub="<?=$hub?>" class="option toggle-hub-option" data-target="#" role="button"><span class="glyphicon glyphicon-star hidden" aria-hidden="true"></span> <?=$solar_system_name?></a></li><?php
  }
?>
        </ul>
       </li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleMarketVolume" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowMarketVolume"></span> Показывать объём товара на рынке</a></li>
       <li><a id="btnToggleBestOffer" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBestOffer"></span> Показывать объём лучшего предложения</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleOurOrdersOnly" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowOurOrdersOnly"></span> Скрыть цены без наших ордеров (логист)</a></li>
        <li><a id="btnToggleTheirOrdersOnly" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowTheirOrdersOnly"></span> Показывать предложения конкурентов (торговец)</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnResetOptions" data-target="#" role="button">Сбросить все настройки</a></li>
      </ul>
    </li>
    <li><a id="btnShowMarketHubs" data-target="" role="button" data-toggle="modal">Торговые хабы</a></li>
   </ul>
  </div>
 </div>
</nav>
<?php }

function __dump_praisal_table_header(&$market_hubs)
{
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $hubs_count = count($active_market_hub_ids);
  $col_qty = 3;
  $col_uni_pr = 3 + $hubs_count + 3;
?><style>
#tbl tbody tr td:nth-child(<?=$col_qty?>) { font-size: large; vertical-align: middle; }
<?php foreach (range($col_qty,$col_uni_pr) as $num) { ?>
#tbl thead tr th:nth-child(<?=$num?>),
#tbl tbody tr td:nth-child(<?=$num?>)<?=($num!=$col_uni_pr)?",\n":''?>
<?php } ?> { text-align: right; }
grayed { color : #808080; }
price_warning { color : #9e6101; }
price_warning:hover { color: #9e6101; text-shadow: 0 0 0.2vw #9e6101b2, 0 0 8vw #9e6101; cursor: default; }
price_normal { color: #3371b6; }
price_normal:hover { color: #3371b6; text-shadow: 0 0 0.2vw #3371b6b2, 0 0 8vw #3371b6; cursor: default; }
price_ordinal { color: #c5c8c9; }
price_ordinal:hover { color: #c5c8c9; text-shadow: 0 0 0.2vw #c5c8c9b2, 0 0 8vw #c5c8c9; cursor: default; }
price_grayed { color: #808080; }
price_grayed:hover { color: #808080; text-shadow: 0 0 0.2vw #808080b2, 0 0 8vw #808080; cursor: default; }
tid { white-space: nowrap; }
.qind-info-btn { color: #808080; }
.qind-info-btn:hover, .qind-info-btn:active, .qind-info-btn:focus { color: #aaa; }
market-volume { color: #808080; }
best-offer { color: #9e6101; }
their-orders-only {}
</style>
<table class="table table-condensed table-hover table-gallente" id="tbl">
<thead>
 <tr>
  <th></th><!--0-->
  <th>Названия предметов</th><!--1-->
  <th>Кол-во</th><!--2-->
<?php foreach ($active_market_hub_ids as $hub) { ?>
  <th id="tbl-hub<?=$hub?>">
<?php
  foreach ($market_hubs as ["hub" => $_hub, "a" => $a, "f" => $f, "ss" => $solar_system_name])
  {
    if ($a == 't' || $f == 't') continue; // archive or forbidden
    if ($hub != $_hub) continue;
    echo $solar_system_name;
    break;
  }
?>
  </th>
<?php } ?>
  <th>Jita Sell..Buy</th><!--2+hubs+0-->
  <th>Amarr Sell..Buy</th><!--2+hubs+1-->
  <th>Universe<br>Price</th><!--2+hubs+2-->
 </tr>
</thead>
<tbody>
<?php }

function __dump_praisal_table_footer(&$market_hubs)
{
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);
?>
</tbody>
<tfoot>
<tr>
 <td colspan="<?=3+count($active_market_hub_ids)+3?>>"></td>
</tr>
</tfoot>
</table>
<?php }

function __dump_praisal_table_row($type_id, $cnt, $t, &$market_hubs, &$sale_orders) {
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $type_name = $t ? $t['sdet_type_name'] : null;
?>
<tr <?=!is_null($t)?'type_id="'.$type_id.'"':''?>>
<td><img class="icn32" src="<?=__get_img_src($type_id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
      <td><?=$t?('<tid>'.$type_name.get_clipboard_copy_button($type_name)).get_glyph_icon_button('info-sign','class="qind-info-btn"').'</tid>':''?></td>
<td><?=is_null($cnt)?'':number_format($cnt,0,'.',',')?></td>
<?php foreach ($active_market_hub_ids as $hub) { ?>
<td>
<?php
  if ($sale_orders)
    foreach ($sale_orders as ["id" => $_type_id,
                              "hub" => $_hub,
                              "ov" => $our_volume,
                              "pt" => $price_total,
                              "op" => $our_price,
                              "pm" => $price_max,
                              "ot" => $orders_total,
                              "tv" => $their_volume,
                              "tp" => $their_price,
                              "bo" => $best_offer_volume
                             ])
    {
      if ($type_id != $_type_id) continue;
      if ($hub != $_hub) continue;
      $op_known = !is_null($our_price);
      $tp_known = !is_null($their_price);
      if ($op_known && $tp_known)
      {
        $color = null;
        if ($their_price < $our_price)
          $color = 'price_warning';
        else if ($their_price > $our_price)
          $color = 'price_normal';
        else
          $color = 'price_ordinal';
        ?><market-volume>(<?=$our_volume?>)</market-volume>&nbsp;<?='<'.$color.'>'.number_format($our_price,2,'.',',').'</'.$color.'>'?><br>
          <market-volume>(<?=(is_null($best_offer_volume))?'':'<best-offer>'.$best_offer_volume.'<grayed>/</grayed></best-offer>'?><?=$their_volume?>)</market-volume>&nbsp;<price_ordinal><?=number_format($their_price,2,'.',',')?></price_ordinal><?php
      }
      else if ($tp_known)
      {
        ?><their-orders-only><br>
          <market-volume>(<?=$their_volume?>)</market-volume>&nbsp;<price_ordinal><?=number_format($their_price,2,'.',',')?></price_ordinal></their-orders-only><?php
      }
      else if ($op_known)
      {
        ?><market-volume>(<?=$our_volume?>)</market-volume>&nbsp;<price_ordinal><?=number_format($our_price,2,'.',',')?></price_ordinal><?php
      }
      break;
    }
?>
</td>
<?php } ?>
<td><?php
 if ($t) {
  $s = $t['jita_sell'];
  $b = $t['jita_buy'];
  if ($s || $b) {
   if (!(is_null($s))) { ?><?='<price_ordinal>'.number_format($s,2,'.',',').'</price_ordinal>'?><?php }
   echo '<br>';
   if (!(is_null($b))) { ?><?='<price_grayed>'.number_format($b,2,'.',',').'</price_grayed>'?><?php }
  }
 }
?></td>
<td><?php
 if ($t) {
  $s = $t['amarr_sell'];
  $b = $t['amarr_buy'];
  if ($s || $b) {
   if (!(is_null($s))) { ?><?='<price_ordinal>'.number_format($s,2,'.',',').'</price_ordinal>'?><?php }
   echo '<br>';
   if (!(is_null($b))) { ?><?='<price_grayed>'.number_format($b,2,'.',',').'</price_grayed>'?><?php }
  }
 }
?></td>
<td><?php if ($t && $t['universe_price']) echo '<price_ordinal>'.number_format($t['universe_price'],2,'.',',').'</price_ordinal>'; ?></td>
</tr>
<?php }


__dump_header("Praisal", FS_RESOURCES, "", true);

// ---------------------------
// IDs
// ---------------------------
$IDs = null;
if (isset($_GET['id'])) {
  $_get_id = htmlentities($_GET['id']);
  if (is_numeric($_get_id)) $IDs = array(get_numeric($_get_id));
  else if (is_numeric_array($_get_id)) $IDs = get_numeric_array($_get_id);
}

if (is_null($IDs))
{
  __dump_clipboard_waiter(true);
  __dump_footer();
  return;
}

$IDs_len = count($IDs);
if ($IDs_len == 1)
{
  $IDs[] = 1;
  $IDs_len = 2;
}

if (($IDs_len > 2) && (($IDs_len%2) != 0))
{
  ?><script>location.assign("<?=strtok($_SERVER['REQUEST_URI'],'?')?>");</script><?php
  __dump_clipboard_waiter(true);
  __dump_footer();
  return;
}

$type_ids = array();
foreach (range(0,$IDs_len/2-1) as $idx) $type_ids[] = $IDs[2*$idx];
$type_ids = array_unique($type_ids, SORT_NUMERIC);
$sys_type_ids = array_filter($type_ids, "sys_numbers");

// ---------------------------
// DATABASE
// ---------------------------
if (!extension_loaded('pgsql'))
{
  __dump_footer();
  return;
}
$conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
        or die('pg_connect err: '.pg_last_error());
pg_exec($conn, "SET search_path TO qi");

?><script><?php
$blueprints_data = array();
__dump_blueprints_data($conn, $sys_type_ids, $blueprints_data);
$product_type_ids = array();
get_product_type_ids($blueprints_data, $product_type_ids);
$merged_type_ids = array_merge($sys_type_ids, $product_type_ids);

$main_data = array();
__dump_main_data($conn, $merged_type_ids, $main_data);
$market_hubs = array();
__dump_market_hubs_data($conn, $market_hubs);
$sale_orders = array();
__dump_market_orders_data($conn, $market_hubs, $merged_type_ids, $sale_orders);
?></script><?php

__dump_praisal_menu_bar($market_hubs);
__dump_praisal_table_header($market_hubs);
foreach (range(0,$IDs_len/2-1) as $idx)
{
  $id = $IDs[2*$idx];
  $cnt = $IDs[2*$idx+1];
  $t_key = get_main_data_tkey($main_data, $id);
  __dump_praisal_table_row($id, $cnt, is_null($t_key) ? null : $main_data[$t_key], $market_hubs, $sale_orders);
  if ($blueprints_data)
    foreach ($blueprints_data as ["bp" => $bp, "act" => $act, "prod" => $prod])
    {
      $_bp = intval($bp);
      if ($_bp!=$id) continue;
      if ($_bp>$id) break;
      $_prod = intval($prod);
      $t_key = get_main_data_tkey($main_data, $prod);
      __dump_praisal_table_row($prod, null, is_null($t_key) ? null : $main_data[$t_key], $market_hubs, $sale_orders);
    }
}
__dump_praisal_table_footer($market_hubs);
__dump_clipboard_waiter(false);
pg_close($conn);

__dump_market_hubs_dialog($market_hubs);
__dump_products_and_orders_dialog($market_hubs);
__dump_copy_to_clipboard_javascript();
?><script><?php
include 'qi_praisal.js'; /*используется copy_to_clipboard*/
include 'qi_render_trade_hubs.js';
include 'qi_render_products_and_orders.js';
?></script>
<?php __dump_footer(); ?>
