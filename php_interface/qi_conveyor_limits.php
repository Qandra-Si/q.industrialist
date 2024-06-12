<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include 'qi_render_products_and_orders.php';
include 'qi_render_trade_hubs.php';
include_once '.settings.php';

function __dump_conveyor_limits(&$conn, &$conveyor_limits) {
  $query = <<<EOD
select
 cl_type_id id,
 cl_trade_hub hub,
 cl_trader_corp co,
 cl_approximate lim
from conveyor_limits;
EOD;
  $conveyor_limits_cursor = pg_query($conn, $query)
          or die('pg_query err: '.pg_last_error());
  $conveyor_limits = pg_fetch_all($conveyor_limits_cursor);

  echo 'g_conveyor_limits=[';
  if ($conveyor_limits)
    foreach ($conveyor_limits as &$t)
    {
      echo '['.
              $t['id'].','. //0
              $t['hub'].','. //1
              $t['co'].','. //2
              $t['lim']. //3
           "],\n";
    }
  echo "null];\n";
}

function get_product_type_ids(&$conveyor_limits, &$product_type_ids) {
  if ($conveyor_limits)
    foreach ($conveyor_limits as ["id" => $prod])
    {
      $product_type_ids[] = intval($prod);
    }
  $product_type_ids = array_unique($product_type_ids, SORT_NUMERIC);
}

function __dump_limits_menu_bar(&$market_hubs) {
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
       <li><a id="btnToggleMarketVolume" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowMarketVolume"></span> Показывать оставшийся объём товара на рынке</a></li>
       <li><a id="btnTogglePercentVolume" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowPercentVolume"></span> Показывать объём в процентах</a></li>
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

function __dump_limits_table_header(&$market_hubs) {
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
their-orders-only {}

limit-grayed { color: #808080; }
limit-grayed:hover { color: #808080; text-shadow: 0 0 0.2vw #808080b2, 0 0 8vw #808080; cursor: default; }
.qind-edit-btn { color: #fddb77; }
.qind-edit-btn:hover, .qind-edit-btn:active, .qind-edit-btn:focus { color: #ffd353; }

remain-volume { color: #808080; }
limit-volume { color: #c5c8c9; }
limit-volume:hover { color: #c5c8c9; text-shadow: 0 0 0.2vw #c5c8c9b2, 0 0 8vw #c5c8c9; cursor: default; }
numeric-volume { }
percent-volume { }

.remain-excess { color : #9e6101; }
.remain-excess:hover { color: #9e6101; text-shadow: 0 0 0.2vw #9e6101b2, 0 0 8vw #9e6101; cursor: default; }
.remain-insufficient { color: #3371b6; }
.remain-insufficient:hover { color: #3371b6; text-shadow: 0 0 0.2vw #3371b6b2, 0 0 8vw #3371b6; cursor: default; }
.remain-bright { color: #c5c8c9; }
.remain-bright:hover { color: #c5c8c9; text-shadow: 0 0 0.2vw #c5c8c9b2, 0 0 8vw #c5c8c9; cursor: default; }
.remain-normal { color: #808080; }
.remain-normal:hover { color: #808080; text-shadow: 0 0 0.2vw #808080b2, 0 0 8vw #808080; cursor: default; }
</style>
<table class="table table-condensed table-hover table-gallente" id="tbl">
<thead>
 <tr>
  <th></th><!--0-->
  <th>Названия предметов</th><!--1-->
  <th>Общ.лимит</th><!--2-->
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
  <th class="hidden">Jita Sell..Buy</th><!--2+hubs+0-->
  <th class="hidden">Amarr Sell..Buy</th><!--2+hubs+1-->
  <th class="hidden">Universe<br>Price</th><!--2+hubs+2-->
 </tr>
</thead>
<tbody>
<?php }

function __dump_limits_table_footer(&$market_hubs) {
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

function __dump_limits_table_row($type_id, $t, &$conveyor_limits, &$market_hubs, &$sale_remain) {
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $cnt = 0;
  if ($conveyor_limits)
  {
    foreach ($conveyor_limits as ["id" => $prod, "lim" => $limit])
      if ($prod == $type_id)
        $cnt += $limit;
  }

  $type_name = $t ? $t['sdet_type_name'] : null;
?>
<tr <?=!is_null($t)?'type_id="'.$type_id.'"':''?>>
<td><img class="icn32" src="<?=__get_img_src($type_id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
      <td><?=$t?('<tid>'.$type_name.get_clipboard_copy_button($type_name)).get_glyph_icon_button('info-sign','class="qind-info-btn"').get_glyph_icon_button('stats','class="qind-edit-btn"').'</tid>':''?></td>
<td><?=is_null($cnt)?'':number_format($cnt,0,'.',',')?></td>
<?php foreach ($active_market_hub_ids as $hub) { ?>
<td hub="<?=$hub?>">
<?php
  $hub_limit = null;
  $our_remain = null;
  if ($conveyor_limits)
    foreach ($conveyor_limits as ["id" => $_type_id, "hub" => $_hub, /*"co" => $corp,*/ "lim" => $limit])
    {
      if ($type_id != $_type_id) continue;
      if ($hub != $_hub) continue;
      $hub_limit = $limit;
      break;
    }
  if ($sale_remain)
    foreach ($sale_remain as ["id" => $_type_id, "hub" => $_hub, "r" => $remain])
    {
      if ($type_id != $_type_id) continue;
      if ($hub != $_hub) continue;
      $our_remain = $remain;
      break;
    }
  $hl_known = !is_null($hub_limit);
  $or_known = !is_null($our_remain);
  if ($hl_known && $or_known)
  {
    $color_remain = null;
    $percent = $our_remain / $hub_limit;
    if ($our_remain > $hub_limit)
      $color_remain = 'remain-excess';
    else if ($percent < 0.1)
      $color_remain = 'remain-insufficient';
    else
      $color_remain = 'remain-normal';
    ?>
    <limit-volume lim="<?=$hub_limit?>"><?=number_format($hub_limit,0,'.',',')?></limit-volume>
    <br>
    <remain-volume class="hidden <?=$color_remain?>"
    >(<numeric-volume><?=number_format($our_remain,0,'.',',')?></numeric-volume
    ><percent-volume class="hidden"><?=number_format($percent*100,0,'.',',')?>%</percent-volume
    >)</remain-volume>
    <?php
  }
  else if ($hl_known)
  {
    ?><limit-volume lim="<?=$hub_limit?>"><?=number_format($hub_limit,0,'.',',')?></limit-volume><?php
  }
  else if ($or_known)
  {
    $color_remain = 'color_remain';
    ?><limit-volume></limit-volume><br><remain-volume class="hidden">(<?='<'.$color_remain.'>'.number_format($our_remain,0,'.',',').'</'.$color_remain.'>'?>)</remain-volume><?php
  }
?>
</td>
<?php } ?>
<td class="hidden"><?php
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
<td class="hidden"><?php
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
<td class="hidden"><?php if ($t && $t['universe_price']) echo '<price_ordinal>'.number_format($t['universe_price'],2,'.',',').'</price_ordinal>'; ?></td>
</tr>
<?php }

function __dump_edit_limit_dialog(&$market_hubs) { ?>
<div class="modal fade" id="modalLimits" tabindex="-1" role="dialog" aria-labelledby="modalLimitsLabel">
 <div class="modal-dialog modal-sm" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modalLimitsLabel"></h4>
   </div>
   <div class="modal-body">
<!-- -->
<ul class="nav nav-tabs">
  <li role="presentation" class="active"><a href="#navOverstocks" aria-controls="navOverstocks" role="tab" data-toggle="tab">Ограничения</a></li>
</ul>
<div class="tab-content">
  <!-- -->
  <div role="tabpanel" class="tab-pane active" id="navOverstocks">
<?php
  foreach ($market_hubs as ["hub" => $hub, "co" => $co, "a" => $a, "f" => $f, "ss" => $ss])
  {
    if ($a == 't' || $f == 't') continue; // archive or forbidden
    ?>
<div class="row" hub="<?=$hub?>" corp="<?=$co?>">
 <div class="col-md-4"><?=$ss?></div>
 <div class="col-md-8" align="right">
  <input type="text" class="form-control">
 </div>
</div><?php
  }
?>
  </div>
  <!-- -->
</div> <!--tab-content-->
<!-- -->
    <form id="frmSetupLimits" class="hidden">
     <input type="hidden" name="tid" readonly>
     <input type="hidden" name="hub" readonly>
     <input type="hidden" name="corp" readonly>
     <input type="hidden" name="limit" readonly>
    </form>
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal" id="limSubmit">Сохранить</button>
    <button type="button" class="btn btn-default" data-dismiss="modal">Отменить</button>
   </div>
  </div>
 </div>
</div>
<?php }


__dump_header("Conveyor Limits", FS_RESOURCES, "", true);

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
$conveyor_limits = array();
__dump_conveyor_limits($conn, $conveyor_limits);
$product_type_ids = array();
get_product_type_ids($conveyor_limits, $product_type_ids);
//echo var_export($product_type_ids);
$main_data = array();
__dump_main_data($conn, $product_type_ids, $main_data);
$market_hubs = array();
__dump_market_hubs_data($conn, $market_hubs);
//$sale_orders = array();
//__dump_market_orders_data($conn, $market_hubs, $product_type_ids, $sale_orders);
$sale_remain = array();
__dump_market_orders_remain($conn, $market_hubs, $sale_remain);
?></script><?php

__dump_limits_menu_bar($market_hubs);
__dump_limits_table_header($market_hubs);
foreach ($product_type_ids as $num => $id)
{
  $t_key = get_main_data_tkey($main_data, $id);
  __dump_limits_table_row($id, is_null($t_key) ? null : $main_data[$t_key], $conveyor_limits, $market_hubs, $sale_remain);
}
__dump_limits_table_footer($market_hubs);
//__dump_clipboard_waiter(false);
pg_close($conn);
__dump_market_hubs_dialog($market_hubs);
__dump_products_and_orders_dialog($market_hubs);
__dump_edit_limit_dialog($market_hubs);
__dump_copy_to_clipboard_javascript();
?><script><?php
include 'qi_conveyor_limits.js'; /*используется copy_to_clipboard*/
include 'qi_render_trade_hubs.js';
include 'qi_render_products_and_orders.js'
?></script>
<?php __dump_footer(); ?>
