<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';

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
<script src="/tools/tids.php"></script>
<script>
document.addEventListener('paste', async (e) => {
 e.preventDefault();
 const paste = (e.clipboardData || window.clipboardData).getData('text');
 const lines = paste.split('\n');
 var uri = '';
 for (const line of lines) {
<?php
/* == Форматы копируемой информации ==
Имущество (режим просмотра, список):
10MN Afterburner II	45	Propulsion Module			225 м^3	109 222 217,10 ISK
10MN Afterburner II<t><right>45<t>Propulsion Module<t><t><t><right>225 м^3<t><right>109 222 217,10 ISK
Имущество (режим просмотра, информация):
10MN Afterburner II	45	Propulsion Module			225 м^3	109 222 217,10 ISK
10MN Afterburner II<t><right>45<t>Propulsion Module<t><t><t><right>225 м^3<t><right>109 222 217,10 ISK
Имущество (режим просмотра, пиктограммы):
10MN Afterburner II	45
Мои ордера:
10MN Afterburner II	5/5	2 546 000,00 ISK	B2J-5N - Shukhov (R)	Malpais	89д 23ч 48мин 12с
10MN Afterburner II<t><right>5/5<t><right><color='0xFFFFFFFF'>2 546 000,00 ISK</color></right><t>B2J-5N - Shukhov (R)<t>Malpais<t>89д 23ч 41мин 47с
Корпоративные ордера:
10MN Afterburner II	5/5	2 546 000,00 ISK	B2J-5N - Shukhov (R)	Malpais	89д 23ч 41мин 20с	Qandra Si	Главный счет 
10MN Afterburner II<t><right>5/5<t><right><color='0xFFFFFFFF'>2 546 000,00 ISK</color></right><t>B2J-5N - Shukhov (R)<t>Malpais<t>89д 23ч 42мин 46с<t>Qandra Si<t>Главный счет 
История заказов:
Отменён	2023.09.24 16:33:00	Warp Disruptor II	10 / 10	1 757 000,00 ISK	B2J-5N - Shukhov (R)	Malpais
Отменён<t>2023.09.24 16:33:00<t>Warp Disruptor II<t>10 / 10<t><right>1 757 000,00 ISK</right><t>B2J-5N - Shukhov (R)<t>Malpais
*/
?>
  const words = line.split('\t');
  const len = words.length;
  if (len == 0) continue;
  var t = words[0];
  var tid = getSdeItemId(t);
  if (tid) {
   var cnt = 1;
   if (len >= 2) {
    cnt = words[1];
    if (cnt.includes('/')) cnt = cnt.split('/')[0];
    cnt = cnt.replace(/\s/g, '');
    if (!cnt) cnt = 1;
   }
   if (uri) uri += ',';
   uri += tid+','+cnt;
  }
 }
 if (uri) location.assign("<?=strtok($_SERVER['REQUEST_URI'],'?')?>?id="+uri);
});
</script>
<?php }

function __dump_main_data(&$conn, &$type_ids, &$main_data) {
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
  $params = array('{'.implode(',',$type_ids).'}');
  $main_data_cursor = pg_query_params($conn, $query, $params)
          or die('pg_query err: '.pg_last_error());
  $main_data = pg_fetch_all($main_data_cursor);

  echo 'g_main_data=[';
  foreach ($main_data as &$t)
  {
    $at = $t['sdet_created_at'];
    $bp = $t['sdet_base_price'];
    $mgi = $t['sdet_meta_group_id'];
    $tl = $t['sdet_tech_level'];
    echo '['.
            $t['sdet_type_id'].','. //0
            '"'.str_replace('"','\"',$t['sdet_type_name']).'",'. //1
            $t['sdet_volume'].','. //2
            $t['sdet_packaged_volume'].','. //3
            $t['sdet_capacity'].','. //4
            (is_null($bp)?'null':$bp).','. //5
            $t['sdet_market_group_id'].','. //6
            $t['sdet_group_id'].','. //7
            (is_null($mgi)?'null':$mgi).','. //8
            (is_null($tl)?'null':$tl).','. //9
            (($t['sdet_published']=='t')?1:0).','. //10
            (is_null($at)?'null':'"'.$at.'"').','. //11
            $t['jita_sell'].','. //12
            $t['jita_buy'].','. //13
            $t['amarr_sell'].','. //14
            $t['amarr_buy'].','. //15
            $t['universe_price']. //16
         "],\n";
  }
  echo "null];\n";
}

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
         "],\n";
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
 hub_market.min_price as tp, -- their_price
 their_best_offer.remain as bo -- their best offer volume (remain)
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
  -- кол-во предметов, которые продаются не нами по цене ниже нашей
  left outer join (
   select
    etho_location_id as hub_id,
    etho_type_id as type_id,
    sum(etho_volume_remain) as remain
   from esi_trade_hub_orders h
   where
    etho_type_id=any($3) and
    not etho_is_buy and
    etho_location_id=any($2) and
    etho_price < (
     select min(ecor_price)
     from esi_corporation_orders
     where
      not ecor_is_buy_order and
      not ecor_history and
      ecor_corporation_id=any($1) and
      etho_type_id=ecor_type_id and etho_location_id=ecor_location_id
     group by ecor_type_id
    )
   group by etho_location_id, etho_type_id
  ) as their_best_offer on (sell_orders.hub_id=their_best_offer.hub_id and sell_orders.type_id=their_best_offer.type_id)
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
                            "tp" => $their_price,
                            "bo" => $best_offer_volume
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
            (is_null($their_price)?'null':$their_price).','. //8
            (is_null($best_offer_volume)?'null':$best_offer_volume). //9
         "],\n";
  }
  echo "null];\n";
}

function __dump_praisal_menu_bar() { ?>
<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-navbar-collapse" aria-expanded="false">
    <span class="sr-only">Переключить навигацию</span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
   </button>
   <a class="navbar-brand" data-target="#"><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>
  </div>
  <div class="collapse navbar-collapse" id="bs-navbar-collapse">
   <ul class="nav navbar-nav">
    <li class="dropdown">
     <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Настройки отображения <span class="caret"></span></a>
      <ul class="dropdown-menu">
       <li><a id="btnToggleJitaPrice" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowJitaPrice"></span> Показывать Jita Price</a></li>
       <li><a id="btnToggleAmarrPrice" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowAmarrPrice"></span> Показывать Amarr Price</a></li>
       <li><a id="btnToggleUniversePrice" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowUniversePrice"></span> Показывать Universe Price</a></li>
       <li role="separator" class="divider"></li>
       <li><a id="btnToggleMarketVolume" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowMarketVolume"></span> Показывать объём товара на рынке</a></li>
       <li><a id="btnToggleBestOffer" data-target="#" role="button"><span class="glyphicon glyphicon-star" aria-hidden="true" id="imgShowBestOffer"></span> Показывать объём лучшего предложения</a></li>
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
price_normal { color: #3371b6; }
tid { white-space: nowrap; }
.qind-info-btn { color: #808080; }
.qind-info-btn:hover, .qind-info-btn:active, .qind-info-btn:focus { color: #aaa; }
market-volume { color: #808080; }
best-offer { color: #9e6101; }
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
                            "tp" => $their_price,
                            "bo" => $best_offer_volume
                           ])
  {
    if ($type_id != $_type_id) continue;
    if ($hub != $_hub) continue;
    if (is_null($their_price))
    {
      ?><market-volume>(<?=$our_volume?>)</market-volume>&nbsp;<?=number_format($our_price,2,'.',',')?><?php
    }
    else
    {
      $color = null;
      if ($their_price < $our_price)
        $color = 'price_warning';
      else if ($their_price > $our_price)
        $color = 'price_normal';
      ?><market-volume>(<?=$our_volume?>)</market-volume>&nbsp;<?=$color?'<'.$color.'>':''?><?=number_format($our_price,2,'.',',')?><?=$color?'</'.$color.'>':''?><br>
        <market-volume>(<?=(is_null($best_offer_volume))?'':'<best-offer>'.$best_offer_volume.'<grayed>/</grayed></best-offer>'?><?=$their_volume?>)&nbsp;<?=number_format($their_price,2,'.',',')?></market-volume><?php
    }
    break;
  }
?>
</td>
<?php } ?>
<td><?php if ($t) {
  $s = $t['jita_sell'];
  $b = $t['jita_buy'];
  if ($s || $b) echo (is_null($s)?'':number_format($s,2,'.',',')).'<br><grayed>'.(is_null($s)?'':number_format($b,2,'.',',').'</grayed>'); }
?></td>
<td><?php if ($t) {
  $s = $t['amarr_sell'];
  $b = $t['amarr_buy'];
  if ($s || $b) echo (is_null($s)?'':number_format($s,2,'.',',')).'<br><grayed>'.(is_null($s)?'':number_format($b,2,'.',',').'</grayed>'); }
?></td>
<td><?php if ($t && $t['universe_price']) echo number_format($t['universe_price'],2,'.',','); ?></td>
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
$main_data = array();
__dump_main_data($conn, $sys_type_ids, $main_data);
$market_hubs = array();
__dump_market_hubs_data($conn, $market_hubs);
$sale_orders = array();
__dump_market_orders_data($conn, $market_hubs, $sys_type_ids, $sale_orders);
?></script><?php

__dump_praisal_menu_bar();
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
?>


<style>
table.table-market-hubs thead tr th:nth-child(2),
table.table-market-hubs thead tr th:nth-child(3),
table.table-market-hubs thead tr th:nth-child(4),
table.table-market-hubs thead tr th:nth-child(5),
table.table-market-hubs thead tr th:nth-child(6),
table.table-market-hubs thead tr th:nth-child(7),
table.table-market-hubs tbody tr td:nth-child(2),
table.table-market-hubs tbody tr td:nth-child(3),
table.table-market-hubs tbody tr td:nth-child(4),
table.table-market-hubs tbody tr td:nth-child(5),
table.table-market-hubs tbody tr td:nth-child(6),
table.table-market-hubs tbody tr td:nth-child(7) { text-align: right; }
</style>
<div class="modal fade" id="modalMarketHubs" tabindex="-1" role="dialog" aria-labelledby="modalMarketHubs">
 <div class="modal-dialog modal-lg" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modalMarketHubsLabel"></h4>
   </div>
   <div class="modal-body">
   <!-- -->
<h3>Активные хабы</h3>
<table id="tblHubs" class="table table-condensed table-market-hubs table-hover" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Хаб</th>
  <th>Пошлина<br>КпБТ,%</th>
  <th>Комиссия<br>брокера,%</th>
  <th>Налог с<br>продаж,%</th>
  <th>Маржа,%</th>
  <th>Дистанция,сл</th>
  <th>Изотопы,шт</th>
  <th>Маршрут</th>
 </tr>
</thead>
<tbody>
</tbody>
</table>
<h3>Архивные хабы</h3>
<table id="tblArchiveHubs" class="table table-condensed table-market-hubs" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>Хаб</th>
  <th>Пошлина<br>КпБТ,%</th>
  <th>Комиссия<br>брокера,%</th>
  <th>Налог с<br>продаж,%</th>
  <th>Маржа,%</th>
  <th>Дистанция,сл</th>
  <th>Изотопы,шт</th>
  <th>Маршрут</th>
 </tr>
</thead>
<tbody>
</tbody>
</table>
   <!-- -->
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Закрыть</button>
   </div>
  </div>
 </div>
</div>


<div class="modal fade" id="modalDetails" tabindex="-1" role="dialog" aria-labelledby="modalDetailsLabel">
 <div class="modal-dialog modal-lg" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modalDetailsLabel"></h4>
   </div>
   <div class="modal-body">
<!-- -->
<ul class="nav nav-tabs">
  <li role="presentation" class="active"><a href="#navPrice" aria-controls="navPrice" role="tab" data-toggle="tab">Цены</a></li>
  <li role="presentation"><a href="#navAssets" aria-controls="navAssets" role="tab" data-toggle="tab">Имущество</a></li>
  <li role="presentation"><a href="#navTrade" aria-controls="navTrade" role="tab" data-toggle="tab">Торговля</a></li>
  <li role="presentation"><a href="#navDetails" aria-controls="navDetails" role="tab" data-toggle="tab">Характеристики</a></li>
</ul>
<div class="tab-content">
  <!-- -->
  <div role="tabpanel" class="tab-pane active" id="navPrice">
    <div class="row">
      <div class="col-md-8">Текущая Jita Sell цена</div>
      <div class="col-md-4" align="right"><mark id="dtlsJitaSell"></mark> ISK<?=get_glyph_icon_button('copy','id="copyJitaSell" data-copy="" class="qind-copy-btn" data-toggle="tooltip"')?></div>
    </div>
    <div class="row">
      <div class="col-md-8">Текущая Jita Buy цена</div>
      <div class="col-md-4" align="right"><mark id="dtlsJitaBuy"></mark> ISK<?=get_glyph_icon_button('copy','id="copyJitaBuy" data-copy="" class="qind-copy-btn" data-toggle="tooltip"')?></div>
    </div>
    <div class="row">
      <div class="col-md-8">Текущая Amarr Sell цена</div>
      <div class="col-md-4" align="right"><mark id="dtlsAmarrSell"></mark> ISK<?=get_glyph_icon_button('copy','id="copyAmarrSell" data-copy="" class="qind-copy-btn" data-toggle="tooltip"')?></div>
    </div>
    <div class="row">
      <div class="col-md-8">Текущая Amarr Buy цена</div>
      <div class="col-md-4" align="right"><mark id="dtlsAmarrBuy"></mark> ISK<?=get_glyph_icon_button('copy','id="copyAmarrBuy" data-copy="" class="qind-copy-btn" data-toggle="tooltip"')?></div>
    </div>
    <div class="row">
      <div class="col-md-8">Средняя цена товара на Tranquility</div>
      <div class="col-md-4" align="right"><mark id="dtlsUniversePrice"></mark> ISK<?=get_glyph_icon_button('copy','id="copyUniversePrice" data-copy="" class="qind-copy-btn" data-toggle="tooltip"')?></div>
    </div>
    <div class="row">
    <div class="col-md-8">Базовая цена (установленная CCP-шниками)</div>
      <div class="col-md-4" align="right"><mark id="dtlsBasePrice"></mark> ISK<?=get_glyph_icon_button('copy','id="copyBasePrice" data-copy="" class="qind-copy-btn" data-toggle="tooltip"')?></div>
    </div>
  </div>
  <!-- -->
  <div role="tabpanel" class="tab-pane" id="navDetails">
    <div class="row">
      <div class="col-md-4">Занимаемый объём</div>
      <div class="col-md-8" align="right"><div id="dtlsVolume"></div></div>
    </div>
    <div class="row">
      <div class="col-md-8">Вместимость грузового отсека</div>
      <div class="col-md-4" align="right"><mark id="dtlsCapacity"></mark> m³</div>
    </div>
    <hr>
    <div class="row">
      <div class="col-md-8">Идентификатор предмета</div>
      <div class="col-md-4" align="right"><mark id="dtlsTypeId"></mark><?=get_glyph_icon_button('copy','id="copyTypeId" data-copy="" class="qind-copy-btn" data-toggle="tooltip"')?></div>
    </div>
    <div class="row">
      <div class="col-md-8">Идентификатор market-группы</div>
      <div class="col-md-4" align="right"><mark id="dtlsMarketGroupId"></mark></div>
    </div>
    <div class="row">
      <div class="col-md-8">Идентификатор группы</div>
      <div class="col-md-4" align="right"><mark id="dtlsGroupId"></mark></div>
    </div>
    <div class="row">
      <div class="col-md-8">Идентификатор meta-группы</div>
      <div class="col-md-4" align="right"><mark id="dtlsMetaGroupId"></mark></div>
    </div>
    <div class="row">
      <div class="col-md-8">Идентификатор технологического уровня</div>
      <div class="col-md-4" align="right"><mark id="dtlsTechLevelId"></mark></div>
    </div>
    <div class="row">
      <div class="col-md-8">Предмет опубликован</div>
      <div class="col-md-4" align="right"><mark id="dtlsPublished"></mark></div>
    </div>
    <div class="row">
      <div class="col-md-8">Предмет зарегистрирован в БД</div>
      <div class="col-md-4" align="right"><mark id="dtlsCreatedAt"></mark></div>
    </div>
  </div>
  <!-- -->
  <div role="tabpanel" class="tab-pane" id="navTrade">
    <!-- -->
    <center>
      <nav aria-label="Market Hubs" id="dtlsSelMarketHub">
       <ul class="pagination pagination-sm">
<?php
  foreach ($market_hubs as ["hub" => $hub, "co" => $co, "a" => $a, "f" => $f, "ss" => $ss])
  {
    if ($a == 't' || $f == 't') continue; // archive or forbidden
    ?><li hub="<?=$hub?>" corp="<?=$co?>"><a href="#"><?=$ss?></a></li><?php
  }
?>
       </ul>
      </nav>
    </center>
    <div class="row">
     <div class="col-md-5">
      Текущие ордера в маркете
<style type="text/css">
.tblMarketOrders-wrapper { max-height: 300px; overflow: auto; scrollbar-color: #696969 #262727; scrollbar-width: thin; }
.tblMarketOrders-wrapper table { padding:1px; font-size: x-small; width: 100%; }
.tblMarketOrders-wrapper thead th { position: sticky; top: 0; z-index: 1; color: #7f7f7f; background-color: #202020; text-align:center; }
.tblMarketOrders-wrapper tbody tr td:nth-child(1) { text-align: right; font-weight: bold; }
.tblMarketOrders-wrapper tbody tr td:nth-child(2) { text-align: right; }
.tblMarketOrders-wrapper tbody tr td:nth-child(3) { text-align: center; }
.tblMarketOrders-wrapper tbody tr td:nth-child(4) { text-align: left; }
.tblMarketOrders-wrapper tbody tr td:nth-child(5) { text-align: left; font-weight: bold; }
</style>
    <div class="tblMarketOrders-wrapper">
     <table id="tblMarketOrders">
      <thead>
       <tr>
        <th style="width:30%;" colspan="2">Покупка</th>
        <th style="width:40%;">Цена,&nbsp;ISK</th>
        <th style="width:30%;" colspan="2">Продажа</th>
       </tr>
      </thead>
      <tbody>
      </tbody>
     </table>
     <form id="frmMarketOrders">
      <input type="hidden" name="corp" readonly value="">
      <input type="hidden" name="hub" readonly value="">
      <input type="hidden" name="tid" readonly>
     </form>
    </div>
    <!-- -->
     </div>
     <div class="col-md-7">
      Хронология изменений ордеров
    <!-- -->
<style type="text/css">
.tblMarketHistory-wrapper { max-height: 300px; overflow: auto; scrollbar-color: #696969 #262727; scrollbar-width: thin; }
.tblMarketHistory-wrapper table { padding:1px; font-size: x-small; width: 100%; }
.tblMarketHistory-wrapper thead th { position: sticky; top: 0; z-index: 1; color: #7f7f7f; background-color: #202020; text-align:center; }
.tblMarketHistory-wrapper tbody tr td:nth-child(1) { text-align: left; }
.tblMarketHistory-wrapper tbody tr td:nth-child(2) { text-align: right; }
.tblMarketHistory-wrapper tbody tr td:nth-child(3) { text-align: center; }
.tblMarketHistory-wrapper tbody tr td:nth-child(4) { text-align: left; }
.tblMarketHistory-wrapper tbody tr td:nth-child(5) { text-align: right; }
.tblMarketHistory-wrapper tbody tr td:nth-child(6) { text-align: right; }
</style>
    <div class="tblMarketHistory-wrapper">
     <table id="tblMarketHistory">
      <thead>
       <tr>
        <th style="width:21%;" colspan="2">Покупка</th>
        <th style="width:28%;">Цена,&nbsp;ISK</th>
        <th style="width:21%;" colspan="2">Продажа</th>
        <th style="width:30%;">Длительность ордера</th>
       </tr>
      </thead>
      <tbody>
      </tbody>
     </table>
     <form id="frmMarketHistory">
      <input type="hidden" name="corp" readonly value="">
      <input type="hidden" name="hub" readonly value="">
      <input type="hidden" name="tid" readonly>
     </form>
    </div>
     </div>
    </div>
  </div>
  <!-- -->
  <div role="tabpanel" class="tab-pane" id="navAssets">
<style type="text/css">
.tblCorpAssets-wrapper { max-height: 300px; overflow: auto; scrollbar-color: #696969 #262727; scrollbar-width: thin; }
.tblCorpAssets-wrapper table { padding:1px; font-size: x-small; width: 100%; }
.tblCorpAssets-wrapper thead th { position: sticky; top: 0; z-index: 1; color: #7f7f7f; background-color: #202020; text-align:center; }
.tblCorpAssets-wrapper thead tr th:nth-child(1),
.tblCorpAssets-wrapper thead tr th:nth-child(2),
.tblCorpAssets-wrapper tbody tr td:nth-child(1),
.tblCorpAssets-wrapper tbody tr td:nth-child(2){ text-align: left; }
.tblCorpAssets-wrapper thead tr th:nth-child(3),
.tblCorpAssets-wrapper thead tr th:nth-child(4),
.tblCorpAssets-wrapper thead tr th:nth-child(5),
.tblCorpAssets-wrapper tbody tr td:nth-child(3),
.tblCorpAssets-wrapper tbody tr td:nth-child(4),
.tblCorpAssets-wrapper tbody tr td:nth-child(5){ text-align: right; }
</style>
    <div class="tblCorpAssets-wrapper">
     <table id="tblCorpAssets" class="table table-condensed table-hover">
      <thead>
       <tr>
        <th>Название</th>
        <th>Хранилище</th>
        <th>Кол-во</th>
        <th>Создан</th>
        <th>Обновлён</th>
       </tr>
      </thead>
      <tbody>
      </tbody>
     </table>
    </div>
   <form id="frmCorpAssets">
    <input type="hidden" name="corp" readonly value="">
    <input type="hidden" name="tid" readonly>
   </form>
  </div>
  <!-- -->
</div> <!--tab-content-->
<!-- -->
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Закрыть</button>
   </div>
  </div>
 </div>
</div>

<script><?php include 'qi_praisal.js'; ?></script>
<?php
__dump_footer();
__dump_copy_to_clipboard_javascript();
?>
