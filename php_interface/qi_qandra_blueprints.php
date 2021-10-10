<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


function __dump_blueprints_tree(&$blueprints) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th colspan="5" width="66%">Blueprints</th>
  <!--<th style="text-align: right;">Base Price</th>-->
 </tr>
 <tr>
  <th colspan="2"></th>
  <th>ID</th>
  <th>ME</th>
  <th>TE</th>
  <th>Location</th>
  <th>Quantity</th>
  <!--<th></th>-->
 </tr>
</thead>
<tbody>
<?php
    $prev_market_group = null;
    $market_group_names = array(null, null, null, null, null, null, null, null, null, null);
    $prev_blueprint_name = null;
    if ($blueprints)
        foreach ($blueprints as &$bpo)
        {
            // market group info
            $market_group_depth = $bpo['mgd'];
            if ($market_group_depth == 1) continue; // уровень c `Blueprints & Reactions` пропускаем
            $market_group_name = $bpo['mgn'];
            $market_group_id = $bpo['mgi'];
            // blueprint info
            $blueprint_type_id = $bpo['bid'];
            $blueprint_name = $bpo['bnm'];
            //$blueprint_base_price = $bpo['bp'];
            // product info
            $product_type_id = $bpo['pid'];
            $product_name = $bpo['pnm'];
            $product_quantity = $bpo['pq'];
            $product_meta = $bpo['meta'];
            // qandra si info
            $bpo_unique_id = $bpo['uid'];
            $bpo_location_id = $bpo['lid'];
            $bpo_me = $bpo['me'];
            $bpo_te = $bpo['te'];
            $bpo_quantity = $bpo['bq'];
            $bpo_storage = $bpo['st'];

            if ($prev_market_group != $market_group_name)
            {
                $prev_market_group = $market_group_name;
                $market_group_names[$market_group_depth-2] = $market_group_name;
                ?><tr><td class="active" colspan="9"><strong><?=str_pad('', ($market_group_depth-2)*7, '&nbsp; ', STR_PAD_LEFT)?><?php
                if ($market_group_depth > 2)
                {
                    ?><span class="text-muted"><?php
                    for ($i = 0, $cnt = $market_group_depth - 2; $i < $cnt; ++$i)
                    {
                        ?><?=$market_group_names[$i]?> &raquo; <?php
                    }
                    ?></span><?php
                }
                ?><?=$market_group_name?> <span class="text-muted">(<?=$market_group_id?>)</span></strong></td></tr><?php
            }

            // если в этом разделе нет чертежей (это корневая группа), то пропуск вывода подробностей
            if (is_null($blueprint_type_id)) continue;
            // выводим информацию только по meta=1
            if ($product_meta == 2) continue;

            if ($prev_blueprint_name != $blueprint_name)
            {
            ?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($product_type_id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?php
    if ($product_quantity > 1)
    {
        ?><strong><?=$product_quantity?>x</strong> <?php
    }
    ?><?=$product_name?><br><span class="text-muted"><?=$product_type_id?></span><?php
    if ($product_meta != 1)
    {
        ?> <span class="label label-warning">meta<?=$product_meta?></span><?php
    }
?></td>
 <td colspan="5">
  <?=$blueprint_name.get_clipboard_copy_button($blueprint_name).'<br><span class="text-muted">'.$blueprint_type_id.'</span>'.get_clipboard_copy_button($blueprint_type_id)?>
  <?php
    if (is_null($bpo_unique_id))
    {
        ?><span class="label label-danger">absent</span><?php
    }
  ?>
 </td>
 <?php /* <td align="right"><?=number_format($blueprint_base_price,0,'.',',')?></td> */ ?>
</tr>
            <?php
            }

            // если нет закупленных чертежей этого типа, то пропускаем вывод подробностей
            if (is_null($bpo_unique_id)) continue;

            ?>
<tr>
 <td colspan="2"></td>
 <td><?=$bpo_unique_id?><?php
    $warning = '';
    if ($bpo_storage == 1)
        $warning = ' <span class="label label-primary">manufacturing</span>';
    else if ($bpo_storage == 3)
        $warning = ' <span class="label label-info">te</span>';  # Science
    else if ($bpo_storage == 4)
        $warning = ' <span class="label label-info">me</span>';  # Science
    else if ($bpo_storage == 5)
        $warning = ' <span class="label label-info">copying</span>';  # Science
    else if ($bpo_storage == 7)
        $warning = ' <span class="label label-info">reverse</span>';  # Science
    else if ($bpo_storage == 8)
        $warning = ' <span class="label label-info">invention</span>';  # Science
    else if (($bpo_storage == 9) || ($bpo_storage == 11))
        $warning = ' <span class="label label-success">reaction</span>';  # Reaction
    if ($warning)
        print($warning);
 ?></td>
 <td><?=$bpo_me?></td>
 <td><?=$bpo_te?></td>
 <td><?=($bpo_location_id==1037211996610)?'Qandra Si BPC':($bpo_location_id==1037368057421?'Qandra Si BPC (10-20)':'???')?></td>
 <td><?=($bpo_quantity==-1)?1:$bpo_quantity?><?=($bpo_quantity>1)?' <span class="label label-danger">stack</span>':''?></td>
 <td></td>
</tr>
            <?php
        }
?>
</tbody>
</table>
<?php
}



    __dump_header("Qandra Si' Blueprints", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
  -- rpad('          ',(rrr.depth-1)*2)||rrr.name as tree, -- market group name 
  rrr.depth as mgd, -- tree depth
  rrr.name as mgn, -- market group name
  rrr.id as mgi, -- market group id
  t.id as bid, -- blueprint type id
  t.name as bnm, -- blueprint name
  -- t.base_price as bp, -- base price
  p.product_id as pid, -- product type id
  p.nm as pnm, -- product name
  p.q as pq, -- product quantity
  p.meta as meta, -- product meta group id
  q.id as uid, -- blueprint unique id
  q.location_id as lid, -- blueprint location id
  q.me as me,
  q.te as te,
  q.quantity as bq, -- qandra' blueprint quantity
  q.storage as st -- qandra si' blueprint storage
from (
  select
    rr.*,
    row_number() OVER () as rnum
  from (
    with recursive r as (
      select
        sdeg_group_id as id,
        sdeg_parent_id as parent,
        sdeg_group_name as name,
        1 as depth,
        sdeg_group_name::varchar(255) as sort_str
      from qi.eve_sde_market_groups
      where sdeg_parent_id is null and sdeg_group_id = 2
      union all
      select
        branch.sdeg_group_id,
        branch.sdeg_parent_id,
        branch.sdeg_group_name,
        r.depth+1,
        (r.sort_str || '|' || branch.sdeg_group_name)::varchar(255)
      from qi.eve_sde_market_groups as branch
        join r on branch.sdeg_parent_id = r.id
      where branch.sdeg_group_id not in (
       1338 -- Structures
       ,2157 -- Structure Modifications
       ,2158 -- Structure Equipment
       ,878 -- Titans
       ,2262 -- Force Auxiliaries
       ,883 -- Exhumers
       ,782 -- Dreadnoughts
       ,419 -- Covert Ops
       ,881 -- Command Ships
       ,879 -- Carriers
       ,207 -- Battleships
       ,588 -- Battlecruisers
       ,458 -- Assault Frigates
       ,1045 -- Capital Industrial Ships
       ,634 -- Transport Ships
       ,882 -- Recon Ships
       ,442 -- Logistics
       ,880 -- Interdictors
       ,408 -- Interceptors,
       ,1719 -- Capital Armor Rigs
       ,1720 -- Capital Astronautic Rigs
       ,1721 -- Capital Drone Rigs
       ,1723 -- Capital Electronics Superiority Rigs
       ,1725 -- Capital Energy Weapon Rigs
       ,1724 -- Capital Engineering Rigs
       ,1726 -- Capital Hybrid Weapon Rigs
       ,1727 -- Capital Missile Launcher Rigs
       ,1728 -- Capital Projectile Weapon Rigs
       ,1797 -- Capital Resource Processing Rigs
       ,1804 -- Capital Scanning Rigs
       ,1729 -- Capital Shield Rigs
       ,1808 -- Capital Targeting Rigs
       ,913 -- Superweapons
       ,599,598,597,794,792,793 -- Extra Large
       ,1602,1601,1603 -- Orbital Strike
       ,2191 -- Structure Anticapital Missiles
       ,2192 -- Structure Antisubcapital Missiles
       ,1286 -- XL Cruise Missiles
       ,617 -- XL Torpedoes
       ,1016 -- Bombs
       ,2193 -- Structure Guided Bombs
       ,2237 -- Fighters
       ,1041 -- Manufacture & Research
       ,1849 -- Reaction Formulas
       ,2248 -- Burst Projectors
      )
    )
    select r.id, r.parent, r.name, r.depth from r
    --select r.* from r
    order by r.sort_str
  ) rr
) rrr
  -- чертежи, которые запланированы к покупке
  left outer join (
    select
      sdet_type_id as id,
      sdet_type_name as name,
      sdet_base_price as base_price,
      sdet_market_group_id as market_group
    from qi.eve_sde_type_ids
    where
      sdet_published and
      sdet_type_name not like 'Capital %' and
      sdet_type_name not like '% XL %' and
      sdet_type_id not in (
       48745,49973,58973,58974,58975,27015,10040,52245,49971,48095,55763,1218 -- can't buy
       ,49100 -- rare
       ,40743,40741,40742,40755,40757 -- Heavy (non std Warp Disruptor)
       ,41243,41244,41257,41256,41258,41313 -- huge non std propulsion
       ,23736,23954,28647,28653,56734 -- some of fleet assistance
       ,41609,41607,41608 -- huge steel plates
       ,27952,20281,28584 -- huge weapon upgrades
      )
  ) as t on (t.market_group = rrr.id)
  -- продукты производства по этим чертежам
  left outer join (
     select
      sdebp_blueprint_type_id as id,
      sdebp_product_id as product_id,
      sdebp_quantity as q,
      sdet_type_name as nm,
      sdet_meta_group_id as meta
    from qi.eve_sde_blueprint_products, qi.eve_sde_type_ids
    where sdet_type_id = sdebp_product_id and sdebp_activity = 1
  ) as p on (t.id = p.id)
  -- чертежи, которые закуплены
  left outer join (
    select
      b.ecb_item_id as id,
      b.ecb_type_id as type_id,
      b.ecb_location_id as location_id,
      b.ecb_material_efficiency as me,
      b.ecb_time_efficiency as te,
      b.ecb_quantity as quantity,
      -1 as storage
    from qi.esi_corporation_blueprints b
    where
      b.ecb_corporation_id = 98615601 and
      b.ecb_location_id in (1037211996610, 1037368057421) and
      b.ecb_quantity <> -2
    union
    select
      j.ecj_blueprint_id,
      j.ecj_blueprint_type_id,
      j.ecj_blueprint_location_id,
      null,
      null,
      1,
      j.ecj_activity_id
    from
      qi.esi_corporation_industry_jobs j
    where
      j.ecj_corporation_id = 98615601 and
      ( j.ecj_output_location_id in (1037211996610, 1037368057421) or
        j.ecj_blueprint_location_id in (1037211996610, 1037368057421)
      ) and
      -- j.ecj_activity_id in (3,4) and
      j.ecj_status = 'active'
  ) as q on (t.id = q.type_id)
order by rrr.rnum;
EOD;
    $blueprints_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $blueprints = pg_fetch_all($blueprints_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>Qandra Si' Blueprints</h2>
<?php __dump_blueprints_tree($blueprints); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
