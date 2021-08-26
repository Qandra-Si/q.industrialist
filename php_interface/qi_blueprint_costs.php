<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_blueprint_costs($costs) {
?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th>System / ID</th>
  <th style="width:32px;"></th>
  <th>Blueprint</th>
  <th style="width:32px;"></th>
  <th>Product</th>
  <th>Rest links</th>
  <th style="text-align: right;">Cost</th>
  <th style="text-align: right;">Pay &amp; Tax</th>
  <th>Date / time</th>
 </tr>
</thead>
<tbody>
<?php
    foreach ($costs as &$item)
    {
        $ss = $item['ss'];
        $tt = $item['tt'];
        $id = $item['id'];
        $bpt = $item['bpt'];
        $bptn = $item['bptn'];
        $bpr = $item['bpr'];
        $jid = $item['jid'];
        $jc = $item['jc'];
        $jpay = $item['jpay'];
        $jtax = $item['jtax'];
        $dt = $item['dt'];
        $dtt = $item['dtt'];
        $ecj_r = $item['ecj_r'];
        $ecj_sr = $item['ecj_sr'];
        if ($tt == 'A')
        {
            $te = $item['te'];
            $me = $item['me'];
            $bpid = $item['bpid'];
?>
<tr<?=!is_null($jid)?' class="info"':''?>>
<td<?php if (!is_null($ss)) { ?> align="left"><?=$ss?><?php } else { ?>><?php } ?><br><span class="text-muted">№ <?=$id?></span></td>
<td><img class="icn32" src="<?=__get_img_src($bpt,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
<?php
            if ($bpr == -1) // BPO
            {
?>
<td colspan="4"><?=$bptn?>&nbsp;<span class="label label-success"><?=$me?> <?=$te?></span>&nbsp;<span class="label label-default">original</span><br><span class="text-muted">BP № <?=$bpid?><?php if (!is_null($jid)) { ?> = <span class="text-info">JOB № <?=$jid?></span><?php } ?></span></td>
<?php
            }
            else // BPC
            {
?>
<td colspan="4"><?=$bptn?>&nbsp;<span class="label label-success"><?=$me?> <?=$te?></span>&nbsp;<small><span class="badge"><?=$bpr?></span></small><br><span class="text-muted">BP № <?=$bpid?><?php if (!is_null($jid)) { ?> = <span class="text-info">JOB № <?=$jid?></span><?php } ?></span></td>
<?php
            }
        }
        else // $tt in 'p','f'
        {
            //$cid = $item['cid'];
            $aid = $item['aid'];
            $jr = $item['jr'];
            $sr = $item['sr'];
            $pt = $item['pt'];
            $ptn = $item['ptn'];
            $jte = $item['jte'];
            $jme = $item['jme'];
            switch ($aid)
            {
            case 1: $anm = '&nbsp;<span class="label label-primary">manufacturing</span>'; break;  # Manufacturing
            case 3: $anm = '&nbsp;<span class="label label-info">te</span>'; break;  # Science
            case 4: $anm = '&nbsp;<span class="label label-info">me</span>'; break;  # Science
            case 5: $anm = '&nbsp;<span class="label label-info">copying</span>'; break;  # Science
            case 7: $anm = '&nbsp;<span class="label label-info">reverse</span>'; break;  # Science
            case 8: $anm = '&nbsp;<span class="label label-info">invention</span>'; break;  # Science
            case 11:
            case 9: $anm = '&nbsp;<span class="label label-success">reaction</span>'; break;  # Reaction
            default:$anm = '&nbsp;<span class="label label-danger">activity#'.$aid.'</span>'; break;
            }
            if ($aid == 8) // invent
            {
?>
<tr class="<?=($tt=='p')?'success':'warning'?>">
<td<?php if (!is_null($ss)) { ?> align="left"><?=$ss?><?php } else { ?>><?php } ?><br><span class="text-muted">№ <?=$id?></span></td>
<td><img class="icn32" src="<?=__get_img_src($bpt,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
<td><?=$bptn?><small>&nbsp;<span class="badge"><?=is_null($ecj_sr)?'?':$ecj_sr?> of <?=$ecj_r?> runs</span></small><br><span class="text-info">JOB № <?=$jid?></span><?=$anm?></td>
<td><img class="icn32" src="<?=__get_img_src($pt,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
<td><?=$ptn?></td>
<td><?=$ecj_sr-$sr?> of <?=is_null($ecj_sr)?'?':$ecj_sr?></td>
<?php
            }
            else // copy
            {
?>
<tr class="<?=($tt=='p')?'success':'warning'?>">
<td<?php if (!is_null($ss)) { ?> align="left"><?=$ss?><?php } else { ?>><?php } ?><br><span class="text-muted">№ <?=$id?></span></td>
<td><img class="icn32" src="<?=__get_img_src($bpt,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
<td colspan="3"><?=$bptn?><small>&nbsp;<span class="badge"><?=$ecj_r?> runs <?=$bpr?>x</span></small><br><span class="text-info">JOB № <?=$jid?></span><?=$anm?>&nbsp;<span class="label label-success"><?=is_null($jme)?'?':$jme?> <?=is_null($jte)?'?':$jte?></span></td>
<td><?=$ecj_r-$jr?> of <?=$ecj_r?></td>
<?php
            }
        }
        // началу у записей разное, завершение одинаковое
?>
<td<?php if (!is_null($jc)) { ?> align="right"><?=number_format($jc,0,'.',',')?><?php if (!is_null($ecj_sr) && ($ecj_sr>0)) { ?><br><mark><?=number_format($jc/$ecj_sr,0,'.',',')?></mark><?php } } else { ?>><?php } ?></td>
<td<?php if (!is_null($jpay)) { ?> align="right"><?=number_format($jpay,0,'.',',').'&nbsp;/&nbsp;'.number_format($jtax,0,'.',',')?><?php if (!is_null($ecj_sr) && ($ecj_sr>0)) { ?><br><mark><?=number_format($jpay/$ecj_sr,0,'.',',').'&nbsp;/&nbsp;'.number_format($jtax/$ecj_sr,0,'.',',')?></mark><?php } } else { ?>><?php } ?></td>
<td><?=$dt?><br><?=$dtt?></td>
</tr>
<?php
    }
?>
</tbody>
</table>
<?php
} ?>


<?php
    __dump_header("Blueprint Costs", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 (select sden_name from eve_sde_names where sden_category = 3 and sden_id = ebc_system_id) as ss,
 ebc_transaction_type as tt,
 ebc_id as id,
 ebc_blueprint_id as bpid,
 ebc_blueprint_type_id as bpt,
 (select sden_name from eve_sde_names where sden_category = 1 and sden_id = ebc_blueprint_type_id) as bptn,
 ebc_blueprint_runs as bpr,
 ebc_time_efficiency as te,
 ebc_material_efficiency as me,
 ebc_job_id as jid,
 -- ebc_job_corporation_id as cid,
 ebc_job_activity as aid,
 ebc_job_runs as jr,
 ebc_job_product_type_id as pt,
 (select sden_name from eve_sde_names where sden_category = 1 and sden_id = ebc_job_product_type_id) as ptn,
 ebc_job_successful_runs as sr,
 ebc_job_time_efficiency as jte,
 ebc_job_material_efficiency as jme,
 j.ecj_cost as jc,
 ebc_industry_payment as jpay,
 ebc_tax as jtax,
 to_char(ebc_created_at,'Mon DD') as dt,
 to_char(ebc_created_at,'HH24:MI:SS') as dtt,
 j.ecj_runs as ecj_r,
 j.ecj_successful_runs as ecj_sr
from
 esi_blueprint_costs
  left outer join qi.esi_corporation_industry_jobs j
   on ecj_job_id=ebc_job_id and ecj_corporation_id=ebc_job_corporation_id
where
 ( ebc_transaction_type in ('f','p','j') or 
   (ebc_transaction_type in ('A') and (ebc_blueprint_runs != -1))
 )
 and ebc_created_at >= (current_timestamp at time zone 'GMT' - interval '7 days')
order by
 ebc_created_at DESC;
EOD;
    $costs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $costs = pg_fetch_all($costs_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_blueprint_costs($costs); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
