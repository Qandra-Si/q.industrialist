const minutes_to_actualize_hubs_stat = 360;

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
 resetOptionToDefault('Show Jita Price', 1);
 resetOptionToDefault('Show Amarr Price', 1);
 resetOptionToDefault('Show Universe Price', 1);
 resetOptionToDefault('Show Market Volume', 1);
 resetOptionToDefault('Show Best Offer', 1);
 resetOptionToDefault('Show Only Our Orders', 0);
}
function rebuildOptionsMenu() {
 displayOptionInMenu('Show Jita Price', $('#imgShowJitaPrice'));
 displayOptionInMenu('Show Amarr Price', $('#imgShowAmarrPrice'));
 displayOptionInMenu('Show Universe Price', $('#imgShowUniversePrice'));
 displayOptionInMenu('Show Market Volume', $('#imgShowMarketVolume'));
 displayOptionInMenu('Show Best Offer', $('#imgShowBestOffer'));
 var show = ls.getItem('Show Market Volume');
 if (show==1)
  $('#btnToggleBestOffer').parent().removeClass('disabled');
 else
  $('#btnToggleBestOffer').parent().addClass('disabled');
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

function onlyUnique(value, index, array) {
  return array.indexOf(value) === index;
}

function refreshMarketHubDetails(minutes) {
 //- отправка запроса на формирование таблицы торговых хабов
 //$("#tblCorpAssets tbody").html('');
 var frm = $("#frmMarketHubDetails");
 frm.find("input[name='min']").val(minutes);
 frm.submit();
}

function refreshCorpAssets(type_id) {
 //- отправка запроса на формирование таблица корпоративного имущества
 $("#tblCorpAssets tbody").html('');
 var corps = [];
 for (const h of g_market_hubs) {
  if (h === null) break;
  if (h[7]==1) continue; //archive
  if (h[8]==1) continue; //forbidden
  corps.push(h[1]);
 }
 corps = corps.filter(onlyUnique);
 var frm = $("#frmCorpAssets");
 frm.find("input[name='corp']").val(corps.join(',')); // мб. список
 frm.find("input[name='tid']").val(type_id); // мб. список
 frm.submit();
}

function refreshMarketOrdersAndHistory(type_id, hub, corp) {
 setOption('Selected Market Hub', hub);
 setOption('Selected Trader Corp', corp);
 for (const h of g_market_hubs) {
  if (h[0] != hub) continue;
  if (h[1] != corp) continue;
  $('#dtlsSelMarketHub ul').find('li').each(function() {
   var li = $(this);
   if ((li.attr('hub') == hub) && (li.attr('corp')))
    li.addClass('active');
   else
    li.removeClass('active');
  });
  break;
 }
 //- отправка запроса на формирование таблицы текущий маркет-ордеров
 $("#tblMarketOrders tbody").html('');
 var frm = $("#frmMarketOrders");
 frm.find("input[name='corp']").val(corp); // мб. список
 frm.find("input[name='hub']").val(hub);
 frm.find("input[name='tid']").val(type_id);
 frm.submit();
 //- отправка запроса на формирование таблицы текущий маркет-ордеров
 $("#tblMarketHistory tbody").html('');
 /*var*/ frm = $("#frmMarketHistory");
 frm.find("input[name='corp']").val(corp); // мб. список
 frm.find("input[name='hub']").val(hub);
 frm.find("input[name='tid']").val(type_id);
 frm.submit();
}

function fillMarketHubsTable(tbody,active) {
 tbody.html();
 var rows = '';
 for (const h of g_market_hubs) {
  if (h === null) break;
  if (active==1) {
   if (h[7]==1) continue; //archive
   if (h[8]==1) continue; //forbidden
  } else {
   if ((h[7]==0) && (h[8]==0)) continue; //active
  }
  var fee = h[2];
  var tax = h[3];
  var margin = h[4];
  rows=rows+
   '<tr id="hub'+h[0]+'_co'+h[1]+'">'+
   '<td style="white-space: nowrap;">'+h[11]+'<br>'+
    '<grayed>'+h[10]+' ('+h[0]+')</grayed>'+
   '</td>'+
   '<td></td>';
  if (eveUserNumber(h[0])) rows=rows+'<td>0.5</td>'; else rows=rows+'<td></td>';
  rows=rows+'<td>'+Math.round10(fee*100.0,-2)+'</td>'+
   '<td>'+Math.round10(tax*100.0,-1)+'</td>'+
   '<td>'+Math.round10(margin*100.0,-1)+'</td>'+
   '<td>';
  if (!(h[12]===null)) rows=rows+numLikeEve(h[12]);
  if (!(h[13]===null)) rows=rows+'<br>'+numLikeEve(h[13]);
  rows=rows+
   '</td>';
  if (h[14]===null) rows=rows+'<td></td>';
  else rows=rows+'<td><a href="'+h[14]+'" target="_blank" class="url">в '+h[9]+'</a><br><a href="'+h[15]+'" target="_blank" class="url">из '+h[9]+'</a></td>';
  rows=rows+'</tr>';
 }
 tbody.html(rows);
}
function showMarketHubsModal() {
 var modal = $("#modalMarketHubs");
 $('#modalMarketHubsLabel').html('<span class="text-primary">Торговые хабы</span> информация');
 fillMarketHubsTable($("#tblHubs tbody"),1);
 fillMarketHubsTable($("#tblArchiveHubs tbody"),0);
 //- отправка запроса на получение подробной информации о торговых хабах
 refreshMarketHubDetails(minutes_to_actualize_hubs_stat);
 modal.modal('show');
}

$("#frmMarketOrders").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/etho_ecor.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){
   var tbody = '';
   $(data).each(function(i,row) {
    var tr = "";
    var corp_remain = (row.corp === undefined)?'':row.corp;
    var buy = row.sell === undefined;
    var bg; var cl;
    if (row.corp === undefined) {
      bg = (buy?'#742929':'#234a19') + '80';
      cl = '#9a9a9a';
    } else {
      bg = buy?'#9f3131':'#1f284d';
      cl = '#fff';
    }
    if (buy)
     tr = "<tr style='color:"+cl+";background:"+bg+"'><td>"+corp_remain+"</td><td>"+row.volume+"</td><td>"+row.buy+"</td><td></td><td></td></tr>";
    else
     tr = "<tr style='color:"+cl+";background:"+bg+"'><td></td><td></td><td>"+row.sell+"</td><td>"+row.volume+"</td><td>"+corp_remain+"</td></tr>";
    tbody += tr;
   });
   var tbl = $("#tblMarketOrders tbody");
   tbl.html(tbody);
   /* как дождаться прорисовки tbody?!
   $("#tblMarketOrders").parent().scrollTop(0);
   //-- scroll
   var rows = $("#tblMarketOrders thead tr");
   if (!(rows === undefined) && (rows.length == 1)) { // на всякий случай
     var tbl_head_px = rows[0].offsetHeight;
     rows = $("#tblMarketOrders tbody tr");
     if (!(rows === undefined) && (rows.length > 0)) { // вдруг содержимое таблицы пусто?
       var px = rows[1].offsetHeight; // высота строки
       var tbody_px = 300 - tbl_head_px;
       if ((px > 0) && ((tbody_px / rows.length) < px)) { // если вся таблица не влезла в tblMarketOrders-wrapper=300px, то скроллируем её к середине
         var split = row_buy_idx * px;
         alert(tbody_px + ' ' + px + ' ' + ' ' + rows.length + ' ' + split);
         if ((tbody_px/2) < split) {
   $("#tblMarketOrders").parent().scrollTop(split);
         }
       }
     }
   }
   */
  },
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

$("#frmMarketHistory").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/ethh.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){
   var tbody = '';
   $(data).each(function(i,row) {
    tr = '';
    if (!(row.date == undefined)) {
      tr = "<tr style='color:#c5c5c5;background-color:#242427;'><td colspan='7' style='padding-left:10px;'><b>"+row.date+"</b></td></tr>";
    }
    var buy = row.sell === undefined;
    var bg; var cl;
    if (row.corp === undefined) {
      bg = (buy?'#742929':'#234a19') + '80';
      cl = '#9a9a9a';
    } else {
      bg = buy?'#9f3131':'#1f284d';
      cl = '#fff';
    }
    var volume = '';
    if (row.closed) {
      if (row.volume == row.total)
        volume = row.volume;
      else
        volume = row.volume+'&hellip;<span style="color:gray;">'+row.total+'</span>';
    } else if (row.volume > 0)
      volume = row.volume;
    var closed = row.closed?'<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>':'';
    if (buy)
     tr += "<tr style='color:"+cl+";background:"+bg+"'><td>"+closed+"</td><td>"+volume+"</td><td>"+row.buy+"</td><td></td><td></td><td>"+row.duration+"</td></tr>";
    else
     tr += "<tr style='color:"+cl+";background:"+bg+"'><td></td><td></td><td>"+row.sell+"</td><td>"+volume+"</td><td>"+closed+"</td><td>"+row.duration+"</td></tr>";
    tbody += tr;
   });
   var tbl = $("#tblMarketHistory tbody");
   tbl.html(tbody);
  },
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

$("#frmCorpAssets").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/eca.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){
   var tbody = '';
   $(data).each(function(i,row) {
    var tr="<tr>"+
     "<td>"+(row.nm ?? '')+"</td>"+
     "<td>"+(row.lnm ?? '')+" <span class='text-primary'>"+row.lfl+"</span> <grayed>("+row.lid+")</grayed>"+"</td>"+
     "<td>"+numLikeEve(row.qty)+"</td>"+
     "<td>"+row.cat+"</td>"+
     "<td>"+row.uat+"</td>"+
    "</tr>";
    tbody += tr;
   });
   var tbl = $("#tblCorpAssets tbody");
   tbl.html(tbody);
  },
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

$("#frmMarketHubDetails").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/mh_ech_eco_ethp_etho.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){
  $(data).each(function(i,row) {
    var tr = $('#hub'+row.hub+'_co'+row.co);
    var td1 = tr.find('td:nth-child(1)');
    var td2 = tr.find('td:nth-child(2)');
    var td1_html = '<br>'+row.cnm+' <grayed>('+row.co+')</grayed>';
    if (!(row.tr === undefined)) td1_html = td1_html + '<br><grayed>Пилот:</grayed> '+row.tnm+' <grayed>('+row.tr+')</grayed>';
    var td2_html = '';
    if (!(row.uat === undefined)) td2_html = td2_html + row.uat;
    if (!(row.ok === undefined)) td2_html = td2_html + '<br><grayed>Ордера:</grayed> '+numLikeEve(row.ok);
    if (!(row.oc === undefined)) td2_html = td2_html + '<br><grayed>'+minutes_to_actualize_hubs_stat+'мин:</grayed> '+numLikeEve(row.oc);
    td1.html(td1.html()+td1_html);
    td2.html(td2_html);
   });
  },
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
 applyOptionVal(show, 'market-volume');
 if (show) {
  /*var*/ show = ls.getItem('Show Best Offer');
  applyOptionVal(show, 'best-offer');
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

$(document).ready(function(){
 $('#btnToggleJitaPrice').on('click', function () { toggleMenuOption('Show Jita Price'); });
 $('#btnToggleAmarrPrice').on('click', function () { toggleMenuOption('Show Amarr Price'); });
 $('#btnToggleUniversePrice').on('click', function () { toggleMenuOption('Show Universe Price'); });
 $('#btnToggleMarketVolume').on('click', function () { toggleMenuOption('Show Market Volume'); });
 $('#btnToggleBestOffer').on('click', function () { toggleMenuOption('Show Best Offer'); });
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

 $('#btnShowMarketHubs').click(function(e) { showMarketHubsModal(); });

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
 $('a.qind-info-btn').bind('click', function() {
  var tr = $(this).closest('tr');
  if (tr.attr('type_id') === undefined) return;
  var type_id = tr.attr('type_id');
  var tid = null;
  for (const t of g_main_data) {
   if (t === null) break;
   if (t[0] != type_id) continue;
   tid = t;
   break;
  }
  if (tid === null) return;
  $('#dtlsTypeId').html(type_id);
  $('#copyTypeId').attr('data-copy', type_id);
  //- отправка запроса на формирование таблицы текущий маркет-ордеров
  //- отправка запроса на формирование таблицы текущий маркет-ордеров
  var hub = getOption('Selected Market Hub', 60003760);
  var corp = getOption('Selected Trader Corp', 98553333);
  refreshMarketOrdersAndHistory(type_id, hub, corp);
  //- отправка запроса на формирование таблица корпоративного имущества
  refreshCorpAssets(type_id);
  //- формирование содержимого диалогового окна
  var modal = $("#modalDetails");
  $('#modalDetailsLabel').html('<span class="text-primary">'+tid[1]+'</span> информация');
  if (tid[12]) {
    $('#dtlsJitaSell')
     .html(numLikeEve(tid[12].toFixed(2)))
     .parent().removeClass('hidden');
    $('#copyJitaSell').attr('data-copy', numLikeEve(tid[12].toFixed(2)));
  } else {
    $('#dtlsJitaSell')
     .closest('div').addClass('hidden');
  }
  if (tid[13]) {
    $('#dtlsJitaBuy')
     .html(numLikeEve(tid[13].toFixed(2)))
     .parent().removeClass('hidden');
    $('#copyJitaBuy').attr('data-copy', numLikeEve(tid[13].toFixed(2)));
  } else {
    $('#dtlsJitaBuy')
     .closest('div').addClass('hidden');
  }
  if (tid[14]) {
    $('#dtlsAmarrSell')
     .html(numLikeEve(tid[14].toFixed(2)))
     .parent().removeClass('hidden');
    $('#copyamarrSell').attr('data-copy', numLikeEve(tid[14].toFixed(2)));
  } else {
    $('#dtlsAmarrSell')
     .closest('div').addClass('hidden');
  }
  if (tid[15]) {
    $('#dtlsAmarrBuy')
     .html(numLikeEve(tid[15].toFixed(2)))
     .parent().removeClass('hidden');
    $('#copyAmarrBuy').attr('data-copy', numLikeEve(tid[15].toFixed(2)));
  } else {
    $('#dtlsAmarrBuy')
     .closest('div').addClass('hidden');
  }
  if (tid[16]) {
    $('#dtlsUniversePrice')
     .html(numLikeEve(tid[16].toFixed(2)))
     .parent().removeClass('hidden');
    $('#copyUniversePrice').attr('data-copy', numLikeEve(tid[16].toFixed(2)));
  } else {
    $('#dtlsUniversePrice')
     .closest('div').addClass('hidden');
  }
  if (tid[5]) {
    $('#dtlsBasePrice')
     .html(numLikeEve(tid[5].toFixed(2)))
     .parent().removeClass('hidden');
    $('#copyBasePrice').attr('data-copy', numLikeEve(tid[5].toFixed(2)));
  } else {
    $('#dtlsBasePrice')
     .closest('div').addClass('hidden');
  }
  if (tid[2] == tid[3])
    $('#dtlsVolume').html('<mark>'+numLikeEve(tid[2]+'</mark> m³'));
  else
    $('#dtlsVolume').html('<mark>'+numLikeEve(tid[2])+'</mark> m³ (в упакованном виде <mark>'+numLikeEve(tid[3])+'</mark> m³)');
  $('#dtlsCapacity').html(numLikeEve(tid[4]));
  $('#dtlsMarketGroupId').html(tid[6]);
  $('#dtlsGroupId').html(tid[7]);
  if (tid[8])
    $('#dtlsMetaGroupId').html(tid[8]).parent().removeClass('hidden');
  else
    $('#dtlsMetaGroupId').closest('div').addClass('hidden');
  if (tid[9])
    $('#dtlsTechLevelId').html(tid[9]).parent().removeClass('hidden');
  else
    $('#dtlsTechLevelId').closest('div').addClass('hidden');
  $('#dtlsPublished').html(tid[10]?'да':'нет');
  if (tid[11])
    $('#dtlsCreatedAt').html(tid[11]).parent().removeClass('hidden');
  else
    $('#dtlsCreatedAt').closest('div').addClass('hidden');
  modal.modal('show');
 });
});
