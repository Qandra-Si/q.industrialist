<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';

$html_style = <<<EOD
<style type="text/css">
body {
 color: #c5c8c9;
 background-color: #162326;
}
a.url {
 color: #ffa600;
}
a:hover.url,
a:focus.url {
 color: #ffa600;
 background-color: #8f6310;
}
hr { border-top: 1px solid #1d3231; }
.panel {
 background-color: #162326;
}
.panel-default > .panel-heading {
 color: #e8e8e8;
 background-color: #21312b;
 border-color: #1d3231;
}
.btn-default {
 color: #c7cccb;
 background-color: #233630;
 border-color: #489579;
}
.btn-default:hover {
 color: #ebefee;
 background-color: #477e6b;
 border-color: #4b8975;
}
.btn-default.active,
.btn-default:active,
.btn-default.focus,
.btn-default:focus,
.open > .dropdown-toggle.btn-default,
.btn-default:active:hover,
.btn-default.active:hover,
.open > .dropdown-toggle.btn-default:hover,
.btn-default:active:focus,
.btn-default.active:focus,
.open > .dropdown-toggle.btn-default:focus,
.btn-default:active.focus,
.btn-default.active.focus,
.open > .dropdown-toggle.btn-default.focus {
 color: #616161;
 background-color: #e7e7e7;
 border-color: #e7e7e7;
}
.page-header { border-bottom: 1px solid #1d3231; }
.table > tbody > tr.active > td,
.table > tbody > tr.active > th,
.table > tbody > tr > td.active,
.table > tbody > tr > th.active,
.table > tfoot > tr.active > td,
.table > tfoot > tr.active > th,
.table > tfoot > tr > td.active,
.table > tfoot > tr > th.active,
.table > thead > tr.active > td,
.table > thead > tr.active > th,
.table > thead > tr > td.active,
.table > thead > tr > th.active { background-color: #2a493e; }
.table > tbody > tr > td { color: inherit; background-color: inherit; }
.table-hover > tbody > tr:hover,
.table > tbody > tr:active > td {
 color: #c4c8c7;
 background-color: #22312e;
}
.activity1 { background-color: #ff9900; }
.activity3,
.activity4,
.activity5,
.activity7,
.activity8 { background-color: #3371b6; }
.activity9,
.activity11 { background-color: #0a7f6f; }
.label-summary {
 font-size: 66%;
 font-weight: unset;
}
mark {
 background-color: #1a302e;
 color: #d8dada;
 padding: .3em .3em .3em;
}
.progress {
 height: 8px;
 margin-bottom: 0px;
 background-color: #232e31;
 border-radius: 0px;
}
.table-gallente { padding: 1px; font-size: smaller; }
.table-gallente thead tr th:nth-child(1),
.table-gallente tbody tr td:nth-child(1) { width: 32px; }
.table-gallente tbody tr:hover td:nth-child(2) { border-left: 1px solid #6db09e; }
.table-gallente thead tr th { padding: 4px; border-bottom: 1px solid #1d3231; vertical-align: bottom; }
.table-gallente tbody tr td { padding: 4px; border-top: none; vertical-align: top; }
.table-gallente tfoot tr td { padding: 4px; border-top: 1px solid #1d3231; }
.table-gallente tbody tr td { border-left: 1px solid #1d3231; }
.table-gallente tbody tr td:nth-child(2) { border-left: none; }
</style>
EOD;

function sys_numbers($var) { return $var <= 2147483647; }
function user_numbers($var) { return $var > 2147483647; }

function __dump_clipboard_waiter($notice) { ?>
<noscript>Вам необходимо включить JavaScript для использования этой программы.</noscript>
<?php if ($notice) { ?>
<center>
<h2>Вставьте содержимое буфера обмена...</h2>
<div class="row">
 <div class="col-md-2"></div>
 <div class="col-md-8">
 <p>В окне контейнера выберите <mark>Режим просмотра (Список)</mark>, затем выделите нужную позицию, щёлкните <kbd>Right-click</kbd> на выбранных строках и выберите "Скопировать". Также можно использовать копирование с помощью кнопок клавиатуры <kbd>Cmd</kbd>&nbsp;|&nbsp;<kbd>Ctrl</kbd>&nbsp;+&nbsp;<kbd>A</kbd>, затем <kbd>Cmd</kbd>&nbsp;|&nbsp;<kbd>Ctrl</kbd>&nbsp;+&nbsp;<kbd>C</kbd>. после чего вернитесь на эту страницу и нажмите <kbd>Cmd</kbd>&nbsp;|&nbsp;<kbd>Ctrl</kbd>&nbsp;+&nbsp;<kbd>V</kbd> для получения отчёта по скопированным предметам.</p>
 </div>
 <div class="col-md-2"></div>
</div> <!--row-->
</center>
<?php } ?>
<script src="/qi_praisal_js.php"></script>
<script>
document.addEventListener('paste', async (e) => {
 e.preventDefault();
 const paste = (e.clipboardData || window.clipboardData).getData('text');
 const lines = paste.split('\n');
 var uri = '';
 for (const line of lines) {
  const words = line.split('\t');
  const len = words.length;
  if (len == 0) continue;
  var t = words[0];
  var tid = getSdeItemId(t);
  if (tid) {
   var cnt = (len >= 2) ? words[1].replace(/\s/g, '') : 1;
   if (!cnt) cnt = 1;
   if (uri) uri += ',';
   uri += tid+','+cnt;
  }
 }
 if (uri) location.assign("<?=strtok($_SERVER['REQUEST_URI'],'?')?>?id="+uri);
});
</script>
<?php }

function __dump_market_hubs_data(&$conn, &$market_hubs) {
  $query = <<<EOD
select
 h.mh_hub_id as hub,
 h.mh_trader_corp as co,
 h.mh_brokers_fee as fee,
 h.mh_trade_hub_tax as tax,
 h.mh_default_profit as pr,
 h.mh_manufacturing_possible as m,
 h.mh_invent_possible as i,
 h.mh_archive as a,
 --c.ech_name as tr,
 s.forbidden as f,
 s.solar_system_name as ss,
 s.station_type_name as snm,
 s.name as nm,
 r.mr_lightyears_src_dst+r.mr_lightyears_dst_src as ly,
 r.mr_isotopes_src_dst+r.mr_isotopes_dst_src as it,
 r.mr_route_src_dst as rs,
 r.mr_route_dst_src as rd
from
 market_hubs h
  --left outer join esi_characters as c on (h.mh_trader_id=c.ech_character_id)
  left outer join market_routes as r on (h.mh_hub_id=r.mr_dst_hub),
 esi_known_stations s
where h.mh_hub_id=s.location_id
order by h.mh_archive, s.forbidden, r.mr_lightyears_dst_src desc;
EOD;
  $params = array();
  $market_hubs_cursor = pg_query_params($conn, $query, $params)
          or die('pg_query err: '.pg_last_error());
  $market_hubs = pg_fetch_all($market_hubs_cursor);

  echo 'g_market_hubs=[';
  foreach ($market_hubs as ["hub" => $hub
           ,"co" => $trader_corp
           ,"fee" => $brokers_fee
           ,"tax" => $trade_hub_tax
           ,"pr" => $default_profit
           ,"m" => $manufacturing_possible
           ,"i" => $invent_possible
           ,"a" => $archive
           ,"f" => $forbidden
           ,"ss" => $solar_system_name
           ,"snm" => $station_type_name
           ,"nm" => $station_name
           ,"ly" => $lightyears
           ,"it" => $isotopes
           ,"rs" => $route_to
           ,"rd" => $route_from
          ])
  {
    echo '['.
            $hub.','. //0
            $trader_corp.','. //1
            $brokers_fee.','. //2
            $trade_hub_tax.','. //3
            $default_profit.','. //4
            (($manufacturing_possible=='t')?1:0).','. //5
            (($invent_possible=='t')?1:0).','. //6
            (($archive=='t')?1:0).','. //7
            (($forbidden=='t')?1:0).','. //8
            '"'.$solar_system_name.'",'. //9
            '"'.$station_type_name.'",'. //10
            '"'.str_replace('"','\"',$station_name).'",'. //11
            (is_null($lightyears)?'null':'"'.$lightyears.'"').','. // 12
            (is_null($isotopes)?'null':'"'.$isotopes.'"').','. //13
            (is_null($route_to)?'null':'"'.$route_to.'"').','. //14
            (is_null($route_from)?'null':'"'.$route_from.'"'). //15
         "]\n,";
  }
  echo "null];\n";
}

function get_active_market_hub_ids(&$market_hubs, &$active_market_hub_ids, &$active_trader_corp_ids)
{
  foreach ($market_hubs as ["hub" => $hub, "co" => $co, "a" => $a, "f" => $f])
  {
    if ($a == 't' || $f == 't') continue; // archive or forbidden
    $active_market_hub_ids[] = intval($hub);
    $active_trader_corp_ids[] = intval($co);
  }
  $active_market_hub_ids = array_unique($active_market_hub_ids, SORT_NUMERIC);
  $active_trader_corp_ids = array_unique($active_trader_corp_ids, SORT_NUMERIC);
}

function __dump_market_orders_data(&$conn, &$market_hubs, &$type_ids, &$sale_orders) {
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $query = <<<EOD
select
 --sell_orders.corp_id,
 sell_orders.type_id as id, -- type_id
 sell_orders.hub_id as hub, -- hub id
 sell_orders.volume_remain as ov, -- our_volume
 round(sell_orders.price_total::numeric, 2) as pt, -- price_total
 sell_orders.price_min as op, -- our_price
 sell_orders.price_max as pm, -- price_max
 sell_orders.orders_total as ot, -- orders_total
 hub_market.total_volume as tv, -- their_volume
 hub_market.min_price as tp -- their_price
from
 -- сводная статистика по текущим ордерам в наших маркетах
 (select
  ecor_corporation_id as corp_id,
  ecor_location_id as hub_id,
  ecor_type_id as type_id,
  sum(ecor_volume_remain) as volume_remain,
  avg(ecor_price*ecor_volume_remain) as price_total,
  min(ecor_price) as price_min,
  max(ecor_price) as price_max,
  count(1) as orders_total
 from esi_corporation_orders
 where
  ecor_type_id=any($3) and
  not ecor_is_buy_order and
  not ecor_history and
  ecor_corporation_id=any($1)
 group by ecor_corporation_id, ecor_location_id, ecor_type_id) sell_orders
  -- локальные цены в этих торговых хабах (исключая наши позиции)
  left outer join (
   select
    etho_location_id as hub_id,
    etho_type_id as type_id,
    min(etho_price) as min_price,
    sum(etho_volume_remain) as total_volume
   from esi_trade_hub_orders -- pk:location_id+oder_id
   where
       etho_type_id=any($3) and
    not etho_is_buy and
    etho_location_id=any($2) and
    etho_order_id not in (
     select ecor_order_id
     from market_hubs, esi_corporation_orders -- pk:corporation_id+order_id
     where ecor_corporation_id=mh_trader_corp and ecor_location_id=mh_hub_id
    )
   group by etho_location_id, etho_type_id
  ) as hub_market on (sell_orders.hub_id=hub_market.hub_id and sell_orders.type_id=hub_market.type_id)
order by sell_orders.type_id;
EOD;
  $params = array('{'.implode(',',$active_trader_corp_ids).'}','{'.implode(',',$active_market_hub_ids).'}','{'.implode(',',$type_ids).'}');
  $sale_orders_cursor = pg_query_params($conn, $query, $params)
          or die('pg_query err: '.pg_last_error());
  $sale_orders = pg_fetch_all($sale_orders_cursor);

  //echo "/*".$query."\n"; var_export($trader_corp_ids); var_export($hub_ids); var_export($type_ids); echo "*/\n";

  echo 'g_sale_orders=[';
  foreach ($sale_orders as ["id" => $type_id,
                            "hub" => $hub,
                            "ov" => $our_volume,
                            "pt" => $price_total,
                            "op" => $our_price,
                            "pm" => $price_max,
                            "ot" => $orders_total,
                            "tv" => $their_volume,
                            "tp" => $their_price
                           ])
  {
    echo '['.
            $type_id.','. //0
            $hub.','. //1
            $our_volume.','. //2
            $price_total.','. //3
            $our_price.','. //4
            $price_max.','. //5
            $orders_total.','. //6
            (is_null($their_volume)?'null':$their_volume).','. //7
            (is_null($their_price)?'null':$their_price). //8
         "]\n,";
  }
  echo "null];\n";
}

function __dump_praisal_table_header(&$market_hubs)
{
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $hubs_count = count($active_market_hub_ids);
  $col_qty = 3;
  $col_uni_pr = 3 + $hubs_count + 3;
  $col_details = $col_uni_pr + 1;
?><style>
#tbl tbody tr td:nth-child(<?=$col_qty?>) { font-size: large; vertical-align: middle; }
<?php foreach (range($col_qty,$col_uni_pr) as $num) { ?>
#tbl thead tr th:nth-child(<?=$num?>),
#tbl tbody tr td:nth-child(<?=$num?>)<?=($num!=$col_uni_pr)?",\n":''?>
<?php } ?> { text-align: right; }
#tbl thead tr th:nth-child(<?=$col_details?>),
#tbl tbody tr td:nth-child(<?=$col_details?>) { text-align: center; }
#tbl tbody tr td:nth-child(<?=$col_details?>) { vertical-align: middle; }
#tbl tbody tr td span.grayed { color : #808080; }
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
  <th>Подробности</th><!--2+hubs+3-->
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
 <td colspan="<?=3+count($active_market_hub_ids)+3+1?>>"></td>
</tr>
</tfoot>
</table>
<?php }

function __dump_praisal_table_row($type_id, $cnt, $t, &$market_hubs, &$sale_orders) {
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $type_name = $t ? $t['sdet_type_name'] : null;
  $hubs_count = count($active_market_hub_ids);
  $col_qty = 3;
  $col_uni_pr = 3 + $hubs_count + 3;
  $col_details = $col_uni_pr + 1;
?>
<tr <?php if (!is_null($t)) { ?>
    sdet_v="<?=$t['sdet_volume']?>"
    sdet_pv="<?=$t['sdet_packaged_volume']?>"
    sdet_c="<?=$t['sdet_capacity']?>"
    sdet_bp="<?=$t['sdet_base_price']?>"
    sdet_mg="<?=$t['sdet_market_group_id']?>"
    sdet_g="<?=$t['sdet_group_id']?>"
    sdet_mt="<?=$t['sdet_meta_group_id']?>"
    sdet_tl="<?=$t['sdet_tech_level']?>"
    sdet_p="<?=($t['sdet_published']=='t')?1:0?>"
    sdet_at="<?=$t['sdet_created_at']?>"
    sdet_js="<?=$t['jita_sell']?>"
    sdet_jb="<?=$t['jita_buy']?>"
    sdet_as="<?=$t['amarr_sell']?>"
    sdet_ab="<?=$t['amarr_buy']?>"
    sdet_up="<?=$t['universe_price']?>"<?php } ?>
>
<td><img class="icn32" src="<?=__get_img_src($type_id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
<td><?=$t?($type_name.get_clipboard_copy_button($type_name)):''?></td>
<td><?=$cnt?></td>

<?php foreach ($active_market_hub_ids as $hub) { ?>
<td>
<?php
  foreach ($sale_orders as ["id" => $_type_id,
                            "hub" => $_hub,
                            "ov" => $our_volume,
                            "pt" => $price_total,
                            "op" => $our_price,
                            "pm" => $price_max,
                            "ot" => $orders_total,
                            "tv" => $their_volume,
                            "tp" => $their_price
                           ])
  {
    if ($type_id != $_type_id) continue;
    if ($hub != $_hub) continue;
    if (is_null($their_price))
    {
      ?><span class="grayed">(<?=$our_volume?>)</span>&nbsp;<?=number_format($our_price,2,'.',',')?><?php
    }
    else
    {
      $color = null;
      if ($their_price < $our_price)
        $color = '#9e6101';
      else if ($their_price > $our_price)
        $color = '#3371b6';
      ?><span class="grayed">(<?=$our_volume?>)</span>&nbsp;<?=$color?'<span style="color:'.$color.'";>':''?><?=number_format($our_price,2,'.',',')?><?=$color?'</span>':''?><br>
        <span class="grayed">(<?=$their_volume?>)&nbsp;<?=number_format($their_price,2,'.',',')?></span><?php
    }
    break;
  }
?>
</td>
<?php } ?>
<td><?php if ($t) {
  $s = $t['jita_sell'];
  $b = $t['jita_buy'];
  if ($s || $b) echo (is_null($s)?'':number_format($s,2,'.',',')).'<br><span class="grayed">'.(is_null($s)?'':number_format($b,2,'.',',').'</span>'); }
?></td>
<td><?php if ($t) {
  $s = $t['amarr_sell'];
  $b = $t['amarr_buy'];
  if ($s || $b) echo (is_null($s)?'':number_format($s,2,'.',',')).'<br><span class="grayed">'.(is_null($s)?'':number_format($b,2,'.',',').'</span>'); }
?></td>
<td><?php if ($t && $t['universe_price']) echo number_format($t['universe_price'],2,'.',','); ?></td>
<td></td>
</tr>
<?php }


__dump_header("Praisal", FS_RESOURCES, $html_style);

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

$query = <<<EOD
select
 tid.*,
 jita.sell as jita_sell,
 jita.buy as jita_buy,
 amarr.sell as amarr_sell,
 amarr.buy as amarr_buy,
 universe.price as universe_price
from eve_sde_type_ids tid
 -- цены в жите прямо сейчас
 left outer join (
   select ethp_type_id, ethp_sell as sell, ethp_buy as buy
   from qi.esi_trade_hub_prices
   where ethp_location_id = 60003760
 ) jita on (tid.sdet_type_id = jita.ethp_type_id)
 -- цены в амарре прямо сейчас
 left outer join (
   select ethp_type_id, ethp_sell as sell, ethp_buy as buy
   from qi.esi_trade_hub_prices
   where ethp_location_id = 60008494
 ) amarr on (tid.sdet_type_id = amarr.ethp_type_id)
 -- усреднённые цены по евке прямо сейчас
 left outer join (
   select
     emp_type_id,
     case
       when emp_average_price is null or (emp_average_price < 0.001) then emp_adjusted_price
       else emp_average_price
     end as price
   from qi.esi_markets_prices
 ) universe on (tid.sdet_type_id = universe.emp_type_id)
where sdet_type_id=any($1);
EOD;
$params = array('{'.implode(',',$sys_type_ids).'}');
$main_data_cursor = pg_query_params($conn, $query, $params)
        or die('pg_query err: '.pg_last_error());
$main_data = pg_fetch_all($main_data_cursor);
if (!$main_data) return;

?><script><?php
$market_hubs = array();
__dump_market_hubs_data($conn, $market_hubs);
$sale_orders = array();
__dump_market_orders_data($conn, $market_hubs, $sys_type_ids, $sale_orders);
?></script><?php

__dump_praisal_table_header($market_hubs);
foreach (range(0,$IDs_len/2-1) as $idx)
{
  $id = $IDs[2*$idx];
  $cnt = $IDs[2*$idx+1];
  $t_key = null;
  foreach ($main_data as $tk => $t)
  {
    $_id = intval($t['sdet_type_id']);
    if ($_id!=$id) continue;
    $t_key = $tk;
    break;
  }
  __dump_praisal_table_row($id, $cnt, is_null($t_key) ? null : $main_data[$t_key], $market_hubs, $sale_orders);
}
__dump_praisal_table_footer($market_hubs);
__dump_clipboard_waiter(false);
pg_close($conn);
__dump_footer();
?>
