<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';


function __dump_blueprints_tree(&$blueprints) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th colspan="4">Blueprints</th>
  <th colspan="3" width="50%">Materials</th>
 </tr>
 <tr>
  <th colspan="2"></th>
  <th>Quantity</th>
  <th>Runs</th>
  <th>ME</th>
  <th colspan="2"></th>
  <th>Calculated</th>
 </tr>
</thead>
<tbody>
<?php
    $prev_group = null;
    $prev_blueprint_name = null;
    $prev_blueprint_qty = null;
    $prev_blueprint_runs = null;
    $prev_blueprint_me = null;
    if ($blueprints)
        foreach ($blueprints as &$bpc)
        {
            // group info
            $group_name = $bpc['grp_name'];
            $group_id = $bpc['grp_id'];
            // blueprint info
            $blueprint_tech = $bpc['bp_tech'];
            $blueprint_type_id = $bpc['bp_tid'];
            $blueprint_name = $bpc['bp_name'];
            $blueprint_qty = $bpc['bp_q'];
            $blueprint_runs = $bpc['bp_r'];
            $blueprint_me = $bpc['bp_me'];
            // material info
            $material_type_id = $bpc['m_id'];
            $material_name = $bpc['m_name'];
            $material_qty = $bpc['m_qty'];

            if ($prev_group != $group_name)
            {
                $prev_group = $group_name;
                ?><tr><td class="active" colspan="9"><strong><?=$group_name?> <span class="text-muted">(<?=$group_id?>)</span></strong></td></tr><?php
            }
            ?>

<tr>
            <?php
            if ($prev_blueprint_name != $blueprint_name)
            {
                $prev_blueprint_name = $blueprint_name;
                $prev_blueprint_qty = null;
                $prev_blueprint_runs = null;
                $prev_blueprint_me = null;
            ?>
 <td><img class="icn32" src="<?=__get_img_src($blueprint_type_id,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?php
    if ($blueprint_qty > 1)
    {
        ?><strong><?=$blueprint_qty?>x</strong> <?php
    }
    ?><?=$blueprint_name?>&nbsp;&nbsp;<span class="text-muted">(<?=$blueprint_type_id?>)</span><?php
    /*if (!is_null($blueprint_tech)) { ?> <span class="label label-default">T<?=$blueprint_tech?></span><?php }*/
?></td>
            <?php
            }
            else
            {
                ?><td colspan="2"><?php
            }
            if ($prev_blueprint_qty != $blueprint_qty ||
                $prev_blueprint_runs != $blueprint_runs ||
                $prev_blueprint_me != $blueprint_me)
            {
                $prev_blueprint_qty = $blueprint_qty;
                $prev_blueprint_runs = $blueprint_runs;
                $prev_blueprint_me = $blueprint_me;
                ?>
 <td><?=$blueprint_qty?></td>
 <td><?=$blueprint_runs?></td>
 <td><?=$blueprint_me?></td>
                <?php
            }
            else
            {
                ?><td colspan="3"><?php
            }
            ?>
 <td><img class="icn16" src="<?=__get_img_src($material_type_id,32,FS_RESOURCES)?>" width="16px" height="16px"></td>
 <td><?php
    if ($material_qty > 1) { ?><strong><?=$material_qty?>x</strong> <?php }
    ?><?=$material_name?><?php /* <br><span class="text-muted"><?=$material_type_id?></span>*/ ?><?php
?></td>
 <td><?php
            if ($material_qty == 1)
            {
                ?><?=$blueprint_qty*$blueprint_runs?><?php
            }
            else
            {
                # считаем бонус чертежа (накладываем ME чертежа на БПЦ)
                $stage1 = (float)($material_qty * $blueprint_runs * (100 - $blueprint_qty) / 100.0);
                # учитываем бонус профиля сооружения
                $stage2 = (float)($stage1 * (100.0 - 1.0) / 100.0);
                # учитываем бонус установленного модификатора
                $stage3 = (float)($stage2 * (100.0 - 4.2) / 100.0);
                # округляем вещественное число до старшего целого
                $stage4 = (int)((float)($stage3 + 0.99));
                ?><?=$stage4?><?php
            }
?></td>
</tr>
            <?php
        }
?>
</tbody>
</table>
<?php
}



    __dump_header("Needs of Industry", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 bp.sdet_group_id grp_id,
 grp.sdecg_group_name grp_name,
 bp.sdet_tech_level bp_tech,
 bpc.t bp_tid,
 bp.sdet_type_name bp_name,
 bpc.q bp_q,
 bpc.r bp_r,
 bpc.me bp_me,
 mat.sdebm_material_id m_id,
 m.sdet_type_name m_name,
 mat.sdebm_quantity m_qty
from (
 select x.t, sum(x.q) q, x.r, x.me from (
  -- список корпоративных чертежей в конвейере (их раны)
  select ecb_type_id t, 1 q, ecb_runs r, ecb_material_efficiency me
  from qi.esi_corporation_blueprints
  where ecb_quantity=-2 and ecb_location_id in (
   select eca_item_id
   from qi.esi_corporation_assets
   where
    eca_corporation_id=98677876 and
    (eca_name like '[prod]%' or
     eca_name like '[order]%' or
     eca_name like '.[prod]%')
  )
  union
  select ecj_product_type_id, ecj_runs, ecj_licensed_runs, coalesce(ecb.me,10)
  from qi.esi_corporation_industry_jobs
   left outer join (
    select ecb_item_id id,ecb_material_efficiency me
    from qi.esi_corporation_blueprints
   ) ecb on (ecb.id=ecj_blueprint_id)
  where
   ecj_corporation_id=98677876 and
   ecj_activity_id=5 and
   ecj_end_date>CURRENT_TIMESTAMP AT TIME ZONE 'GMT' and
   ecj_output_location_id in (
    select eca_item_id 
    from qi.esi_corporation_assets
    where
     eca_corporation_id=98677876 and
     (eca_name like '[prod]%' or
      eca_name like '[order]%' or
      eca_name like '.[prod]%')
   )
 ) x
 group by 1,3,4
) bpc
 -- подробности о чертеже
 left outer join qi.eve_sde_type_ids bp on (bp.sdet_type_id=bpc.t)
 -- группа, которой принадлежит чертёж
 left outer join qi.eve_sde_group_ids grp on (grp.sdecg_group_id=bp.sdet_group_id)
 -- материалы, из которых производится продукция по чертежу
 left outer join qi.eve_sde_blueprint_materials mat on (mat.sdebm_activity=1 and mat.sdebm_blueprint_type_id=bpc.t)
 -- подробности о материале
 left outer join qi.eve_sde_type_ids m on (m.sdet_type_id=mat.sdebm_material_id)
order by 1,3,4,6,7,8,9
EOD;
    $blueprints_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $blueprints = pg_fetch_all($blueprints_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<h2>Needs of Industry</h2>
<?php __dump_blueprints_tree($blueprints); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<?php __dump_copy_to_clipboard_javascript() ?>
