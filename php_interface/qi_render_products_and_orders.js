// используется:
//  getOption
//  numLikeEve

function onlyUnique(value, index, array) {
  return array.indexOf(value) === index;
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
  if (h === null) break;
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

function getProductMainData(elem) {
 var tr = elem.closest('tr');
 var type_id = tr.attr('type_id');
 if (type_id === undefined) return;
 var tid = null;
 for (const t of g_main_data) {
  if (t === null) break;
  if (t[0] != type_id) continue;
  tid = t;
  break;
 }
 return tid;
}

 // щелчок по кнопке (i)
function showProductInfoDialog(elem) {
 var tid = getProductMainData(elem);
 if (tid === null) return;
 let type_id = tid[0];
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
   $('#copyAmarrSell').attr('data-copy', numLikeEve(tid[14].toFixed(2)));
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
}
