// используется: eveUserNumber

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

function refreshMarketHubDetails(minutes) {
 //- отправка запроса на формирование таблицы торговых хабов
 //$("#tblCorpAssets tbody").html('');
 var frm = $("#frmMarketHubDetails");
 frm.find("input[name='min']").val(minutes);
 frm.submit();
}

const minutes_to_actualize_hubs_stat = 360;

function showMarketHubsModal() {
 var modal = $("#modalMarketHubs");
 $('#modalMarketHubsLabel').html('<span class="text-primary">Торговые хабы</span> информация');
 fillMarketHubsTable($("#tblHubs tbody"),1);
 fillMarketHubsTable($("#tblArchiveHubs tbody"),0);
 //- отправка запроса на получение подробной информации о торговых хабах
 refreshMarketHubDetails(minutes_to_actualize_hubs_stat);
 modal.modal('show');
}

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

$(document).ready(function(){
 $('#btnShowMarketHubs').click(function(e) { showMarketHubsModal(); });
});
