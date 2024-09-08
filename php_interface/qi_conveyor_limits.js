// Options storage (prepare)
var ls = window.localStorage;
function setOption(opt, val) {
 ls.setItem(opt, val);
}
function getOption(opt, def) {
 var val = ls.getItem(opt);
 if (!val) return def;
 return val;
}
function resetOptionToDefault(opt, def) {
 if (!ls.getItem(opt)) ls.setItem(opt, def);
}
function displayOptionInMenu(opt, img, inverse=false) {
 show = ls.getItem(opt);
 if (show == (inverse?0:1))
  img.removeClass('hidden');
 else
  img.addClass('hidden');
}
function resetOptionsMenuToDefault() {
 resetOptionToDefault('Selected Market Hub', 60003760); // Jita hub
 resetOptionToDefault('Selected Trader Corp', 98553333); // R Strike
 resetOptionToDefault('Show Jita Price', 0);
 resetOptionToDefault('Show Amarr Price', 0);
 resetOptionToDefault('Show Universe Price', 0);
 resetOptionToDefault('Show Market Volume', 0);
 resetOptionToDefault('Show Percent Volume', 0);
 resetOptionToDefault('Show Only Our Orders', 0);
}
function rebuildOptionsMenu() {
 displayOptionInMenu('Show Jita Price', $('#imgShowJitaPrice'));
 displayOptionInMenu('Show Amarr Price', $('#imgShowAmarrPrice'));
 displayOptionInMenu('Show Universe Price', $('#imgShowUniversePrice'));
 displayOptionInMenu('Show Market Volume', $('#imgShowMarketVolume'));
 displayOptionInMenu('Show Percent Volume', $('#imgShowPercentVolume'));
 var show = ls.getItem('Show Market Volume');
 if (show==1)
  $('#btnTogglePercentVolume').parent().removeClass('disabled');
 else
  $('#btnTogglePercentVolume').parent().addClass('disabled');
 displayOptionInMenu('Show Only Our Orders', $('#imgShowOurOrdersOnly'), true);
 displayOptionInMenu('Show Only Our Orders', $('#imgShowTheirOrdersOnly'));

 var hidden_hub_names = [];
 var hidden_hubs = ls.getItem('Hidden Market Hubs');
 if (hidden_hubs)
  hidden_hubs = JSON.parse(hidden_hubs);
 $('a.toggle-hub-option').each(function() {
  const hub = parseInt($(this).attr('hub'));
  var img = $(this).find('span.glyphicon-star');
  if (!(hidden_hubs) || (hidden_hubs.indexOf(hub)==-1))
   img.addClass('hidden');
  else {
   img.removeClass('hidden');
   for (const h of g_market_hubs) {
    if (h === null) break;
    if (h[7]==1) continue; //archive
    if (h[8]==1) continue; //forbidden
    if (h[0]!=hub) continue;
    const nm = h[9];
    hidden_hub_names.push(nm);
    break;
   }
  }
 });
 if (hidden_hub_names.length == 0)
  $('#lbHiddenMarketHubs').html('-');
 else
  $('#lbHiddenMarketHubs').html(hidden_hub_names.join(","));
}
function applyOptionVal(show, selector) {
 $(selector).each(function() { if (show==1) $(this).removeClass('hidden'); else $(this).addClass('hidden'); })
}
function applyOption(option, selector) {
 show = ls.getItem(option);
 applyOptionVal(show, selector);
}

function eveSysNumber(x) { return x <= 2147483647; }
function eveUserNumber(x) { return x > 2147483647; }

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

function getTableHeaderIndex(title) {
 var idx = null;
 $('#tbl thead tr').find('th').each(function() {
  var t = $(this).html();
  t = t.replace(/\s/g, '').replace(/<\/?[^>]+(>|$)/g, "").toLowerCase();
  if (t.localeCompare(title)==0)
   idx = $(this).index();
 });
 return idx;
}

// Options storage (rebuild body components)
function rebuildBody() {
 var idx = getTableHeaderIndex('jitasell..buy');
 if (!(idx === null)) {
  idx++;
  const show = ls.getItem('Show Jita Price');
  applyOptionVal(show, '#tbl thead tr th:nth-child('+idx+')');
  applyOptionVal(show, '#tbl tbody tr td:nth-child('+idx+')');
 }
 /*var*/ idx = getTableHeaderIndex('amarrsell..buy');
 if (!(idx === null)) {
  idx++;
  const show = ls.getItem('Show Amarr Price');
  applyOptionVal(show, '#tbl thead tr th:nth-child('+idx+')');
  applyOptionVal(show, '#tbl tbody tr td:nth-child('+idx+')');
 }
 /*var*/ idx = getTableHeaderIndex('universeprice');
 if (!(idx === null)) {
  idx++;
  const show = ls.getItem('Show Universe Price');
  applyOptionVal(show, '#tbl thead tr th:nth-child('+idx+')');
  applyOptionVal(show, '#tbl tbody tr td:nth-child('+idx+')');
 }
 var show = ls.getItem('Show Market Volume');
 applyOptionVal(show, 'remain-volume');
 if (show) {
  let percent = ls.getItem('Show Percent Volume');
  applyOptionVal((percent==1)?1:0, 'percent-volume');
  applyOptionVal((percent==1)?0:1, 'numeric-volume');
 }
 /*var*/ show = ls.getItem('Show Only Our Orders');
 if (show==0)
  $('their-orders-only').css('opacity','0.1');
 else
  $('their-orders-only').css('opacity','unset');
 var hidden_hubs = ls.getItem('Hidden Market Hubs');
 if (hidden_hubs)
  hidden_hubs = JSON.parse(hidden_hubs);
 var visible_market_hubs_idx = [];
 var hidden_market_hubs_idx = [];
 for (const h of g_market_hubs) {
  if (h === null) break;
  if (h[7]==1) continue; //archive
  if (h[8]==1) continue; //forbidden
  const nm = h[9];
  var idx = getTableHeaderIndex(nm.toLowerCase());
  if (!(idx === null)) {
   idx++;
   if (hidden_hubs && (hidden_hubs.indexOf(h[0])>=0))
    hidden_market_hubs_idx.push(idx);
   else
    visible_market_hubs_idx.push(idx);
  }
 }
 for (const idx of visible_market_hubs_idx) {
  applyOptionVal(1, '#tbl thead tr th:nth-child('+idx+')');
  applyOptionVal(1, '#tbl tbody tr td:nth-child('+idx+')');
 }
 for (const idx of hidden_market_hubs_idx) {
  applyOptionVal(0, '#tbl thead tr th:nth-child('+idx+')');
  applyOptionVal(0, '#tbl tbody tr td:nth-child('+idx+')');
 }
}

// Options menu and submenu setup
function toggleMenuOption(name, inverse=false) {
 show = (ls.getItem(name) == (inverse?0:1)) ? 0 : 1;
 ls.setItem(name, show);
 rebuildOptionsMenu();
 rebuildBody();
}

function editProductLimit(elem) {
 var tid = getProductMainData(elem);
 if (tid === null) return;
 let type_id = tid[0];
 //- сохранение идентификатора продукта в форму
 var frm = $("#frmSetupLimits");
 frm.find("input[name='tid']").val(type_id);
 //- формирование содержимого диалогового окна
 var tr = elem.closest('tr');
 var modal = $("#modalLimits");
 $('#modalLimitsLabel').html('<span class="text-primary">'+tid[1]+'</span> настройки производства');
 for (const h of g_market_hubs) {
  if (h === null) break;
  if (h[7]==1) continue; //archive
  if (h[8]==1) continue; //forbidden
  var ed=$('#navOverstocks div.row[hub='+h[0]+'][corp='+h[1]+'] div input');
  if (ed === undefined) return;
  var td = tr.find('td[hub='+h[0]+']');
  var lv = td.find('limit-volume');
  var found=null;
  if (!(lv === undefined)) {
   let lim = lv.attr('lim');
   if (!(lim === undefined)) found = lim;
  }
  if (found)
   ed.val(found);
  else
   ed.val('');
 }
 modal.modal('show');
}

function submitProductLimit() {
 var frm = $("#frmSetupLimits");
 let type_id = frm.find("input[name='tid']").val(); // см. editProductLimit
 var tr = $('#tbl tbody tr[type_id='+type_id+']');
 if (tr === undefined) return;
 var hubs = [];
 var corps = [];
 var limits = [];
 var common_lim = Number(0);
 for (const h of g_market_hubs) {
  if (h === null) break;
  if (h[7]==1) continue; //archive
  if (h[8]==1) continue; //forbidden
  var found=null;
  var ed=$('#navOverstocks div.row[hub='+h[0]+'][corp='+h[1]+'] div input');
  if (ed === undefined) return;
  var lim=ed.val();
  if (!lim || isNaN(Number(lim)) || (lim <= 0)) lim=null;
  var td = tr.find('td[hub='+h[0]+']');
  var lv = td.find('limit-volume');
  if (!(lv === undefined) && !(lv.html() === undefined)) {
   if (lim) {
    lv.attr('lim', lim);
    lv.html(numLikeEve(lim));
   } else {
    lv.removeAttr('lim');
    lv.html('');
   }
  } else if (lim) {
   td.html('<limit-volume lim="'+lim+'">'+numLikeEve(lim)+'</limit-volume>');
  }
  hubs.push(h[0]);
  corps.push(h[1]);
  if (!lim) limits.push(0); else { limits.push(lim); common_lim += Number(lim); }
 }
 if (common_lim)
  tr.find('td:eq(2)').html(numLikeEve(common_lim));
 else
  tr.find('td:eq(2)').html('');
 //- сохранение настроек в форму
 //var frm = $("#frmSetupLimits");
 //см.выше:frm.find("input[name='tid']").val(type_id);
 frm.find("input[name='hub']").val(hubs.join(',')); // мб. список
 frm.find("input[name='corp']").val(corps.join(',')); // мб. список
 frm.find("input[name='limit']").val(limits.join(',')); // мб. список
 frm.submit();
}

$("#frmSetupLimits").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/cl.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){},
  error: function (jqXHR, exception) {
   if (jqXHR.status === 0) alert('Not connect. Verify Network.');
   else if (jqXHR.status == 404) alert('Requested page not found (404).');
   else if (jqXHR.status == 500) alert('Internal Server Error (500).');
   else if (exception === 'parsererror') alert('Requested JSON parse failed.'); // некорректный ввод post-params => return в .php, нет данных
   else if (exception === 'timeout') alert('Time out error.'); // сервер завис?
   else if (exception === 'abort') alert('Ajax request aborted.');
   else alert('Uncaught Error. ' + jqXHR.responseText);
  }
 });
});

$(document).ready(function(){
 $('#btnToggleJitaPrice').on('click', function () { toggleMenuOption('Show Jita Price'); });
 $('#btnToggleAmarrPrice').on('click', function () { toggleMenuOption('Show Amarr Price'); });
 $('#btnToggleUniversePrice').on('click', function () { toggleMenuOption('Show Universe Price'); });
 $('#btnToggleMarketVolume').on('click', function () { toggleMenuOption('Show Market Volume'); });
 $('#btnTogglePercentVolume').on('click', function () { toggleMenuOption('Show Percent Volume'); });
 $('#btnToggleOurOrdersOnly').on('click', function () { toggleMenuOption('Show Only Our Orders'); });
 $('#btnToggleTheirOrdersOnly').on('click', function () { toggleMenuOption('Show Only Our Orders'); });
 $('#btnResetOptions').on('click', function () {
  ls.clear();
  resetOptionsMenuToDefault();
  rebuildOptionsMenu();
  rebuildBody();
 });
 // first init
 resetOptionsMenuToDefault();
 rebuildOptionsMenu();
 rebuildBody();

 $('.dropdown-submenu a.options-submenu').on("click", function(e){
  $(this).next('ul').toggle();
  e.stopPropagation();
  e.preventDefault();
 });
 $('a.toggle-hub-option').on("click", function(e){
  var hub = parseInt($(this).attr('hub'));
  var hubs = ls.getItem('Hidden Market Hubs');
  if (!(hubs)) {
   hubs = [hub];
  } else {
   hubs = JSON.parse(hubs);
   var idx = hubs.indexOf(hub);
   if (idx == -1)
    hubs.push(hub);
   else
    hubs.splice(idx,1);
  }
  ls.setItem('Hidden Market Hubs', JSON.stringify(hubs));
  rebuildOptionsMenu();
  rebuildBody();
 });

 $('#dtlsSelMarketHub a').click(function(e) {
  e.preventDefault();
  var type_id = $('#copyTypeId').attr('data-copy');
  var li = $(this).closest('li');
  var hub = li.attr('hub');
  var corp = li.attr('corp');
  //- отправка запроса на формирование таблицы текущий маркет-ордеров
  //- отправка запроса на формирование таблицы текущий маркет-ордеров
  refreshMarketOrdersAndHistory(type_id, hub, corp);
 });

 $('#dtlsSelTransferHub a').click(function(e) {
  e.preventDefault();
  var type_id = $('#copyTypeId').attr('data-copy');
  var li = $(this).closest('li');
  var hub = li.attr('hub');
  var corp = li.attr('corp');
  //- отправка запроса на формирование таблицы текущий маркет-ордеров
  //- отправка запроса на формирование таблицы текущий маркет-ордеров
  refreshIndustryProductTransferDetails(type_id, hub, corp);
 });

 // работа с буфером обмена
 if (!( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) )) {
  $('price_normal,price_warning,price_ordinal,price_grayed').each(function() {
   $(this).tooltip();
  });
  $('price_normal,price_warning,price_ordinal,price_grayed').bind('click', function () {
   var data_copy = $(this).html();
   data_copy = data_copy.replace(/\s/g, '').replace(/<\/?[^>]+(>|$)/g, "").toLowerCase();
   doCopyToClpbrd($(this), data_copy);
  });
  $('price_normal,price_warning,price_ordinal,price_grayed').bind('copied', function(event, message) {
   var t = $(this).attr('title', message)
    .tooltip('fixTitle')
    .tooltip('show');
   setTimeout(function() { t.tooltip('destroy'); }, 1500);
  });
 }

 // щелчок по кнопке (i)
 $('a.qind-info-btn').bind('click', function() { showProductInfoDialog($(this)); });
 // щелчок по кнопке (edit)
 $('a.qind-edit-btn').bind('click', function() { editProductLimit($(this)); });
 $('#limSubmit').bind('click', function() { submitProductLimit(); });
});
