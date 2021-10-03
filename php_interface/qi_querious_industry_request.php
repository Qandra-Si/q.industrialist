<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';
?>

<?php function __dump_industry_cost(&$industry_cost) { ?>
<style>
.label-t1 { color: #fff; background-color: #777; }
.label-t2 { color: #fff; background-color: #ceb056; }
.label-noordersreal { color: #fff; background-color: #d9534f; }
.label-noorders { color: #fff; background-color: #eebbb9; }
.label-veryfew { color: #fff; background-color: #337ab7; }
.text-muted-much { color: #bbb; }
</style>
<table class="table table-condensed" style="padding:1px;font-size:smaller;" id="tblIndustry">
<thead>
 <tr>
  <th></th>
  <th width="100%">Items</th>
  <th style="text-align: right;">Weekly<br>Quantity</th>
  <th style="text-align: right;">RI4 Price<br>Quantity</th>
  <th style="text-align: right;">Jita Materials<br>Cost</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy</th>
  <th style="text-align: right;">Amarr Materials<br>Cost</th>
  <th style="text-align: right;">Amarr Sell<br>Amarr Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $prev_market_group = null;
    if ($industry_cost)
        foreach ($industry_cost as &$product)
        {
            $problems = '';
            $warnings = '';

            $tid = $product['id'];
            $blueprint_tid = $product['bp_id'];
            $market_group = $product['grp'];
            $nm = $product['name'];
            $meta = $product['meta'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $amarr_buy = $product['ab'];
            $jita_materials_cost = $product['jsmp'];
            $amarr_materials_cost = $product['asmp'];
            $weekly_volume = $product['wv'];
            $ri4_market_quantity = $product['mv'];
            $ri4_price = $product['mp'];

            if ($meta == 1)
                $warnings .= '&nbsp;<span class="label label-t1">T1</span>';
            else if ($meta == 2)
                $warnings .= '&nbsp;<span class="label label-t2">T2</span>';

            $too_few = (($ri4_market_quantity+0) <= ($weekly_volume+0)) ? 1 : 0;
            if (is_null($ri4_market_quantity) || ($ri4_market_quantity == 0))
                $problems .= '&nbsp;<span class="label label-noordersreal">no orders</span>';
            else if ($too_few)
                $problems .= '&nbsp;<span class="label label-veryfew">very few</span>';

            if ($prev_market_group != $market_group)
            {
                $prev_market_group = $market_group;
                ?><tr><td class="active" colspan="8"><strong><?=$market_group?></strong></td></tr><?php
            }
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><br><span class="text-muted"><?=$tid?> / <?=$blueprint_tid.$problems.$warnings?></span></td>
<?php
    if (is_null($weekly_volume))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><br><?=number_format($weekly_volume,1,'.',',')?></td><?php
    }

    if (is_null($ri4_price))
    {
        ?><td bgcolor="#e8c8c8"></td><?php
    }
    else
    {
        ?><td align="right"<?=$too_few?(' bgcolor="#e8c8c8"'):''?>><?=number_format($ri4_price,2,'.',',')?><br><?=number_format($ri4_market_quantity,0,'.',',')?></td><?php
    }

    if (is_null($jita_materials_cost))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($jita_materials_cost,2,'.',',')?></td><?php
    }

    if (is_null($jita_sell))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($jita_sell,2,'.',',')?><br><?=number_format($jita_buy,2,'.',',')?></td><?php
    }

    if (is_null($amarr_materials_cost))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($amarr_materials_cost,2,'.',',')?></td><?php
    }

    if (is_null($amarr_sell))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($amarr_sell,2,'.',',')?><br><?=number_format($amarr_buy,2,'.',',')?></td><?php
    }
?>
</tr>
<?php
        }
?>
</tbody>
</table>
<?php
}



    __dump_header("Querious Industry Request", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  product.sdebp_product_id as id,
  cost.sdebm_blueprint_type_id as bp_id,
  market_group.name as grp,
  tid.sdet_type_name as name,
  tid.sdet_meta_group_id as meta,
  round((cost.jsmp/product.sdebp_quantity)::numeric, 2) as jsmp,
  round((cost.asmp/product.sdebp_quantity)::numeric, 2) as asmp,
  jita.ethp_sell as js,
  jita.ethp_buy as jb,
  amarr.ethp_sell as as,
  amarr.ethp_buy as ab,
  case
    when (weeks_passed.volume_sell=0) or (weeks_passed.diff<0.14) then null
    when (weeks_passed.diff < 1.14) then weeks_passed.volume_sell
    else round(weeks_passed.volume_sell/weeks_passed.diff,1)
  end as wv, -- weekly volume
  round(orders_stat.ri4_price::numeric, 2) as mp, -- RI4 price
  orders_stat.volume_remain as mv -- RI4 volume
from
  -- продукты производства
  qi.eve_sde_blueprint_products as product
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (product.sdebp_product_id = jita.ethp_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (product.sdebp_product_id = amarr.ethp_type_id),
  -- сведения о предмете
  qi.eve_sde_type_ids as tid,
  -- сведения о market-группе предмета
  qi.eve_sde_market_groups_semantic as market_group,
  -- расчёт стоимости материалов в постройке продукта
  ( select
      m.sdebm_blueprint_type_id,
      -- m.sdebm_material_id,
      -- m.sdebm_quantity,
      sum(m.sdebm_quantity * jita.ethp_sell) as jsmp, -- jita' sell materials price
      sum(m.sdebm_quantity * amarr.ethp_sell) as asmp -- amarr' sell materials price
    from
      qi.eve_sde_blueprint_materials m
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from esi_trade_hub_prices
          where ethp_location_id = 60003760
        ) jita on (m.sdebm_material_id = jita.ethp_type_id)
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from esi_trade_hub_prices
          where ethp_location_id = 60008494
        ) amarr on (m.sdebm_material_id = amarr.ethp_type_id)
    where
      --m.sdebm_blueprint_type_id=42883 and
      m.sdebm_activity = 1
    group by m.sdebm_blueprint_type_id
  ) as cost,
  -- предметы, выставленные на продажу
  ( select distinct type_id
    from (
      -- список транзакций по покупке/продаже избранными персонажами от имени 2х корпораций
      select ecwt_type_id as type_id --, 'j'::char as type
      from
        esi_corporation_wallet_journals j
          left outer join esi_corporation_wallet_transactions t on (ecwj_context_id = ecwt_transaction_id) -- (j.ecwj_reference_id = t.ecwt_journal_ref_id)
      where
        (ecwj_date > '2021-08-15') and
        (ecwj_context_id_type = 'market_transaction_id') and
        ( ( ecwj_corporation_id in (98615601) and -- R Initiative 4
            ecwj_second_party_id in (2116129465,2116746261,2116156168,2119173458) and -- Qandra Si, Kekuit Void, Qunibbra Do, Zenorti Void
            ( ecwt_location_id in (1036927076065,1034323745897) and not ecwt_is_buy or -- станка рынка
              ecwt_location_id not in (1036927076065,1034323745897) and ecwt_is_buy
            ) and
            ecwj_division = 1) or
          ( ecwj_corporation_id in (98553333) and -- R Strike
            ecwj_second_party_id in (95858524) and -- Xatul' Madan
            ecwt_is_buy and
            ecwj_division = 7)
        )
      union
      -- список того, что корпорация продавала или продаёт
      select ecor_type_id --, 'o'::char
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id in (1036927076065,1034323745897)) -- станка рынка
      ) jto
  ) querious
    -- сведения о длительности sell-ордеров и о кол-ве проданного на станке рынка
    left outer join (
      select
        ecor_type_id,
        (current_date - min(ecor_issued::date))/7.0 as diff,
        sum(ecor_volume_total - ecor_volume_remain) as volume_sell
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id in (1036927076065,1034323745897))  -- станка рынка
      group by ecor_type_id
    ) weeks_passed on (querious.type_id = weeks_passed.ecor_type_id)
    -- сведения о sell-ордерах, активных прямо сейчас
    left outer join (
      select
        ecor_type_id,
        sum(ecor_volume_remain) as volume_remain,
        min(ecor_price) as ri4_price
      from esi_corporation_orders
      where
        not ecor_is_buy_order and
        (ecor_volume_remain > 0) and
        not ecor_history and
        (ecor_corporation_id=98615601) and  -- R Initiative 4
        (ecor_location_id in (1036927076065,1034323745897))  -- станка рынка
      group by 1
    ) orders_stat on (querious.type_id = orders_stat.ecor_type_id)
where
  querious.type_id = product.sdebp_product_id and
  product.sdebp_blueprint_type_id = cost.sdebm_blueprint_type_id and
  product.sdebp_activity = 1 and
  tid.sdet_type_id = product.sdebp_product_id and
  market_group.id = tid.sdet_market_group_id and
  market_group.semantic_id not in (
    19, -- Trade Goods
    499, -- Advanced Moon Materials
    500, -- Processed Moon Materials
    501, -- Raw Moon Materials
    1031, -- Raw Materials
    1035, -- Components
    1332, -- Planetary Materials
    1857, -- Minerals
    1858, -- Booster Materials
    1860, -- Polymer Materials
    1861, -- Salvage Materials
    1872, -- Research Equipment
    2767 -- Molecular-Forged Materials
  )
order by market_group.name, tid.sdet_type_name;
EOD;
    $industry_cost_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $industry_cost = pg_fetch_all($industry_cost_cursor);
    //---
    pg_close($conn);
?>

<div class="container-fluid">
<div class="btn-group btn-group-toggle" data-toggle="buttons">
 <label class="btn btn-default qind-btn-industry active" group="all"><input type="radio" name="options" autocomplete="off" checked>Все</label>
 <label class="btn btn-default qind-btn-industry" group="meta-t1"><input type="radio" name="options" autocomplete="off">T1</label>
 <label class="btn btn-default qind-btn-industry" group="meta-t2"><input type="radio" name="options" autocomplete="off">T2</label>
 <label class="btn btn-default qind-btn-industry" group="sold"><input type="radio" name="options" autocomplete="off">Всё продано</label>
 <label class="btn btn-default qind-btn-industry" group="very-few"><input type="radio" name="options" autocomplete="off">Товар заканчивается</label>
</div>
<?php __dump_industry_cost($industry_cost); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<script>
  function rebuildIndustry(show_group) {
    $('#tblIndustry').find('tbody').find('tr').each(function() {
      var tr = $(this);
      var show = false;
      if (show_group == 'all')
        show = true;
      else if (show_group == 'meta-t1')
        show = tr.find('td').eq(1).find('span.label-t1').length;
      else if (show_group == 'meta-t2')
        show = tr.find('td').eq(1).find('span.label-t2').length;
      else if (show_group == 'sold')
        show = tr.find('td').eq(1).find('span.label-noordersreal').length;
      else if (show_group == 'very-few')
        show = tr.find('td').eq(1).find('span.label-veryfew').length;
      if (show)
        tr.removeClass('hidden');
      else if (tr.find('td').eq(0).hasClass('active'))
        tr.removeClass('hidden');
      else
        tr.addClass('hidden');
    });
  }
  $(document).ready(function(){
    $('label.qind-btn-industry').on('click', function () {
      if (!$(this).hasClass('active')) // включается
        rebuildIndustry($(this).attr('group'));
    });
  });
</script>
<?php __dump_copy_to_clipboard_javascript() ?>
