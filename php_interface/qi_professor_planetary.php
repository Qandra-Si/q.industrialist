<?php
include 'qi_render_html.php';
include_once '.settings.php';
?>


<?php function __dump_jita_prices($jita) { ?>
<button class="btn btn-default" type="button" data-toggle="modal" data-target="#showJitaPrices">Цены в Jita</button>
<!-- Modal -->
<div class="modal fade" id="showJitaPrices" tabindex="-1" role="dialog" aria-labelledby="showJitaPricesLabel">
 <div class="modal-dialog" role="document">
  <div class="modal-content">
   <div class="modal-header">
     <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
     <h4 class="modal-title" id="showJitaPricesLabel">Цены в Jita на планетарку</h4>
   </div>
   <div class="modal-body">
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Jita Sell</mark></th>
  <th style="text-align: right;">Jita Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $market_group_id = 0;
    if ($jita)
        foreach ($jita as $product)
        {
            $market_group_id = $product['mgid'];
            $tid = $product['id'];
            $nm = $product['name'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];
?>
<tr>
 <td><img class="icn24" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="24px" height="24px"></td>
 <td><?=$nm?> <a data-target="#" role="button" data-copy="<?=$nm?>" class="qind-copy-btn" data-source="table" data-toggle="tooltip" data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>
 </td>
 <td align="right"><?=number_format($jita_sell,2,'.',',')?></td>
 <td align="right"><?=number_format($jita_buy,2,'.',',')?></td>
</tr>
<?php
        }
?>
</tbody>
</table>
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
   </div>
  </div>
 </div>
</div>
<!-- Modal -->
<?php } ?>


<?php function __dump_planetary_stock($planetary, $jita) { ?>
<table class="table table-condensed" style="padding:1px;font-size:smaller;">
<thead>
 <tr>
  <th></th>
  <th>Items</th>
  <th style="text-align: right;">Quantity</mark></th>
  <th style="text-align: right;">Location</th>
  <th style="text-align: right;">Jita Sell<br>Jita Buy</th>
 </tr>
</thead>
<tbody>
<?php
    $summary_jita_sell = 0;
    $summary_jita_buy = 0;
    $location_jita_sell = 0;
    $location_jita_buy = 0;
    $last_location_id = 0;
    if ($planetary)
        foreach ($planetary as $product)
        {
            $tid = $product['id'];
            $nm = $product['name'];
            $quantity = $product['q'];
            $location_id = $product['lid'];
            $location_flag = $product['f'];
            $jita_sell = $product['js'];
            $jita_buy = $product['jb'];

            if ($last_location_id != $location_id)
            {
                $location_jita_sell = 0;
                $location_jita_buy = 0;
            }

            $location_jita_sell += $jita_sell * $quantity;
            $location_jita_buy += $jita_buy * $quantity;
            $summary_jita_sell += $jita_sell * $quantity;
            $summary_jita_buy += $jita_buy * $quantity;
?>
<tr>
 <td><img class="icn32" src="<?=__get_img_src($tid,32,FS_RESOURCES)?>" width="32px" height="32px"></td>
 <td><?=$nm.'<br><span class="text-muted">'.$tid.'</span> '?></td>
 <td align="right"><?=number_format($quantity,0,'.',',')?></td>
 <td align="right"><?=$location_flag.'<br><span class="text-muted">'.$location_id.'</span>'?></td>
 <td align="right"><?=number_format($jita_sell,2,'.',',').'<br>'.number_format($jita_buy,2,'.',',')?></td>
</tr>
<?php
        }
?>
<tr style="font-weight:bold;">
 <td colspan="4" align="right">Jita Summary</td>
 <td align="right"><?=number_format($summary_jita_sell,0,'.',',').'<br>'.number_format($summary_jita_buy,0,'.',',')?></td>
</tr>
</tbody>
</table>
<?php
} ?>



<?php
    __dump_header("Professor' Planetary", FS_RESOURCES);
    if (!extension_loaded('pgsql')) return;
    $conn = pg_connect("host=".DB_HOST." port=".DB_PORT." dbname=".DB_DATABASE." user=".DB_USERNAME." password=".DB_PASSWORD)
            or die('pg_connect err: '.pg_last_error());
    pg_exec($conn, "SET search_path TO qi");
    //---
    $query = <<<EOD
select
 a.eca_type_id as id,
 tid.sdet_type_name as name,
 a.sum_quantity as q,
 a.eca_location_id as lid,
 a.eca_location_flag as f,
 jita.ethp_sell as js,
 jita.ethp_buy as jb
from (
 select
  eca_type_id,
  eca_location_id,
  eca_location_flag,
  sum(eca_quantity) as sum_quantity
 from qi.esi_corporation_assets
 where eca_corporation_id = 2053528477
 group by 1, 2, 3
) a
 left outer join qi.eve_sde_type_ids tid on (a.eca_type_id = tid.sdet_type_id)
 left outer join qi.esi_trade_hub_prices jita on (a.eca_type_id = jita.ethp_type_id and jita.ethp_location_id = 60003760)
where
 tid.sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) -- планетарка
order by a.eca_location_id, a.eca_location_flag, tid.sdet_market_group_id, tid.sdet_type_name;
EOD;
    $planetary_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $planetary = pg_fetch_all($planetary_cursor);
    //---
    $query = <<<EOD
select 
 tid.sdet_market_group_id as mgid,
 jita.ethp_type_id as id,
 tid.sdet_type_name as name,
 jita.ethp_sell as js,
 jita.ethp_buy as jb 
from qi.esi_trade_hub_prices jita
 left outer join qi.eve_sde_type_ids tid on (jita.ethp_type_id = tid.sdet_type_id)
where
  jita.ethp_location_id = 60003760 and
  tid.sdet_market_group_id in (1333, 1334, 1335, 1336, 1337) -- планетарка
order by 1, 3;
EOD;
    $jita_cursor = pg_query($conn, $query)
            or die('pg_query err: '.pg_last_error());
    $jita = pg_fetch_all($jita_cursor);
    //---
    pg_close($conn);
?>
<div class="container-fluid">
 <?php __dump_jita_prices($jita); ?>
 <?php __dump_planetary_stock($planetary, $jita); ?>
</div> <!--container-fluid-->
<?php __dump_footer(); ?>

<script>
  $(document).ready(function(){
    // Working with clipboard
    $('a.qind-copy-btn').each(function() {
      $(this).tooltip();
    })
    $('a.qind-copy-btn').bind('click', function () {
      var data_copy = $(this).attr('data-copy');
      if (data_copy === undefined) {
        var data_source = $(this).attr('data-source');
        if (data_source == 'table') {
          var tr = $(this).parent().parent();
          var tbody = tr.parent();
          var rows = tbody.children('tr');
          var start_row = rows.index(tr);
          data_copy = '';
          rows.each( function(idx) {
            if (!(start_row === undefined) && (idx > start_row)) {
              var td = $(this).find('td').eq(0);
              if (!(td.attr('class') === undefined))
                start_row = undefined;
              else {
                if (data_copy) data_copy += "\n"; 
                data_copy += td.find('a').attr('data-copy') + "\t" + $(this).find('td').eq(1).attr('quantity');
              }
            }
          });
        } else if (data_source == 'span') {
          var div = $(this).parent();
          var spans = div.children('span');
          data_copy = '';
          spans.each( function(idx) {
            var span = $(this);
            if (data_copy) data_copy += "\n";
            var txt = span.text();
            data_copy += txt.substring(txt.indexOf(' x ')+3) + "\t" + span.attr('quantity');
          });
        }
      }
      var $temp = $("<textarea>");
      $("body").append($temp);
      $temp.val(data_copy).select();
      try {
        success = document.execCommand("copy");
        if (success) {
          $(this).trigger('copied', ['Copied!']);
        }
      } finally {
        $temp.remove();
      }
    });
    $('a.qind-copy-btn').bind('copied', function(event, message) {
      $(this).attr('title', message)
        .tooltip('fixTitle')
        .tooltip('show')
        .attr('title', "Copy to clipboard")
        .tooltip('fixTitle');
    });
    if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
      // какой-то код ...
      $('a.qind-copy-btn').each(function() {
        $(this).addClass('hidden');
      })
    }
  });
</script>
