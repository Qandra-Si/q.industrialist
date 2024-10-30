<?php
// --------------------------------------------------------------------------------------------------------------
// __get_img_src
// --------------------------------------------------------------------------------------------------------------
function __get_img_src($tp, $sz, $use_filesystem_resources)
{
    if ($use_filesystem_resources)
        return 'image_export_collection/Types/'.$tp.'_'.$sz.'.png';
    else
        return 'http://imageserver.eveonline.com/Type/'.$tp.'_'.$sz.'.png';
}



// --------------------------------------------------------------------------------------------------------------
// __dump_header
// --------------------------------------------------------------------------------------------------------------
function __dump_header($header_name, $use_filesystem_resources, $html_style="", $use_dark_mode=false)
{
    # см. https://github.com/gokulkrishh/awesome-meta-and-manifest
    # см. https://developer.mozilla.org/ru/docs/Web/Manifest
    # рекомендуемый набор favicon-ок, см. https://stackoverflow.com/a/52322368
    # а также тут, см. https://developer.apple.com/design/human-interface-guidelines/ios/icons-and-images/app-icon/#app-icon-sizes
    if ($use_filesystem_resources)
    {
        $bs_css = 'bootstrap/3.4.1/css/bootstrap.min.css';
        $jq_js = 'jquery/jquery-1.12.4.min.js';
        $bs_js = 'bootstrap/3.4.1/js/bootstrap.min.js';
        $bs_dark_css = '../render_stylesheet_dark.css';
    }
    else
    {
        $bs_css = 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous';
        $jq_js = 'https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous';
        $bs_js = 'https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js" integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd" crossorigin="anonymous';
        $bs_dark_css = '/render_stylesheet_dark.css';
    }
?>
<!doctype html>
<html lang="ru">
 <head>
 <meta charset="utf-8">
 <meta http-equiv="X-UA-Compatible" content="IE=edge">
 <meta name="viewport" content="width=device-width,initial-scale=1">
 <meta name="description" content="A tool for planning logistics, building plans for the manufacture of modules, ships, tracking the process of fulfilling contracts.">
 <meta name="keywords" content="eve-online, eve, manufacturing, logistics, q.industrialist">
<style type="text/css">
.icn16 { width:16px; height:16px; }
.icn24 { width:24px; height:24px; }
.icn32 { width:32px; height:32px; }
.icn64 { width:64px; height:64px; }
</style>
 <title><?=$header_name?> - Q.Industrialist</title>
 <link rel="stylesheet" href="<?=$bs_css?>">
 <!-- Android  -->
 <meta name="theme-color" content="#1e2021">
 <meta name="mobile-web-app-capable" content="yes">
 <!-- iOS -->
 <meta name="apple-mobile-web-app-title" content="Q.Industrialist">
 <meta name="apple-mobile-web-app-capable" content="yes">
 <meta name="apple-mobile-web-app-status-bar-style" content="default">
 <!-- Windows  -->
 <meta name="msapplication-navbutton-color" content="#1e2021">
 <meta name="msapplication-TileColor" content="#1e2021">
 <meta name="msapplication-TileImage" content="ms-icon-144x144.png">
 <meta name="msapplication-config" content="browserconfig.xml">
 <!-- Pinned Sites  -->
 <meta name="application-name" content="Q.Industrialist">
 <meta name="msapplication-tooltip" content="Q.Industrialist for EVE Online game">
 <meta name="msapplication-starturl" content="/">
 <!-- Enable night mode for this page  -->
 <meta name="nightmode" content="enable">
 <meta name="color-scheme" content="dark light">
 
 <!-- Main Link Tags -->
 <link rel="icon" type="image/png" sizes="16x16" href="images/favicon/favicon-16x16.png">
 <link rel="icon" type="image/png" sizes="32x32" href="images/favicon/favicon-32x32.png">
 <link rel="icon" type="image/png" sizes="96x96" href="images/favicon/android-icon-96x96.png">
 <!-- Android  -->
 <link rel="icon" type="image/png" sizes="192x192" href="images/favicon/android-icon-192x192.png">
 <link rel="icon" type="image/png" sizes="128x128" href="images/favicon/android-icon-128x128.png">
 <!-- iOS  -->
 <link rel="apple-touch-icon-precomposed" sizes="180x180" href="apple-touch-icon-precomposed.png">
 <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
 <link rel="apple-touch-icon" sizes="120x120" href="images/favicon/apple-icon-120x120.png">
 <link rel="apple-touch-icon" sizes="152x152" href="images/favicon/apple-icon-152x152.png">
 <link rel="apple-touch-icon" sizes="167x167" href="images/favicon/apple-icon-167x167.png">
 <!-- Others -->
 <link rel="shortcut icon" href="favicon.ico" type="image/x-icon">
 <!-- Manifest.json  -->
 <link rel="manifest" href="manifest.webmanifest">
<?=$html_style?>
<?php if ($use_dark_mode) { ?>
 <link rel="stylesheet" href="<?=$bs_dark_css?>">
<?php } ?>
</head>
<body>
 <div class="page-header"><h1>Q.Industrialist <small><?=$header_name?></small></h1></div>
 <script src="<?=$jq_js?>"></script>
 <script src="<?=$bs_js?>"></script>
<?php }




// --------------------------------------------------------------------------------------------------------------
// __dump_footer
// --------------------------------------------------------------------------------------------------------------
function __dump_footer()
{
    $dt = "?"; // datetime.fromtimestamp(time.time(), __g_local_timezone).strftime('%a, %d %b %Y %H:%M:%S %z'))
?>
<p><!--<small><small>Generated <?=$dt?></small><br>-->
<br>
&copy; 2020 Qandra Si &middot; <a class="inert" href="https://github.com/Qandra-Si/q.industrialist">GitHub</a> &middot; Data provided by <a class="inert" href="https://esi.evetech.net/">ESI</a> and <a class="inert" href="https://zkillboard.com/">zKillboard</a> &middot; Tips go to <a class="inert" href="https://zkillboard.com/character/2116129465/">Qandra Si</a> &middot; v1.1-Imine<br>
<br>
<small>EVE Online and the EVE logo are the registered trademarks of CCP hf. All rights are reserved worldwide. All other trademarks are the property of their respective owners. EVE Online, the EVE logo, EVE and all associated logos and designs are the intellectual property of CCP hf. All artwork, screenshots, characters, vehicles, storylines, world facts or other recognizable features of the intellectual property relating to these trademarks are likewise the intellectual property of CCP hf.</small>
</small></p>
</body></html>
<?php }




// --------------------------------------------------------------------------------------------------------------
// __dump_any_into_modal_header_wo_button
// --------------------------------------------------------------------------------------------------------------
function __dump_any_into_modal_header_wo_button($name, $unique_id=NULL, $modal_size=NULL)
{
    $name_merged = is_null($unique_id) ? str_replace($name, ' ', '') : $unique_id;
    $mdl_sz = is_null($modal_size) ? '' : ' '.$modal_size;
?>
<!-- <?=$name?> Modal -->
<div class="modal fade" id="modal<?=$name_merged?>" tabindex="-1" role="dialog" aria-labelledby="modal<?=$name_merged?>Label">
 <div class="modal-dialog<?=$mdl_sz?>" role="document">
  <div class="modal-content">
   <div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
    <h4 class="modal-title" id="modal<?=$name_merged?>Label"><?=$name?></h4>
   </div>
   <div class="modal-body">
<?php }




// --------------------------------------------------------------------------------------------------------------
// __dump_any_into_modal_header
// --------------------------------------------------------------------------------------------------------------
function __dump_any_into_modal_header($name, $unique_id=NULL, $btn_size="btn-lg", $btn_nm=NULL, $modal_size=NULL)
{
    $name_merged = is_null($unique_id) ? str_replace($name, ' ', '') : $unique_id;
    $btn_nm = is_null($btn_nm) ? 'Show '.$name : $btn_nm;
?>
<!-- Button trigger for <?=$name?> Modal -->
<button type="button" class="btn btn-primary <?=$btn_size?>" data-toggle="modal" data-target="#modal<?=$name_merged?>"><?=$btn_nm?></button>
<?php
    __dump_any_into_modal_header_wo_button($name, $unique_id, $modal_size);
}




// --------------------------------------------------------------------------------------------------------------
// __dump_any_into_modal_footer
// --------------------------------------------------------------------------------------------------------------
function __dump_any_into_modal_footer() { ?>
   </div>
   <div class="modal-footer">
    <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>
    <!-- <button type="button" class="btn btn-primary">Choose</button> -->
   </div>
  </div>
 </div>
</div>
<?php
}




// --------------------------------------------------------------------------------------------------------------
// get_glyph_icon_button
// --------------------------------------------------------------------------------------------------------------
function get_glyph_icon_button(string $glyph, string $html="") {
    return ' <a data-target="#" role="button" '.$html.' data-original-title="" title=""><span class="glyphicon glyphicon-'.$glyph.'" aria-hidden="true"></a>';
}
// --------------------------------------------------------------------------------------------------------------
// get_clipboard_copy_button
// --------------------------------------------------------------------------------------------------------------
function get_clipboard_copy_button(&$data_copy) {
    return get_glyph_icon_button("copy", 'data-copy="'.$data_copy.'" class="qind-copy-btn" data-toggle="tooltip"');
}




// --------------------------------------------------------------------------------------------------------------
// __dump_copy_to_clipboard_javascript
// --------------------------------------------------------------------------------------------------------------
function __dump_copy_to_clipboard_javascript() {
?><script>
function doCopyToClpbrd(self, data_copy) {
 if (data_copy) {
  if (window.isSecureContext && navigator.clipboard) {
   navigator.clipboard.writeText(data_copy).then(() => {
    self.trigger('copied', ['Copied!']);
   }, (e) => {
    self.trigger('copied', ['Data not copied!']);
   });
   document.execCommand("copy");
  }
  else {
   var $temp = $("<textarea>");
   $("body").append($temp);
   $temp.val(data_copy).select();
   try {
    success = document.execCommand("copy");
    if (success)
     self.trigger('copied', ['Copied!']);
    else
     self.trigger('copied', ['Data not copied!']);
   } finally {
    $temp.remove();
   }
  }
 }
 else {
  self.trigger('copied', ['Nothing no copy!']);
 }
}
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
      var td0 = $(this).find('td').eq(0); // ищём <td#0 class='active'>
      if (!(td0.attr('class') === undefined))
       start_row = undefined;
      else {
       //ищём <tr>...<td#1><a data-copy='?'>...
       var td1a = $(this).find('td').eq(1).find('a');
       if (!(td1a === undefined)) {
        var nm = td1a.attr('data-copy');
        if (!(nm === undefined)) {
         var td2q = $(this).find('td').eq(2).attr('quantity');
         if (!(td2q === undefined) && (td2q > 0)) {
          if (data_copy) data_copy += "\n";
          data_copy += nm + "\t" + td2q;
         }
        }
       }
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
  doCopyToClpbrd($(this), data_copy);
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
</script><?php }

// --------------------------------------------------------------------------------------------------------------
// __dump_clipboard_waiter
// --------------------------------------------------------------------------------------------------------------
function __dump_clipboard_waiter($notice) { ?>
<noscript>Вам необходимо включить JavaScript для использования этой программы.</noscript>
<?php if ($notice) { ?>
<center>
<h2>Вставьте содержимое буфера обмена...</h2>
<div class="row">
 <div class="col-md-2"></div>
 <div class="col-md-8">
 <p>В окне контейнера выберите <mark>Режим просмотра (Список)</mark>, затем выделите нужную позицию, щёлкните <kbd>Right-click</kbd> на выбранных строках и выберите "Скопировать". Также можно использовать копирование с помощью кнопок клавиатуры <kbd>Cmd</kbd>&nbsp;|&nbsp;<kbd>Ctrl</kbd>&nbsp;+&nbsp;<kbd>A</kbd>, затем <kbd>Cmd</kbd>&nbsp;|&nbsp;<kbd>Ctrl</kbd>&nbsp;+&nbsp;<kbd>C</kbd>. после чего вернитесь на эту страницу и нажмите <kbd>Cmd</kbd>&nbsp;|&nbsp;<kbd>Ctrl</kbd>&nbsp;+&nbsp;<kbd>V</kbd> для получения отчёта по скопированным предметам.</p>
 </div>
 <div class="col-md-2"></div>
</div> <!--row-->
</center>
<?php } ?>
<script src="/tools/tids.php"></script>
<script>
document.addEventListener('paste', async (e) => {
 e.preventDefault();
 const paste = (e.clipboardData || window.clipboardData).getData('text');
 const lines = paste.split('\n');
 var uri = '';
 for (const line of lines) {
<?php
/* == Форматы копируемой информации ==
Имущество (режим просмотра, список):
10MN Afterburner II	45	Propulsion Module			225 м^3	109 222 217,10 ISK
10MN Afterburner II<t><right>45<t>Propulsion Module<t><t><t><right>225 м^3<t><right>109 222 217,10 ISK
Имущество (режим просмотра, информация):
10MN Afterburner II	45	Propulsion Module			225 м^3	109 222 217,10 ISK
10MN Afterburner II<t><right>45<t>Propulsion Module<t><t><t><right>225 м^3<t><right>109 222 217,10 ISK
Имущество (режим просмотра, пиктограммы):
10MN Afterburner II	45
Мои ордера:
10MN Afterburner II	5/5	2 546 000,00 ISK	B2J-5N - Shukhov (R)	Malpais	89д 23ч 48мин 12с
10MN Afterburner II<t><right>5/5<t><right><color='0xFFFFFFFF'>2 546 000,00 ISK</color></right><t>B2J-5N - Shukhov (R)<t>Malpais<t>89д 23ч 41мин 47с
Корпоративные ордера:
10MN Afterburner II	5/5	2 546 000,00 ISK	B2J-5N - Shukhov (R)	Malpais	89д 23ч 41мин 20с	Qandra Si	Главный счет 
10MN Afterburner II<t><right>5/5<t><right><color='0xFFFFFFFF'>2 546 000,00 ISK</color></right><t>B2J-5N - Shukhov (R)<t>Malpais<t>89д 23ч 42мин 46с<t>Qandra Si<t>Главный счет 
История заказов:
Отменён	2023.09.24 16:33:00	Warp Disruptor II	10 / 10	1 757 000,00 ISK	B2J-5N - Shukhov (R)	Malpais
Отменён<t>2023.09.24 16:33:00<t>Warp Disruptor II<t>10 / 10<t><right>1 757 000,00 ISK</right><t>B2J-5N - Shukhov (R)<t>Malpais
Название предмета:
10MN Afterburner II
*/
?>
  const words = line.split('\t');
  const len = words.length;
  if (len == 0) continue;
  var t = words[0];
  var tid = getSdeItemId(t);
  if (tid) {
   var cnt = 1;
   if (len >= 2) {
    cnt = words[1];
    if (cnt.includes('/')) cnt = cnt.split('/')[0];
    cnt = cnt.replace(/\s/g, '');
    if (!cnt) cnt = 1;
   }
   if (uri) uri += ',';
   uri += tid+','+cnt;
  }
 }
 if (uri) location.assign("<?=strtok($_SERVER['REQUEST_URI'],'?')?>?id="+uri);
});
</script>
<?php }
?>

