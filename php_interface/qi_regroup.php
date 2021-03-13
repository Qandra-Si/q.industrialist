<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>

<?php function __dump_regroup_stock($regroup) { ?>
<nav class="navbar navbar-default">
 <div class="container-fluid">
  <div class="navbar-header">
   <button type="button" class="collapsed navbar-toggle" data-toggle="collapse"
    data-target="#bs-regroup-navbar-collapse" aria-expanded="false">
   <span class="sr-only">Toggle navigation</span>
   <span class="icon-bar"></span>
   <span class="icon-bar"></span>
   <span class="icon-bar"></span>
   </button>
   <a data-target="#" class="navbar-brand">Регруп</a>
  </div>
  <div class="collapse navbar-collapse" id="bs-regroup-navbar-collapse">
   <button type="button" class="btn btn-default navbar-btn" id="qind-btn-add">Добавить новый</button>
  </div>
 </div>
</nav> 
<div class="panel-group" id="regroup_fits" role="tablist" aria-multiselectable="true">
<?php
    // вывод информации о корабле, а также формирование элементов пользовательского интерфейса
    if (!$regroup)
        ;
    else
    {
        foreach ($regroup as &$rgrp)
        {
            $id = $rgrp['rs_id'];
            $active = $rgrp['rs_active'];
            $q = $rgrp['rs_quantity'];
            $sttn = $rgrp['rs_station'];
            $cntnr = $rgrp['rs_container'];
            $rmrk = $rgrp['rs_remarks'];
            $fit = $rgrp['rs_eft'];
            $fit_first_line = trim(strtok($fit, "\n"));
            $cmnt = substr(strstr($fit_first_line, ','), 2, -1);
            $nm = substr(strtok($fit_first_line, ","), 1);
?>
<div class="panel panel-<?=($active=='f')?'warning':'default'?>">
 <div class="panel-heading" role="tab" id="rgrpfit_hd<?=$id?>">
  <h4 class="panel-title">
   <a role="button" data-toggle="collapse"
    href="#rgrpfit_collapse<?=$id?>" aria-expanded="true"
    aria-controls="rgrpfit_collapse<?=$id?>"><strong><?=$nm?></strong>&nbsp;<?=($active=='f')?'(archival copy)&nbsp;':''?><span
    class="badge" id="qind-rgrpfit-q<?=$id?>"><?=$q?></span></a>
  </h4>
  <span class="text-info"><small><strong>EFT comment: </strong><?=$cmnt?></small></span><br>
  <span class="text-default"><small><strong>Станция: </strong><span id="qind-rgrpfit-sttn<?=$id?>"><?=$sttn?></span></small></span><br>
  <span class="text-default"><small><strong>Контейнер: </strong><span id="qind-rgrpfit-cntnr<?=$id?>"><?=$cntnr?></span></small></span><br>
  <span class="text-success"><small><strong>Примечание: </strong><span id="qind-rgrpfit-rmrk<?=$id?>"><?=$rmrk?></span></small></span>
 </div>
 <div id="rgrpfit_collapse<?=$id?>" class="panel-collapse collapse"
  role="tabpanel" aria-labelledby="rgrpfit_hd<?=$id?>">
  <div class="panel-body">
   <div class="row">
    <div class="col-md-6">
     <button type="button" class="btn btn-default btn-xs disabled"><span
      class="glyphicon glyphicon-eye-close" aria-hidden="true"></span>&nbsp;<span>T2</span></button>
     <button type="button" class="btn btn-default btn-xs qind-btn-eft" data-toggle="modal"
      data-target="#modalEFT<?=$id?>"><span class="glyphicon glyphicon-th-list"
      aria-hidden="true"></span>&nbsp;EFT</button>
    </div>
    <div class="col-md-4 col-md-offset-2" align="right">
     <button type="button" class="btn btn-default btn-xs qind-btn-edit" rgrpfit="<?=$id?>" ship="<?=$nm?>"><span
      class="glyphicon glyphicon-pencil" aria-hidden="true"></span></button>
     <?php if ($active=='t') { ?>
     <button type="button" class="btn btn-default btn-xs qind-btn-arch" rgrpfit="<?=$id?>" action="deact"><span class="glyphicon
      glyphicon-cloud" aria-hidden="true"></span></button>
     <button type="button" class="btn btn-default btn-xs disabled"><span class="glyphicon
      glyphicon-trash" aria-hidden="true"></span></button>
     <?php } else { ?>
     <button type="button" class="btn btn-default btn-xs qind-btn-arch" rgrpfit="<?=$id?>" action="act"><span class="glyphicon
      glyphicon-cloud-download" aria-hidden="true"></span></button>
     <button type="button" class="btn btn-default btn-xs qind-btn-del" rgrpfit="<?=$id?>"><span class="glyphicon
      glyphicon-trash" aria-hidden="true"></span></button>
     <?php } ?>
    </div>
   </div>
   <hr style="margin-top: 6px; margin-bottom: 10px;">
   <pre class="pre-scrollable" style="border: 0; background-color: transparent; font-size: 11px;"
    id="qind-rgrpfit-eft<?=$id?>"><?=$fit?></pre></div>
 </div>
</div>
<?php
        // добавление окна, в котором можно просматривать и копировать EFT
        __dump_any_into_modal_header_wo_button(
            sprintf('<strong>%sx %s</strong>%s',
                    $q,
                    $nm,
                    !is_null($rmrk) && !empty($rmrk) ? '<small><br>'.$rmrk.'</small>' : ''
            ),
            'EFT'.$id, // modal добавляется автоматически
            NULL // 'modal-sm'
        );
        // формируем содержимое модального диалога
        echo '<textarea onclick="this.select();" class="col-md-12" rows="15" style="resize:none"'.
             ' readonly="readonly">'.$fit.'</textarea>';
        // закрываем footer модального диалога
        __dump_any_into_modal_footer();
        }
        unset($rgrp);
    }
?>
</div>
<form class="hidden" action="qi_digger.php" method="get" id="frmDelFit">
 <input type="hidden" name="module" value="regroup">
 <input type="hidden" name="action" value="del">
 <input type="hidden" name="fit" value="-1">
</form>
<script>
$(document).ready(function(){
  $('button.qind-btn-del').each(function(){
    $(this).on('click', function () {
      var frm = $("#frmDelFit");
      frm.find("input[name='fit']").val($(this).attr('rgrpfit'));
      frm.submit();
    })
  })
})
</script>

<form class="hidden" action="qi_digger.php" method="get" id="frmArchiveFit">
 <input type="hidden" name="module" value="regroup">
 <input type="hidden" name="action" value="">
 <input type="hidden" name="fit" value="-1">
</form>
<script>
$(document).ready(function(){
  $('button.qind-btn-arch').each(function(){
    $(this).on('click', function () {
      var frm = $("#frmArchiveFit");
      frm.find("input[name='fit']").val($(this).attr('rgrpfit'));
      frm.find("input[name='action']").val($(this).attr('action'));
      frm.submit();
    })
  })
})
</script>

<div class="modal fade" id="modalFit" tabindex="-1" role="dialog" aria-labelledby="modalFitLabel">
 <div class="modal-dialog" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modalFitLabel"></h4>
   </div>
   <div class="modal-body">
    <form action="qi_digger.php" method="post" id="frmEditFit">
     <input type="hidden" name="module" value="regroup">
     <input type="hidden" name="action" value="edit">
     <input type="hidden" name="fit" value="0">
     <div class="form-group">
      <label for="eft">EFT</label>
      <textarea class="form-control" id="eft" name="eft" rows="15" style="resize:none; font-size: 11px;" spellcheck="false"></textarea>
     </div>
     <div class="form-group">
      <label for="quantity">Кол-во комплектов</label>
      <input type="number" class="form-control" id="quantity" name="quantity" min="1" max="100000">
     </div>
     <div class="form-group">
      <label for="station">Название станции (структуры)</label>
      <input class="form-control" id="station" name="station" value="" maxlength="127">
     </div>
     <div class="form-group">
      <label for="container">Название контейнера</label>
      <input class="form-control" id="container" name="container" value="" maxlength="127">
     </div>
     <div class="form-group">
      <label for="remarks">Примечание</label>
      <input class="form-control" id="remarks" name="remarks" value="" maxlength="127">
     </div>
    </form>
   </div>
   <div class="modal-footer">
    <button type="submit" class="btn btn-primary" onclick="$('#frmEditFit').submit();">Save</button>
    <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
   </div>
  </div>
 </div>
</div>
<script>
$(document).ready(function(){
  $('button.qind-btn-edit').each(function(){
    $(this).on('click', function () {
      var rgrpfit = $(this).attr('rgrpfit');
      var ship = $(this).attr('ship');
      var conv = !($("#qind-rgrpfit-conv"+rgrpfit).html() === undefined);
      var q = $("#qind-rgrpfit-q"+rgrpfit).text();
      var sttn = $('#qind-rgrpfit-sttn'+rgrpfit).text();
      var cntnr = $('#qind-rgrpfit-cntnr'+rgrpfit).text();
      var rmrk = $('#qind-rgrpfit-rmrk'+rgrpfit).text();
      var eft = $('#qind-rgrpfit-eft'+rgrpfit).html();
      var modal = $("#modalFit");
      $('#modalFitLabel').html(q + 'x ' + ship);
      modal.find('textarea').html(eft);
      modal.find("input[name='station']").val(sttn);
      modal.find("input[name='container']").val(cntnr);
      modal.find("input[name='remarks']").val(rmrk);
      modal.find("input[name='quantity']").val(q);
      modal.find("input[name='fit']").val(rgrpfit);
      modal.find("input[name='action']").val('edit');
      modal.modal('show');
      frm.submit();
    })
  })
  $('#qind-btn-add').on('click', function () {
      var modal = $("#modalFit");
      $('#modalFitLabel').html('Добавление нового плана отслеживания регрупа...');
      modal.find('textarea').html('');
      modal.find("input[name='station']").val('');
      modal.find("input[name='container']").val('');
      modal.find("input[name='remarks']").val('');
      modal.find("input[name='quantity']").val(1);
      modal.find("input[name='fit']").val(0);
      modal.find("input[name='action']").val('add');
      modal.modal('show');
      frm.submit();
  })
})
</script>
<?php } ?>


<?php
    __dump_header("Regroup Settings", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = 'SELECT rs_id,rs_active,rs_quantity,rs_eft,rs_station,rs_container,rs_remarks FROM regroup_stock ORDER BY 4;';
    $regroup_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $regroup = pg_fetch_all($regroup_cursor);
?>
<div class="container-fluid">
 <div class="row">
  <div class="col-md-6">
   <h3>Отслеживаемые фиты регрупа</h3>
   <?php __dump_regroup_stock($regroup); ?>
  </div>
 </div> <!--row-->
</div> <!--container-fluid-->
<?php
    pg_close($conn);
    //---
    __dump_footer();
?>