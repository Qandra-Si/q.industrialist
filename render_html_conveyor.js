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
// работа с пунктами меню
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
 var show_lost = (getOption('option', 'lost-blueprints') == 1) ? 1 : 0;
 var show_phantom = (getOption('option', 'phantom-blueprints') == 1) ? 1 : 0;
 var show_active = (getOption('option', 'job-active') == 1) ? 1 : 0;
 var show_completed = (getOption('option', 'job-completed') == 1) ? 1 : 0;

 $('tr.row-multiple').each(function() {
  changeElemVisibility($(this), show_possible + show_impossible);
 });
 $('tr.row-possible').each(function() {
  changeElemVisibility($(this), show_possible);
 });
 $('div.run-possible').each(function() {
  changeElemVisibility($(this), show_possible);
 });
 $('tr.row-impossible').each(function() {
  changeElemVisibility($(this), show_impossible);
 });
 $('div.run-impossible').each(function() {
  changeElemVisibility($(this), show_impossible);
 });
 $('tr.lost-blueprints').each(function() {
  changeElemVisibility($(this), show_lost);
 });
 $('tr.phantom-blueprints').each(function() {
  changeElemVisibility($(this), show_phantom);
 });
 $('tr.job-active').each(function() {
  changeElemVisibility($(this), show_active);
 });
 $('tr.job-completed').each(function() {
  changeElemVisibility($(this), show_completed);
 });

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
    rebuildBody();
  });
  // first init
  resetOptionsMenuToDefault();
  rebuildOptionsMenu();
  rebuildBody();
  //rebuildStocksDropdown();
  //rebuildStockMaterials();
  // init popover menus
  //initPopoverMenus();
  // Working with clipboard
  $('a.qind-copy-btn').each(function() {
    $(this).tooltip();
  });
  $('a.qind-copy-btn').bind('click', function () {
    doCopyToClipboard($(this));
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
