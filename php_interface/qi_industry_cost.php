<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


const SORT_PRFT_ASC = 1;
const SORT_PRFT_DESC = -1;
const SORT_PERC_ASC = 2;
const SORT_PERC_DESC = -2;
$SORT = SORT_PRFT_ASC;
$GRPs = null;
$T2 = 0;


function cmp($a, $b)
{
    global $SORT;
    switch ($SORT)
    {
    default:
    case SORT_PRFT_ASC:  return $a['jprft'] < $b['jprft'];
    case SORT_PRFT_DESC: return $a['jprft'] > $b['jprft'];
    case SORT_PERC_ASC:  return $a['jprct'] < $b['jprct'];
    case SORT_PERC_DESC: return $a['jprct'] > $b['jprct'];
    }
}

function get_actual_url($s, $grp, $t2)
{
    $url = strtok($_SERVER[REQUEST_URI], '?').'?s='.$s;
    if ($t2==1) $url = $url.'&t2=1';
    if (!is_null($grp) && !empty($grp)) $url = $url.'&grp='.implode(',',$grp);
    return $url;
}

function __dump_industry_group(&$industry_group) {
    usort($industry_group, "cmp");

    $first = true;
    if ($industry_group)
        foreach ($industry_group as &$product)
        {
            $tid = $product['id'];
            $blueprint_tid = $product['bp_id'];
            $market_group = $product['grp'];
            $nm = $product['name'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $amarr_sell = $product['as'];
            $amarr_buy = $product['ab'];
            $jita_materials_cost = $product['jsmp'];
            $amarr_materials_cost = $product['asmp'];
            $jita_profit = $product['jprft'];
            $jita_percent = $product['jprct'];

            if ($first)
            {
                $first = false;
                ?><tr><td class="active" colspan="7"><strong><?=$market_group?></strong></td></tr><?php
            }
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm?><?=get_clipboard_copy_button($nm)?><br><span class="text-muted"><?=$tid?> / <?=$blueprint_tid?></span></td>
<?php
    if (is_null($jita_profit) || is_null($jita_percent))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"<?=($jita_profit<=0)?" style='color: #c60000'":""?>><?=number_format($jita_profit,2,'.',',')?><br><?=$jita_percent?number_format($jita_percent,1,'.',',').'%':""?></td><?php
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
}

function __dump_industry_links(&$industry_cost, $SORT, $GRPs, $T2) {
    if (is_null($GRPs) && ($T2==0)) { ?><b><?php }
    ?><a href="<?=get_actual_url($SORT, null, 0)?>">ALL</a><?php
    if (is_null($GRPs) && ($T2==0)) { ?></b><?php }

    if ($T2==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T2?0:1)?>">T2 only</a><?php
    if ($T2==1) { ?></b><?php }

    $prev_market_group = null;
    if ($industry_cost)
        foreach ($industry_cost as $pkey => &$product)
        {
            $market_group = $product['grp'];
            if ($prev_market_group != $market_group)
            {
                $prev_market_group = $market_group;
                $market_group_id = intval($product['grp_id']);
                $grp = is_null($GRPs) ? array() : $GRPs;
                $key = array_search($market_group_id, $grp);
                $not_found = $key === false;
                if ($not_found) array_push($grp, $market_group_id); else unset($grp[$key]);
                if (!$not_found) { ?><b><?php }
                ?>, <a href="<?=get_actual_url($SORT, $grp, $T2)?>"><?=$market_group?></a><?php
                if (!$not_found) { ?></b><?php }
            }
        }
}

function __dump_industry_cost(&$industry_cost, $SORT, $GRPs, $T2) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th width="100%">Items</th>
  <th style="text-align: right;"><a href="<?=($SORT==SORT_PRFT_ASC)?get_actual_url(SORT_PRFT_DESC,$GRPs,$T2):get_actual_url(SORT_PRFT_ASC,$GRPs,$T2)?>">Jita Profit</a><br><a href="<?=($SORT==SORT_PERC_ASC)?get_actual_url(SORT_PERC_DESC,$GRPs,$T2):get_actual_url(SORT_PERC_ASC,$GRPs,$T2)?>"">Percent</a></th>
  <th style="text-align: right;">Jita Materials<br>Cost</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy</th>
  <th style="text-align: right;">Amarr Materials<br>Cost</th>
  <th style="text-align: right;">Amarr Sell<br>Amarr Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $prev_market_group = null;
    $curr_market_group = array();
    if ($industry_cost)
        foreach ($industry_cost as $pkey => &$product)
        {
            $market_group = $product['grp'];
            if ($prev_market_group != $market_group)
            {
                $prev_market_group = $market_group;
                __dump_industry_group($curr_market_group);
                $curr_market_group = array();
            }

            if ($T2 == 1)
            {
                $tech = $product['tech'];
                if (is_null($tech)) continue;
                if (intval($tech) != 2) continue;
            }
            if (!is_null($GRPs))
            {
                $market_group_id = intval($product['grp_id']);
                if (array_search($market_group_id, $GRPs) === false) continue;
            }

            $curr_market_group[$pkey] = $product;
            $jita_sell = $product['js'];
            $jita_materials_cost = $product['jsmp'];
            if (is_null($jita_materials_cost) || is_null($jita_sell))
            {
                $curr_market_group[$pkey]['jprft'] = null;
                $curr_market_group[$pkey]['jprct'] = null;
            }
            else
            {
                $curr_market_group[$pkey]['jprft'] = $jita_sell - $jita_materials_cost;
                $curr_market_group[$pkey]['jprct'] = $jita_sell ? (100.0 * (1 - $jita_materials_cost / $jita_sell)) : 0;
            }
        }
?>
</tbody>
</table>
<?php
}



if (!isset($_GET['grp'])) $GRPs = null; else {
  $_get_grp = htmlentities($_GET['grp']);
  if (is_numeric($_get_grp)) $GRPs = array(get_numeric($_get_grp));
  else if (is_numeric_array($_get_grp)) $GRPs = get_numeric_array($_get_grp);
  else return;
}

if (!isset($_GET['s'])) $SORT = SORT_PRFT_ASC; else {
  $_get_sort = htmlentities($_GET['s']);
  if (is_numeric($_get_sort)) $SORT = get_numeric($_get_sort);
  else $SORT = SORT_PRFT_ASC;
}

if (!isset($_GET['t2'])) $T2 = 0; else {
  $_get_t2 = htmlentities($_GET['t2']);
  if (is_numeric($_get_t2)) $T2 = get_numeric($_get_t2);
  else $T2 = 0;
}


    __dump_header("Industry Cost", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  product.sdebp_product_id as id,
  cost.sdebm_blueprint_type_id as bp_id,
  market_group.semantic_id as grp_id,
  market_group.name as grp,
  tid.sdet_type_name as name,
  tid.sdet_tech_level as tech,
  round((cost.jsmp/product.sdebp_quantity)::numeric, 2) as jsmp,
  round((cost.asmp/product.sdebp_quantity)::numeric, 2) as asmp,
  jita.ethp_sell as js,
  jita.ethp_buy as jb,
  amarr.ethp_sell as as,
  amarr.ethp_buy as ab
from
  -- продукты производства
  qi.eve_sde_blueprint_products as product
    -- сведения о чертеже (должен быть published)
    left outer join qi.eve_sde_type_ids product_bp on (product.sdebp_blueprint_type_id = product_bp.sdet_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (product.sdebp_product_id = jita.ethp_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy
      from qi.esi_trade_hub_prices
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
          from qi.esi_trade_hub_prices
          where ethp_location_id = 60003760
        ) jita on (m.sdebm_material_id = jita.ethp_type_id)
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from qi.esi_trade_hub_prices
          where ethp_location_id = 60008494
        ) amarr on (m.sdebm_material_id = amarr.ethp_type_id)
    where
      --m.sdebm_blueprint_type_id=42883 and
      m.sdebm_activity = 1
    group by m.sdebm_blueprint_type_id
  ) as cost
where
  product.sdebp_blueprint_type_id = cost.sdebm_blueprint_type_id and
  product.sdebp_activity = 1 and
  product_bp.sdet_published and 
  tid.sdet_type_id = product.sdebp_product_id and
  tid.sdet_published and
  market_group.id = tid.sdet_market_group_id
order by market_group.name, tid.sdet_type_name;
EOD;
    $industry_cost_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $industry_cost = pg_fetch_all($industry_cost_cursor);
    //---
    pg_close($conn);
?>

<div class="container-fluid">
<?php
  __dump_industry_links($industry_cost, $SORT, $GRPs, $T2);
  __dump_industry_cost($industry_cost, $SORT, $GRPs, $T2);
?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
