﻿//var g_menu_options_default=[[1,"impossible"],[1,"not-available"],[1,"end-level-manuf"],[1,"intermediate-manuf"],[1,"recommended-runs"]];
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
function rebuildBody() {
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
  //rebuildBody();
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
