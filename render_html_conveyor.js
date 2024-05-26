//var g_menu_options_default=[[1,"impossible"],[1,"not-available"],[1,"end-level-manuf"],[1,"intermediate-manuf"],[1,"recommended-runs"]];
//var g_menu_options_default_len=5;
//var g_menu_sort_default='priority';

// Conveyor Options storage (prepare)
ls = window.localStorage;

//-----------
// утилиты
//-----------
function numLikeEve(x) {
 if (x < 1.0) return x;
 return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
(function() {
 /**
  * Корректировка округления десятичных дробей.
  *
  * @param {String}  type  Тип корректировки.
  * @param {Number}  value Число.
  * @param {Integer} exp   Показатель степени (десятичный логарифм основания корректировки).
  * @returns {Number} Скорректированное значение.
  */
 function decimalAdjust(type, value, exp) {
  // Если степень не определена, либо равна нулю...
  if (typeof exp === 'undefined' || +exp === 0) {
   return Math[type](value);
  }
  value = +value;
  exp = +exp;
  // Если значение не является числом, либо степень не является целым числом...
  if (isNaN(value) || !(typeof exp === 'number' && exp % 1 === 0)) {
   return NaN;
  }
  // Сдвиг разрядов
  value = value.toString().split('e');
  value = Math[type](+(value[0] + 'e' + (value[1] ? (+value[1] - exp) : -exp)));
  // Обратный сдвиг
  value = value.toString().split('e');
  return +(value[0] + 'e' + (value[1] ? (+value[1] + exp) : exp));
 }
 // Десятичное округление к ближайшему
 if (!Math.round10) {
  Math.round10 = function(value, exp) {
   return decimalAdjust('round', value, exp);
  };
 }
 // Десятичное округление вниз
 if (!Math.floor10) {
  Math.floor10 = function(value, exp) {
   return decimalAdjust('floor', value, exp);
  };
 }
 // Десятичное округление вверх
 if (!Math.ceil10) {
  Math.ceil10 = function(value, exp) {
   return decimalAdjust('ceil', value, exp);
  };
 }
})();
function eveCeiling(isk) {
  if (isk < 100.0) ;
  else if (isk < 1000.0) isk = Math.ceil10(isk * 10.0) / 10.0;
  else if (isk < 10000.0) isk = Math.ceil10(isk);
  else if (isk < 100000.0) isk = Math.round10(isk+5, 1);
  else if (isk < 1000000.0) isk = Math.round10(isk+50, 2);
  else if (isk < 10000000.0) isk = Math.round10(isk+500, 3);
  else if (isk < 100000000.0) isk = Math.round10(isk+5000, 4);
  else if (isk < 1000000000.0) isk = Math.round10(isk+50000, 5);
  else if (isk < 10000000000.0) isk = Math.round10(isk+500000, 6);
  else if (isk < 100000000000.0) isk = Math.round10(isk+5000000, 7);
  else isk = null;
  return isk;
}
//-----------
// работа с локальным хранилищем
//-----------
function setOption(grp, opt, val) {
 var o = grp+':'+opt;
 ls.setItem(o, val);
}
function resetOptionToDefault(grp, opt, def) {
 var o = grp+':'+opt;
 if (!ls.getItem(o)) ls.setItem(o, def);
}
function getOption(grp, opt) { // for checkboxes
 var o = grp+':'+opt;
 val = (ls.getItem(o) == 1) ? 1 : 0;
 return val;
}
function getOptionValue(grp, opt) { // for strings and numbers
 var o = grp+':'+opt;
 var val = ls.getItem(o);
 return (val === null) ? '' : val;
}
//function isMenuActivated(btn){
// return btn.hasClass('qind-btn-active');
//}
function toggleMenuMarker(btn, show){
 if(show){
  btn.addClass('qind-btn-active');
  btn.find('span').removeClass('hidden');
 }else{
  btn.removeClass('qind-btn-active');
  btn.find('span').addClass('hidden');
 }
}
function toggleSortMarkers(mode){
 $('button.qind-btn-sort').each(function() {
  if ($(this).attr('qind-group') == mode)
   $(this).addClass('active');
  else
   $(this).removeClass('active');
 });
}
function rebuildOptionsMenu() {
 $('a.qind-btn-settings').each(function() {
  var opt = $(this).attr('qind-group');
  toggleMenuMarker($(this), getOption('option', opt));
 });
 toggleSortMarkers(getOptionValue('sort', 'mode'));
}
//-----------
//работа с видимостью контейнеров (групп по приоритетам)
//-----------
function conveyorTagToStr(row) {
 var tag = row.data('tag');
 if (tag === undefined) return;
 return tag.p+'_'+tag.a.join('_');
}
function toggleConveyorVisibility(btn, hide) {
 var tr = btn.parent().parent();
 var tag = conveyorTagToStr(tr);
 //-
 var icon = btn.find('span');
 if (hide === undefined) {
  var already_hidden = icon.hasClass('glyphicon-eye-close') == true;
  hide = already_hidden == false;
 }
 if (hide == false) {
  setOption('conveyor', tag, 0); // 0 = show
  icon.removeClass('glyphicon-eye-close');
  icon.addClass('glyphicon-eye-open');
  btn.removeClass('qind-btn-hide-close');
  btn.addClass('qind-btn-hide-open');
 } else {
  setOption('conveyor', tag, 1); // 1 = hide
  icon.removeClass('glyphicon-eye-open');
  icon.addClass('glyphicon-eye-close');
  btn.removeClass('qind-btn-hide-open');
  btn.addClass('qind-btn-hide-close');
 }
 rebuildBody();
}
function initConveyorVisibility() {
 $('.qind-btn-hide').each(function() {
  var tr = $(this).parent().parent();
  var tag = conveyorTagToStr(tr);
  var hide = getOption('conveyor', tag) == 1;
  toggleConveyorVisibility($(this), hide);
 });
}
//-----------
//работа с динамическим содержимым страницы
//-----------
function getMaterialImg(tid, sz) {
 return '<img class="icn'+sz+'" src="'+g_tbl_stock_img_src.replace("{tid}", tid)+'">';
}
function getMaterialText(choose, q, na, nm) {
 if (choose == false) {
  if (na > 0)
   return q+' нет '+na;
  else
   return q;
 }
 if (na == 0)
  return nm+' <b>x'+q+'</b>';
 else if (q == na)
  return nm+' <b>x'+q+'</b> (нет в наличии)';
 else
  return nm+' <b>x'+q+'</b> (нет '+na+')';
}
function initMaterialNames() {
 $('table.tbl-stock tbody tr td qnm').each(function() {
  var data_tid = $(this).data('tid');
  if (!(data_tid === undefined)) {
   var nm = getSdeItemName(data_tid);
   if (!(nm === null)) $(this).replaceWith(nm);
   else $(this).replaceWith(data_tid);
  }
 });
 $('table.tbl-stock tbody tr td qimg24').each(function() {
  var data_tid = $(this).data('tid');
  if (!(data_tid === undefined)) {
   $(this).replaceWith(getMaterialImg(data_tid, 24));
  }
 });
 $('table.tbl-stock tbody tr td qmaterial').each(function() {
  var tid = $(this).attr('tid');
  var icn = $(this).attr('icn');
  var cl = $(this).attr('cl');
  if (!(tid === undefined)) {
   var nm = getSdeItemName(tid);
   if (nm === null) nm = tid;
   if (icn === undefined) icn = 24;
   if (cl === undefined) cl = ''; else cl = ' '+cl;
   s = getMaterialImg(tid, icn)+' '+nm+'&nbsp;<a' +
       ' data-target="#" role="button" data-tid="'+tid+'" class="qind-copy-btn'+cl+'" data-toggle="tooltip"' +
       ' data-original-title="" title=""><span class="glyphicon glyphicon-copy" aria-hidden="true"></span></a>';
   $(this).replaceWith(s);
  }
 });
}
function initMaterialsOfBlueprints(used_materials, not_available) {
 $('table.tbl-summary tbody tr td div qmaterials').each(function() {
  if (!used_materials && !not_available) {
   $(this).html('');
  } else {
   var s = '';
   var data_arr = $(this).data('arr');
   if (!(data_arr === undefined) && !(data_arr === "") && (data_arr.length>0)) {
    for (var i=0; i<data_arr.length; ++i) {
     if (!used_materials && not_available && data_arr[i][2]==0) continue;
     if (s) s += ' ';
     if (data_arr[i][2]>0) s += '<qmat class="absent">'; else s += '<qmat>';
     s += getMaterialImg(data_arr[i][0], 16)+' <txt>'+getMaterialText(false, data_arr[i][1], data_arr[i][2])+'</txt></qmat>';
    }
   }
   $(this).html('<br>'+s); // при изменении откорректируй использование index() ниже
  }
 });
}
function getMaterialInfo(qmat) {
 var qmaterials = qmat.parent();
 if (qmaterials === undefined) return null;
 var data_arr = qmaterials.data('arr');
 if ((data_arr === undefined) || (data_arr === "") || (data_arr.length==0)) return null;
 var idx = qmat.index()-1; // первый <br>
 if (idx >= data_arr.length) return null;
 return data_arr[idx];
}
function chooseMaterial(qmat) {
 var info = getMaterialInfo(qmat);
 if (info === null) return
 var tid = info[0];
 var nm = getSdeItemName(tid);
 if (nm === null) nm = tid;
 var is_choose = qmat.hasClass('choose') == false;
 $('qmaterials qmat').each(function() {
  i = getMaterialInfo($(this));
  if (tid != i[0]) return;
  if (is_choose) {
   $(this).find('txt').html(getMaterialText(true, i[1], i[2], nm));
   $(this).addClass('choose');
  } else {
   $(this).find('txt').html(getMaterialText(false, i[1], i[2]));
   $(this).removeClass('choose');
  }
 });
}
//-----------
//работа с содержимом страницы
//-----------
function changeElemVisibility(el, show){
 if(show)
  el.removeClass('hidden');
 else
  el.addClass('hidden');
}
function rebuildBody() {
 var show_possible = (getOption('option', 'run-possible') == 1) ? 1 : 0;
 var show_impossible = (getOption('option', 'run-impossible') == 1) ? 1 : 0;
 var show_lost = (getOption('option', 'lost-items') == 1) ? 1 : 0;
 var show_phantom = (getOption('option', 'phantom-blueprints') == 1) ? 1 : 0;
 var show_active = (getOption('option', 'job-active') == 1) ? 1 : 0;
 var show_completed = (getOption('option', 'job-completed') == 1) ? 1 : 0;

 var hide_conveyor = 0;
 var rows = $('table.tbl-summary tbody').children('tr');
 for (var i=0,cnt=rows.length;i<cnt;++i) {
  var tr = rows.eq(i);
  if (tr.hasClass('row-conveyor')) {
   var tag = conveyorTagToStr(tr);
   hide_conveyor = (getOption('conveyor', tag) == 1) ? 0 : 1;
  }
  else if (tr.hasClass('row-multiple')) {
   changeElemVisibility(tr, hide_conveyor * (show_possible + show_impossible));
   tr.find('td div').each(function() {
    if ($(this).hasClass('run-possible'))
     changeElemVisibility($(this), hide_conveyor * show_possible);
    else if ($(this).hasClass('run-impossible'))
     changeElemVisibility($(this), hide_conveyor * show_impossible);
    else if ($(this).hasClass('run-optional'))
     changeElemVisibility($(this), hide_conveyor * (show_possible + show_impossible));
   });
  }
  else if (tr.hasClass('row-possible')) {
   changeElemVisibility(tr, hide_conveyor * show_possible);
   tr.find('td div').each(function() {
    if ($(this).hasClass('run-possible'))
     changeElemVisibility($(this), hide_conveyor * show_possible);
   });
  }
  else if (tr.hasClass('row-impossible')) {
   changeElemVisibility(tr, hide_conveyor * show_impossible);
   tr.find('td div').each(function() {
    if ($(this).hasClass('run-impossible'))
     changeElemVisibility($(this), hide_conveyor * show_impossible);
   });
  }
  else if (tr.hasClass('row-optional')) {
   changeElemVisibility(tr, hide_conveyor * (show_possible + show_impossible));
   tr.find('td div').each(function() {
    if ($(this).hasClass('run-optional'))
     changeElemVisibility($(this), hide_conveyor * (show_possible + show_impossible));
   });
  }
  else if (tr.hasClass('lost-blueprints') || tr.hasClass('lost-assets') || tr.hasClass('lost-jobs'))
   changeElemVisibility(tr, show_lost); // если потеряшки включены, то они отображаются всегда
  else if (tr.hasClass('phantom-blueprints'))
   changeElemVisibility(tr, hide_conveyor * show_phantom);
  else if (tr.hasClass('job-active'))
   changeElemVisibility(tr, hide_conveyor * show_active);
  else if (tr.hasClass('job-completed'))
   changeElemVisibility(tr, hide_conveyor * show_completed);
 }

 var used_materials = (getOption('option', 'used-materials') == 1) ? 1 : 0;
 var not_available = (getOption('option', 'not-available') == 1) ? 1 : 0;
 initMaterialsOfBlueprints(used_materials, not_available);

 var show_endlvl_manuf = (getOption('option', 'end-level-manuf') == 1) ? 1 : 0;
 var show_entry_purch = (getOption('option', 'entry-level-purchasing') == 1) ? 1 : 0;
 var show_interm_manuf = (getOption('option', 'intermediate-manuf') == 1) ? 1 : 0;
}
//-----------
// обработчики нажатий на кнопки
//-----------
$('a.qind-btn-settings').on('click', function () {
 var opt = $(this).attr('qind-group');
 var val = (getOption('option', opt) == 1) ? 0 : 1;
 setOption('option', opt, val);
 if (opt == 'used-materials') {
  if (val == 1)
    setOption('option', 'not-available', 0);
 }
 else if (opt == 'not-available') {
  if (val == 1)
   setOption('option', 'used-materials', 0);
 }
 rebuildOptionsMenu();
 rebuildBody();
});
//---
$('button.qind-btn-sort').on('click', function () {
 var mode = $(this).attr('qind-group');
 setOption('sort', 'mode', mode);
 rebuildOptionsMenu();
 rebuildBody();
});
//---
function formatTime(sec) {
  const seconds = Math.floor(Math.abs(sec));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.round(seconds % 60);
  const t = [h, m > 9 ? m : h ? '0' + m : m || '0', s > 9 ? s : '0' + s]
    .filter(Boolean)
    .join(':');
  return sec < 0 && seconds ? `-${t}` : t;
}
function recalcLifetimeTimestamps() {
 var now = new Date();
 var utc = new Date(now.getTime() + now.getTimezoneOffset() * 60000);
 let js_ts = Math.floor(utc / 1000); // browser time
 let js_offset = js_ts - g_server_time;
 var s = now.toISOString();
 s = s.replace('T',' ').replace('Z','');
 $('#browser-time').html(s);
 $('table.tbl-lifetime * left').each(function() {
  var data_ts = $(this).data('ts');
  var data_w = $(this).data('w');
  if (!(data_ts === undefined) && !(data_w === undefined)) {
   var left_ts = 0 + (g_server_time - data_ts) + js_offset;
   if (data_w == 'a' || data_w == 'b')
    left_ts = 3600 - left_ts;
   else if (data_w == 'o')
    left_ts = 1200 - left_ts;
   else if (data_w == 'j')
    left_ts = 300 - left_ts;
   if (Math.abs(left_ts) >= 86400)
    $(this).html('');
   else
    $(this).html(formatTime(left_ts));
  }
 });
}
//-----------
// работа с пунктами меню
//-----------
function resetOptionsMenuToDefault() {
 for (let i = 0; i < g_menu_options_default_len; ++i) {
  var show = g_menu_options_default[i][0] ? 1 : 0;
  var opt = g_menu_options_default[i][1];
  resetOptionToDefault('option', opt, show);
 }
 resetOptionToDefault('sort', 'mode', g_menu_sort_default);
}
//-----------
// работа с буфером обмена
//-----------
function copyToClipboard(elem, data_copy) {
 var $temp = $("<textarea>");
 $("body").append($temp);
 $temp.val(data_copy).select();
 try {
  success = document.execCommand("copy");
  if (success) {
   elem.trigger('copied', ['Copied!']);
  }
 } finally {
  $temp.remove();
 }
}
//-----------
// работа с буфером обмена (больше вариантов вода)
//-----------
function doCopyToClipboard(elem) {
 // ожидаем либо data-tid="type_id"; либо data-copy="some value"; либо data-source="table"; либо data-source="span"
 var data_tid = elem.data('tid');
 if (!(data_tid === undefined)) {
  var nm = getSdeItemName(data_tid);
  if (!(nm === null)) copyToClipboard(elem, nm);
  else copyToClipboard(elem, data_tid);
  return;
 }
 var data_copy = elem.data('copy');
 if (!(data_copy === undefined)) {
  copyToClipboard(elem, data_copy);
  return;
 }
 data_copy = '';
 var data_source = elem.data('source');
 if (data_source == 'table') {
  var tr = elem.parent().parent();
  var tbody = tr.parent();
  var rows = tbody.children('tr');
  var start_row = rows.index(tr);
  rows.each( function(idx) {
   var tr = $(this);
   if (!(start_row === undefined) && (idx > start_row)) {
    var td = tr.find('td').eq(0);
    if (!(td.attr('class') === undefined))
     start_row = undefined;
    else {
     var q1 = tr.find('td').eq(1).data('q'); q1 = (q1==undefined)?0:parseInt(q1,10);
     var q2 = tr.find('td').eq(2).data('q'); q2 = (q2==undefined)?0:parseInt(q2,10);
     var qq = q1 + q2;
     if (qq == 0) return;
     if (data_copy) data_copy += "\\n";
     data_copy += td.data('nm') + "\\t" + qq;
    }
   }
  });
 } else if (data_source == 'span') {
  var div = elem.parent().find('div.qind-tid');
  if (!(div === undefined)) {
   var tids = div.children('tid');
   if (!(tids === undefined)) {
    tids.each( function(idx) {
     var tid = $(this);
     if (data_copy) data_copy += "\\n";
     data_copy += getSdeItemName(tid.data('tid')) + "\\t" + tid.data('q');
    });
   }
  }
 }
 if (data_copy) copyToClipboard(elem, data_copy);
}

$(document).ready(function(){
  $('#qind-btn-reset').on('click', function () {
    ls.clear();
    resetOptionsMenuToDefault();
    rebuildOptionsMenu();
    initConveyorVisibility();
    rebuildBody();
  });
  // first init
  resetOptionsMenuToDefault();
  rebuildOptionsMenu();
  initConveyorVisibility();
  rebuildBody();
  //rebuildStocksDropdown();
  //rebuildStockMaterials();
  // init popover menus
  //initPopoverMenus();
  $('body').delegate('qmat', 'click', function () {
   chooseMaterial($(this));
  });
  $('.qind-btn-hide').bind('click', function () {
   toggleConveyorVisibility($(this));
  });
  // Working with clipboard
  $('a.qind-copy-btn').each(function() {
    $(this).tooltip();
  });
  $('body').delegate('a.qind-copy-btn', 'click', function () {
    doCopyToClipboard($(this));
  });
  $('#modalLifetime').on('shown.bs.modal', function () {
   recalcLifetimeTimestamps();
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
  // Delayed and low priority operations
  initMaterialNames();
});
