<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


const SORT_PRFT_ASC = 1;
const SORT_PRFT_DESC = -1;
const SORT_PERC_ASC = 2;
const SORT_PERC_DESC = -2;
const T1_ONLY_DEFAULT = 0;
const T2_ONLY_DEFAULT = 0;
const T3_ONLY_DEFAULT = 0;
const AMARR_MARKET_DEFAULT = 0;
const MARKET_VOLUME_DEFAULT = 1;
const PROFIT_BY_SELL_DEFAULT = 1;
const HIDE_UNPROFITABLE_DEFAULT = 1;

$SORT = SORT_PRFT_ASC;
$GRPs = null;
$T1 = T1_ONLY_DEFAULT;
$T2 = T2_ONLY_DEFAULT;
$T3 = T3_ONLY_DEFAULT;
$AMARR_MARKET = AMARR_MARKET_DEFAULT;
$MARKET_VOLUME = MARKET_VOLUME_DEFAULT;
$PROFIT_BY_SELL = PROFIT_BY_SELL_DEFAULT;
$HIDE_UNPROFITABLE = HIDE_UNPROFITABLE_DEFAULT;


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

function get_actual_url($s, $grp, $t1, $t2, $t3, $am, $mv, $pbs, $hu)
{
    $url = strtok($_SERVER[REQUEST_URI], '?').'?s='.$s;
    if ($t1!=T1_ONLY_DEFAULT) $url = $url.'&t1='.($t1?1:0);
    if ($t2!=T2_ONLY_DEFAULT) $url = $url.'&t2='.($t2?1:0);
    if ($t3!=T3_ONLY_DEFAULT) $url = $url.'&t3='.($t3?1:0);
    if (!is_null($grp) && !empty($grp)) $url = $url.'&grp='.implode(',',$grp);
    if ($am!=AMARR_MARKET_DEFAULT) $url = $url.'&am='.($am?1:0);
    if ($mv!=MARKET_VOLUME_DEFAULT) $url = $url.'&mv='.($mv?1:0);
    if ($pbs!=PROFIT_BY_SELL_DEFAULT) $url = $url.'&pbs='.($pbs?1:0);
    if ($hu!=HIDE_UNPROFITABLE_DEFAULT) $url = $url.'&hu='.($hu?1:0);
    return $url;
}

function __dump_industry_group(&$industry_group, $AM, $MV) {
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
            $jita_materials_cost = $product['jsmp'];
            $jita_profit = $product['jprft'];
            $jita_percent = $product['jprct'];
            if ($MV)
            {
                $jita_sell_volume = $product['jsv'];
                $jita_buy_volume = $product['jbv'];
            }
            if ($AM)
            {
                $amarr_sell = $product['as'];
                $amarr_buy = $product['ab'];
                $amarr_materials_cost = $product['asmp'];
                if ($MV)
                {
                    $amarr_sell_volume = $product['asv'];
                    $amarr_buy_volume = $product['abv'];
                }
            }

            if ($first)
            {
                $first = false;
                ?><tr><td class="active" colspan="<?=$AM?(7+($MV?2:0)):(5+($MV?1:0))?>"><strong><?=$market_group?></strong></td></tr><?php
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
        ?><td align="right"<?=($jita_profit<=0)?" style='color: #c60000'":""?>><?=number_format($jita_profit,0,'.',',')?><br><?=$jita_percent?number_format($jita_percent,1,'.',',').'%':""?></td><?php
    }

    if (is_null($jita_materials_cost))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=number_format($jita_materials_cost,0,'.',',')?></td><?php
    }

    if (is_null($jita_sell) && is_null($jita_buy))
    {
        ?><td></td><?php
    }
    else
    {
        ?><td align="right"><?=is_null($jita_sell)?'':number_format($jita_sell,0,'.',',')?><br><?=is_null($jita_buy)?'':number_format($jita_buy,0,'.',',')?></td><?php
    }

    if ($MV)
    {
        if (is_null($jita_sell_volume) && is_null($jita_buy_volume))
        {
            ?><td></td><?php
        }
        else
        {
            ?><td align="right"><?=is_null($jita_sell_volume)?'':number_format($jita_sell_volume,0,'.',',')?><br><?=is_null($jita_buy_volume)?'':number_format($jita_buy_volume,0,'.',',')?></td><?php
        }
    }

    if ($AM)
    {
        if (is_null($amarr_materials_cost))
        {
            ?><td></td><?php
        }
        else
        {
            ?><td align="right"><?=number_format($amarr_materials_cost,0,'.',',')?></td><?php
        }

        if (is_null($amarr_sell) && is_null($amarr_buy))
        {
            ?><td></td><?php
        }
        else
        {
            ?><td align="right"><?=is_null($amarr_sell)?'':number_format($amarr_sell,0,'.',',')?><br><?=is_null($amarr_buy)?'':number_format($amarr_buy,0,'.',',')?></td><?php
        }

        if ($MV)
        {
            if (is_null($amarr_sell_volume) && is_null($amarr_buy_volume))
            {
                ?><td></td><?php
            }
            else
            {
                ?><td align="right"><?=is_null($amarr_sell_volume)?'':number_format($amarr_sell_volume,0,'.',',')?><br><?=is_null($amarr_buy_volume)?'':number_format($amarr_buy_volume,0,'.',',')?></td><?php
            }
        }
    }
?>
</tr>
<?php
        }
}

function __dump_industry_links(&$industry_cost, $SORT, $GRPs, $T1, $T2, $T3, $AM, $MV, $PBS, $HU) {
    ?>Filters: <?php

    $no_filters =
        is_null($GRPs) &&
        ($T1==T1_ONLY_DEFAULT) &&
        ($T2==T2_ONLY_DEFAULT) &&
        ($T3==T3_ONLY_DEFAULT) &&
        ($AM==AMARR_MARKET_DEFAULT) &&
        ($MV==MARKET_VOLUME_DEFAULT);
    if ($no_filters) { ?><b><?php }
    ?><a href="<?=get_actual_url($SORT, null, T1_ONLY_DEFAULT, T2_ONLY_DEFAULT, T3_ONLY_DEFAULT, AMARR_MARKET_DEFAULT, MARKET_VOLUME_DEFAULT, $PBS, 0)?>">ALL</a><?php
    if ($no_filters) { ?></b><?php }

    if ($T1==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T1?0:1, 0, 0, $AM, $MV, $PBS, $HU)?>">T1 only</a><?php
    if ($T1==1) { ?></b><?php }

    if ($T2==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, 0, $T2?0:1, 0, $AM, $MV, $PBS, $HU)?>">T2 only</a><?php
    if ($T2==1) { ?></b><?php }

    if ($T3==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, 0, 0, $T3?0:1, $AM, $MV, $PBS, $HU)?>">T3 only</a><?php
    if ($T3==1) { ?></b><?php }

    ?><br>Settings: <?php

    if ($AM==1) { ?><b><?php }
    ?><a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $AM?0:1, $MV, $PBS, $HU)?>">Amarr market</a><?php
    if ($AM==1) { ?></b><?php }

    if ($MV==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $AM, $MV?0:1, $PBS, $HU)?>">Sell / Buy volume</a><?php
    if ($MV==1) { ?></b><?php }

    if ($PBS==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $AM, $MV, $PBS?0:1, $HU)?>">Calculate sales profit</a><?php
    if ($PBS==1) { ?></b><?php }

    if ($HU==1) { ?><b><?php }
    ?>, <a href="<?=get_actual_url($SORT, $GRPs, $T1, $T2, $T3, $AM, $MV, $PBS, $HU?0:1)?>">Hide unprofitable</a><?php
    if ($HU==1) { ?></b><?php }

    $first = true;
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
                if ($first) { $first = false; ?><br>Categories: <?php } else { ?>, <?php }
                if (!$not_found) { ?><b><?php }
                ?><a href="<?=get_actual_url($SORT, $grp, $T1, $T2, $T3, $AM, $MV, $PBS, $HU)?>"><?=$market_group?></a><?php
                if (!$not_found) { ?></b><?php }
            }
        }
}

function __dump_industry_cost(&$industry_cost, $SORT, $GRPs, $T1, $T2, $T3, $AM, $MV, $PBS, $HU) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th width="100%">Items</th>
  <th style="text-align: right;"><a href="<?=
($SORT==SORT_PRFT_ASC)?
get_actual_url(SORT_PRFT_DESC,$GRPs,$T1,$T2,$T3,$AM,$MV,$PBS,$HU):
get_actual_url(SORT_PRFT_ASC,$GRPs,$T1,$T2,$T3,$AM,$MV,$PBS,$HU)?>">Jita Profit</a><br><a href="<?=
($SORT==SORT_PERC_ASC)?
get_actual_url(SORT_PERC_DESC,$GRPs,$T1,$T2,$T3,$AM,$MV,$PBS,$HU):
get_actual_url(SORT_PERC_ASC,$GRPs,$T1,$T2,$T3,$AM,$MV,$PBS,$HU)?>">Percent</a></th>
  <th style="text-align: right;">Jita Materials<br>Cost</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy</th>
  <?php if ($MV) { ?>
    <th style="text-align: right;">Jita Vol.<br>Sell / Buy</th>
  <?php } ?>
  <?php if ($AM) { ?>
    <th style="text-align: right;">Amarr Materials<br>Cost</th>
    <th style="text-align: right;">Amarr Sell<br>Amarr Buy</th>
    <?php if ($MV) { ?>
      <th style="text-align: right;">Amarr Vol.<br>Sell/Buy</th>
    <?php } ?>
  <?php } ?>
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
                __dump_industry_group($curr_market_group, $AM, $MV);
                $curr_market_group = array();
            }

            if ($T1 == 1 || $T2 == 1 || $T3 == 1)
            {
                $meta = $product['meta'];
                if (is_null($meta)) continue;
                // см. https://everef.net/meta-groups
                $meta_num = intval($meta);
                if ($T1 == 1) { if ($meta_num != 1 && $meta_num != 54) continue; }
                else if ($T2 == 1) { if ($meta_num != 2 && $meta_num != 53) continue; }
                else if ($T3 == 1) { if ($meta_num != 14) continue; }
            }
            if (!is_null($GRPs))
            {
                $market_group_id = intval($product['grp_id']);
                if (array_search($market_group_id, $GRPs) === false) continue;
            }

            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
            $jita_materials_cost = $product['jsmp'];
            $jprft = null;
            $jprct = null;

            if ($PBS == 1)
            {
                if (is_null($jita_materials_cost) || is_null($jita_sell))
                    ;
                else
                {
                    $jprft = $jita_sell - $jita_materials_cost;
                    $jprct = $jita_sell ? (100.0 * (1 - $jita_materials_cost / $jita_sell)) : 0;
                }
            }
            else // if ($PBS == 0)
            {
                if (is_null($jita_materials_cost) || is_null($jita_buy))
                    ;
                else
                {
                    $jprft = $jita_buy - $jita_materials_cost;
                    $jprct = $jita_buy ? (100.0 * (1 - $jita_materials_cost / $jita_buy)) : 0;
                }
            }

            if ($HU && (is_null($jprct) || ($jprct <= 0))) continue;

            $curr_market_group[$pkey] = $product;
            $curr_market_group[$pkey]['jprft'] = $jprft;
            $curr_market_group[$pkey]['jprct'] = $jprct;
        }
    if ($curr_market_group)
    {
        __dump_industry_group($curr_market_group, $AM, $MV);
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

if (!isset($_GET['t1'])) $T1 = T1_ONLY_DEFAULT; else {
  $_get_t1 = htmlentities($_GET['t1']);
  if (is_numeric($_get_t1)) $T1 = get_numeric($_get_t1);
  else $T1 = T1_ONLY_DEFAULT;
}

if (!isset($_GET['t2'])) $T2 = T2_ONLY_DEFAULT; else {
  $_get_t2 = htmlentities($_GET['t2']);
  if (is_numeric($_get_t2)) $T2 = get_numeric($_get_t2);
  else $T2 = T2_ONLY_DEFAULT;
}

if (!isset($_GET['t3'])) $T3 = T3_ONLY_DEFAULT; else {
  $_get_t3 = htmlentities($_GET['t3']);
  if (is_numeric($_get_t3)) $T3 = get_numeric($_get_t3);
  else $T3 = T3_ONLY_DEFAULT;
}

if (!isset($_GET['am'])) $AMARR_MARKET = AMARR_MARKET_DEFAULT; else {
  $_get_am = htmlentities($_GET['am']);
  if (is_numeric($_get_am)) $AMARR_MARKET = get_numeric($_get_am);
  else $AMARR_MARKET = AMARR_MARKET_DEFAULT;
}

if (!isset($_GET['mv'])) $MARKET_VOLUME = MARKET_VOLUME_DEFAULT; else {
  $_get_mv = htmlentities($_GET['mv']);
  if (is_numeric($_get_mv)) $MARKET_VOLUME = get_numeric($_get_mv);
  else $MARKET_VOLUME = MARKET_VOLUME_DEFAULT;
}

if (!isset($_GET['pbs'])) $PROFIT_BY_SELL = PROFIT_BY_SELL_DEFAULT; else {
  $_get_pbs = htmlentities($_GET['pbs']);
  if (is_numeric($_get_pbs)) $PROFIT_BY_SELL = get_numeric($_get_pbs);
  else $PROFIT_BY_SELL = PROFIT_BY_SELL_DEFAULT;
}

if (!isset($_GET['hu'])) $HIDE_UNPROFITABLE = HIDE_UNPROFITABLE_DEFAULT; else {
  $_get_hu = htmlentities($_GET['hu']);
  if (is_numeric($_get_hu)) $HIDE_UNPROFITABLE = get_numeric($_get_hu);
  else $HIDE_UNPROFITABLE = HIDE_UNPROFITABLE_DEFAULT;
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
  tid.sdet_meta_group_id as meta,
  round((cost.jsmp/product.sdebp_quantity)::numeric, 2) as jsmp,
  jita.ethp_sell as js,
  jita.ethp_buy as jb,
  jita.ethp_sell_volume as jsv,
  jita.ethp_buy_volume as jbv
EOD;
  if ($AMARR_MARKET)
  {
    $query .= "\n".<<<EOD
  ,round((cost.asmp/product.sdebp_quantity)::numeric, 2) as asmp
  ,amarr.ethp_sell as as
  ,amarr.ethp_buy as ab
  ,amarr.ethp_sell_volume as asv
  ,amarr.ethp_buy_volume as abv
EOD;
  }
    $query .= "\n".<<<EOD
from
  -- продукты производства
  qi.eve_sde_blueprint_products as product
    -- сведения о чертеже (должен быть published)
    left outer join qi.eve_sde_type_ids product_bp on (product.sdebp_blueprint_type_id = product_bp.sdet_type_id)
    -- цены на продукт производства в жите прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy, ethp_sell_volume, ethp_buy_volume
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60003760
    ) jita on (product.sdebp_product_id = jita.ethp_type_id)
EOD;
  if ($AMARR_MARKET)
  {
    $query .= "\n".<<<EOD
    -- цены на продукт производства в амаррии прямо сейчас
    left outer join (
      select ethp_type_id, ethp_sell, ethp_buy, ethp_sell_volume, ethp_buy_volume
      from qi.esi_trade_hub_prices
      where ethp_location_id = 60008494
    ) amarr on (product.sdebp_product_id = amarr.ethp_type_id)
EOD;
  }
    $query .= "\n,".<<<EOD
  -- сведения о предмете
  qi.eve_sde_type_ids as tid,
  -- сведения о market-группе предмета
  qi.eve_sde_market_groups_semantic as market_group,
  -- расчёт стоимости материалов в постройке продукта
  ( select
      m.sdebm_blueprint_type_id,
      -- m.sdebm_material_id,
      -- m.sdebm_quantity,
      sum(m.sdebm_quantity * jita.ethp_sell) as jsmp -- jita' sell materials price
EOD;
  if ($AMARR_MARKET)
  {
    $query .= "\n".<<<EOD
      ,sum(m.sdebm_quantity * amarr.ethp_sell) as asmp -- amarr' sell materials price
EOD;
  }
    $query .= "\n".<<<EOD
    from
      qi.eve_sde_blueprint_materials m
        -- цены на материалы в жите прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from qi.esi_trade_hub_prices
          where ethp_location_id = 60003760
        ) jita on (m.sdebm_material_id = jita.ethp_type_id)
EOD;
  if ($AMARR_MARKET)
  {
    $query .= "\n".<<<EOD
        -- цены на материалы в амаррии прямо сейчас
        left outer join (
          select ethp_type_id, ethp_sell
          from qi.esi_trade_hub_prices
          where ethp_location_id = 60008494
        ) amarr on (m.sdebm_material_id = amarr.ethp_type_id)
EOD;
  }
    $query .= "\n".<<<EOD
    where
      --m.sdebm_blueprint_type_id=11564 and -- m.sdebm_blueprint_type_id<=11664 and
      m.sdebm_activity in (1,9,11)
    group by m.sdebm_blueprint_type_id
  ) as cost
where
  product.sdebp_blueprint_type_id = cost.sdebm_blueprint_type_id and
  product.sdebp_activity in (1,9,11) and
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
  __dump_industry_links($industry_cost, $SORT, $GRPs, $T1, $T2, $T3, $AMARR_MARKET, $MARKET_VOLUME, $PROFIT_BY_SELL, $HIDE_UNPROFITABLE);
  __dump_industry_cost($industry_cost, $SORT, $GRPs, $T1, $T2, $T3, $AMARR_MARKET, $MARKET_VOLUME, $PROFIT_BY_SELL, $HIDE_UNPROFITABLE);
?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
