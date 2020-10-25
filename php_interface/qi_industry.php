<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_factory_summary($summary_factory_cost) { ?>
<tr style="font-weight:bold;">
 <td colspan="2" align="right">Summary</td>
 <td align="right"><?=number_format($summary_factory_cost,0,'.',',')?></td>
</tr>
</tbody>
</table>
<?php } ?>

<?php function __dump_industrial_jobs($jobs, $quantities) {
    $fid = NULL;
    $summary_factory_cost = 0;
    foreach ($jobs as &$job)
    {
        $aid = $job['aid'];
        $bptid = $job['bptid'];
        $single_run_quantity = 1;
        foreach ($quantities as &$q)
        {
            if ($q['bptid'] != $bptid) continue;
            if ($aid == 1)
              $single_run_quantity = intval($q['mq']);
            elseif ($aid == 8)
              $single_run_quantity = intval($q['iq']);
            elseif ($aid == 9 or $aid == 11)
              $single_run_quantity = intval($q['rq']);
            break;
        }
        $ptid = $job['ptid'];
        $nm = $job['nm'];
        $cost = $job['cost'];
        $summary_factory_cost += $cost;
        $products = $job['runs'] * $single_run_quantity;
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
        if ($fid != $job['fid']) {
            if (!is_null($fid)) __dump_factory_summary($summary_factory_cost);
            $fid = $job['fid']; ?>
<h3><?=$fid?></h3>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th style="width:32px;"></th>
  <th>Items</th>
  <th style="text-align: right;">Fee &amp; Tax, ISK</th>
 </tr>
</thead>
<tbody>
<?php } ?>
<tr><!--<?=$ptid?>-->
 <td><img class="icn32" src="<?=__get_img_src($ptid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><strong><?=number_format($products,0,'.',',')?>x</strong> <?=$nm.$anm?></td>
 <td align="right"><?=number_format($cost,0,'.',',')?><br><mark><span style="font-size: smaller;"><?=number_format($cost / $products,2,'.',',')?></span></mark></td>
</tr>
<?php
    }
    __dump_factory_summary($summary_factory_cost);
} ?>


<?php
    __dump_header("Industry", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
SELECT
 wij_facility_id AS fid,
 wij_product_tid AS ptid,
 sden_name AS nm,
 wij_bp_tid AS bptid,
 wij_activity_id AS aid,
 sum(wij_cost) AS cost,
 sum(wij_runs) AS runs
FROM
 workflow_industry_jobs
  LEFT OUTER JOIN eve_sde_names
  ON sden_category=1 AND sden_id=wij_product_tid
--WHERE wij_activity_id=1
GROUP BY 1,2,3,4,5
ORDER BY 1,3;
EOD;
    $jobs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $jobs = pg_fetch_all($jobs_cursor);
    //---
    $query = <<<EOD
SELECT DISTINCT
 wij_bp_tid AS bptid,
 (SELECT sdei_number FROM eve_sde_integers WHERE sdei_id=wij_bp_tid AND sdei_category=5) AS mq,
 (SELECT sdei_number FROM eve_sde_integers WHERE sdei_id=wij_bp_tid AND sdei_category=6) AS iq,
 (SELECT sdei_number FROM eve_sde_integers WHERE sdei_id=wij_bp_tid AND sdei_category=7) AS rq
FROM workflow_industry_jobs
EOD;
    $quantities_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $quantities = pg_fetch_all($quantities_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
<?php __dump_industrial_jobs($jobs, $quantities); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>