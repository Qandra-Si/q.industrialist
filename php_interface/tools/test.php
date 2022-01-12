<!doctype html>
<html lang="ru">
<head>
 <meta charset="utf-8">
 <script src="https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous"></script>
</head>
<body>

<div class="form_container">
 <table id="msg"><tbody></tbody></table>
 <form id="form">
  <input type="text" name="corp">
  <input type="text" name="hub">
  <input type="text" name="tid">
  <input type="submit" name="send" value="Получить данные">
 </form>
</div>

<script>
$("#form").on("submit", function(e){
 e.preventDefault();
 $.ajax({
  url: '/tools/etho_ecor.php',
  method: 'post',
  dataType: 'json',
  data: $(this).serialize(),
  success: function(data){
    var tbody = '';
    $.each(data, function() {
      var row = "";
      $.each(this, function(k , v) {
        row += "<td>"+v+"</td>";
      });
      tbody += "<tr>"+row+"</tr>";
    });
    $("#msg tbody").html(tbody);
  },
  error: function (jqXHR, exception) {
    if (jqXHR.status === 0) {
      alert('Not connect. Verify Network.');
    } else if (jqXHR.status == 404) {
      alert('Requested page not found (404).');
    } else if (jqXHR.status == 500) {
      alert('Internal Server Error (500).');
    } else if (exception === 'parsererror') {
      alert('Requested JSON parse failed.'); // некорректный ввод post-params => return в .php, нет данных
    } else if (exception === 'timeout') {
      alert('Time out error.'); // сервер завис?
    } else if (exception === 'abort') {
      alert('Ajax request aborted.');
    } else {
      alert('Uncaught Error. ' + jqXHR.responseText);
    }
  }
  });
});
</script>

</body>
</html>
