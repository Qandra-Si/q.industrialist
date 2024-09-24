<?php
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

function __dump_market_orders_data(&$conn, &$market_hubs, &$type_ids, &$sale_orders) {
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $query = <<<EOD
select
 --sell_orders.corp_id,
 coalesce(sell_orders.type_id,hub_market.type_id) as id, -- type_id
 coalesce(sell_orders.hub_id,hub_market.hub_id) as hub, -- hub id
 sell_orders.volume_remain as ov, -- our_volume
 round(sell_orders.price_total::numeric, 2) as pt, -- price_total
 sell_orders.price_min as op, -- our_price
 sell_orders.price_max as pm, -- price_max
 coalesce(sell_orders.orders_total,0) as ot, -- orders_total
 hub_market.total_volume as tv, -- their_volume
 hub_market.min_price as tp, -- their_price
 their_best_offer.remain as bo -- their best offer (remain)
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
  full join (
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

  /*не используется:
  echo 'g_sale_orders=[';
  if ($sale_orders)
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
              ($our_volume ?? 'null').','. //2
              ($price_total ?? 'null').','. //3
              ($our_price ?? 'null').','. //4
              ($price_max ?? 'null').','. //5
              $orders_total.','. //6
              ($their_volume ?? 'null').','. //7
              ($their_price ?? 'null').','. //8
              ($best_offer_volume ?? 'null'). //9
           "],\n";
    }
  echo "null];\n";
  */
}

function __dump_market_orders_remain(&$conn, &$market_hubs, &$sale_remain) {
  $active_market_hub_ids = array();
  $active_trader_corp_ids = array();
  get_active_market_hub_ids($market_hubs, $active_market_hub_ids, $active_trader_corp_ids);

  $query = <<<EOD
select
 ecor_type_id as id, -- type_id
 ecor_location_id as hub, -- hub id
 sum(ecor_volume_remain) as r -- remain sum
from esi_corporation_orders
where
 not ecor_is_buy_order and
 not ecor_history and
 ecor_corporation_id=any($1) and
 ecor_location_id=any($2)
group by ecor_type_id, ecor_location_id;
EOD;
  $params = array('{'.implode(',',$active_trader_corp_ids).'}','{'.implode(',',$active_market_hub_ids).'}');
  $sale_remain_cursor = pg_query_params($conn, $query, $params)
          or die('pg_query err: '.pg_last_error());
  $sale_remain = pg_fetch_all($sale_remain_cursor);
}

function get_main_data_tkey(&$main_data, $id)
{
  $t_key = null;
  foreach ($main_data as $tk => $t)
  {
    $_id = intval($t['sdet_type_id']);
    if ($_id!=$id) continue;
    $t_key = $tk;
    break;
  }
  return $t_key;
}

function __dump_products_and_orders_dialog(&$market_hubs) { ?>
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
  <li role="presentation"><a href="#navIndustry" aria-controls="navIndustry" role="tab" data-toggle="tab">Производство</a></li>
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
    <!-- -->
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
  <div role="tabpanel" class="tab-pane" id="navIndustry">
    <!-- -->
    <center>
      <nav aria-label="Market Hubs" id="dtlsSelTransferHub">
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
    <!-- -->
    <form id="frmIndustryProduct">
     <input type="hidden" name="corp" readonly value="">
     <input type="hidden" name="hub" readonly value="">
     <input type="hidden" name="tid" readonly>
    </form>
    <div id="dtlsIndustryProduct-wrapper" style="font-size: 90%;">
    </div>
  </div>
  <!-- -->
  <div role="tabpanel" class="tab-pane" id="navAssets">
<style type="text/css">
.tblCorpAssets-wrapper { max-height: 300px; overflow: auto; scrollbar-color: #696969 #262727; scrollbar-width: thin; }
.tblCorpAssets-wrapper table { padding:1px; font-size: x-small; width: 100%; }
.tblCorpAssets-wrapper thead th { position: sticky; top: 0; z-index: 1; color: #e4e4e4; background-color: #242427; }
.tblCorpAssets-wrapper thead tr th:nth-child(1),
.tblCorpAssets-wrapper thead tr th:nth-child(2),
.tblCorpAssets-wrapper tbody tr td:nth-child(1),
.tblCorpAssets-wrapper tbody tr td:nth-child(2){ text-align: left; }
.tblCorpAssets-wrapper thead tr th:nth-child(3),
.tblCorpAssets-wrapper tbody tr td:nth-child(3),
.tblCorpAssets-wrapper tbody tr td:nth-child(4),
.tblCorpAssets-wrapper tbody tr td:nth-child(5){ text-align: right; white-space: nowrap; width: min-content; }
.tblCorpAssets-wrapper thead tr th:nth-child(4),
.tblCorpAssets-wrapper thead tr th:nth-child(5){ text-align: center; width: min-content; }
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
<?php }

?>
