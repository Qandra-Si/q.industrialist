<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_conveyor_settings($settings) { ?>
<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="collapsed navbar-toggle" data-toggle="collapse"
    data-target="#bs-jobs-navbar-collapse" aria-expanded="false">
   <span class="sr-only">Toggle navigation</span>
   <span class="icon-bar"></span>
   <span class="icon-bar"></span>
   <span class="icon-bar"></span>
   </button>
   <a data-target="#" class="navbar-brand">Conveyor Entities</a>
  </div>
  <div class="collapse navbar-collapse" id="bs-jobs-navbar-collapse">
   <button type="button" class="btn btn-default navbar-btn" id="qind-btn-add">Add new</button>
  </div>
 </div>
</nav> 
<div class="panel-group" id="monthly_jobs" role="tablist" aria-multiselectable="true">
<?php
    // вывод информации о корабле, а также формирование элементов пользовательского интерфейса
    foreach ($settings as &$entity)
    {
        $id = $entity['cs_id'];
        $bp_nms = $entity['cs_bp_nms'];
        $stock_nms = $entity['cs_stock_nms'];
        $exclude_nms = $entity['cs_exclude_nms'];
        $same_stock = $entity['cs_same_stock'] == 't';
        $fixed_runs = $entity['cs_fixed_runs'];
        $remarks = $entity['cs_remarks'];
        $active = $entity['cs_active'];
?>
<div class="panel panel-<?=($active=='f')?'warning':'default'?>">
 <div class="panel-heading" role="tab" id="conv_entity_hd<?=$id?>">
  <h4 class="panel-title">
   <a role="button" data-toggle="collapse"
    href="#conv_entity_collapse<?=$id?>" aria-expanded="true"
    aria-controls="conv_entity_collapse<?=$id?>"><strong>№ <?=$id?></strong>&nbsp;<?=($active=='f')?'(archival copy)&nbsp;':''?></a>
  </h4>
  <span id="qind-job-rmrks<?=$id?>" class="text-success"><small><?=$remarks?></small></span>
 </div>
 <div id="conv_entity_collapse<?=$id?>" class="panel-collapse collapse"
  role="tabpanel" aria-labelledby="conv_entity_hd<?=$id?>">
  <div class="panel-body">
   <div class="row">
    <div class="col-md-6">
    </div>
    <div class="col-md-4 col-md-offset-2" align="right">
     <button type="button" class="btn btn-default btn-xs qind-btn-edit" entity="<?=$id?>"><span
      class="glyphicon glyphicon-pencil" aria-hidden="true"></span></button>
     <?php if ($active=='t') { ?>
     <button type="button" class="btn btn-default btn-xs qind-btn-arch" entity="<?=$id?>" action="deact"><span class="glyphicon
      glyphicon-cloud" aria-hidden="true"></span></button>
     <button type="button" class="btn btn-default btn-xs disabled"><span class="glyphicon
      glyphicon-trash" aria-hidden="true"></span></button>
     <?php } else { ?>
     <button type="button" class="btn btn-default btn-xs qind-btn-arch" entity="<?=$id?>" action="act"><span class="glyphicon
      glyphicon-cloud-download" aria-hidden="true"></span></button>
     <button type="button" class="btn btn-default btn-xs qind-btn-del" entity="<?=$id?>"><span class="glyphicon
      glyphicon-trash" aria-hidden="true"></span></button>
     <?php } ?>
    </div>
   </div>
   <hr style="margin-top: 6px; margin-bottom: 10px;">
   <dl>
    <dt>Blueprint Containers</dt><dd><?=$bp_nms?></dd>
    <?php if ($same_stock) { ?>
     <dt>Same Stock Containers</dt><dd>yes</dd>
    <?php } else { ?>
     <dt>Stock Containers</dt><dd><?=$stock_nms?></dd>
    <?php } ?>
    <?php if ($exclude_nms) { ?>
     <dt>Exclude Containers</dt><dd><?=$exclude_nms?></dd>
    <?php } ?>
    <?php if ($fixed_runs) { ?>
     <dt>Fixed Number of Runs</dt><dd><?=$fixed_runs?></dd>
    <?php } ?>
   </dl>
  </div>
 </div>
</div>
<?php } ?>
</div>
<?php } ?>


<?php
    __dump_header("Conveyor Settings", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = 'SELECT cs_id,cs_bp_nms,cs_stock_nms,cs_exclude_nms,cs_same_stock,cs_fixed_runs,cs_remarks,cs_active FROM conveyor_settings ORDER BY 1;';
    $jobs_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $jobs = pg_fetch_all($jobs_cursor);
    //---
    $query = 'SELECT ms_key,ms_val FROM modules_settings WHERE ms_module IN (SELECT ml_id FROM modules_list WHERE ml_name=$1);';
    $params = array('conveyor');
    $settings_cursor = pg_query_params($conn, $query, $params)
            or die('pg_query_params err: '.pg_last_error());
    if (pg_num_rows($settings_cursor) > 0)
        $settings = pg_fetch_all($settings_cursor);
    else
        $settings = NULL;
    //---
    pg_close($conn);
?>
<div class="container-fluid">
 <div class="row">
  <div class="col-md-6">
   <h3>Conveyor Settings</h3>
   <?php __dump_conveyor_settings($jobs); ?>
  </div>
  <div class="col-md-6">
  </div>
 </div> <!--row-->
</div> <!--container-fluid-->
<?php __dump_footer(); ?>