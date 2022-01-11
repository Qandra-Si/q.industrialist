<!doctype html>
<html lang="ru">
<head>
 <meta charset="utf-8">
</head>
<body>
 <script src="https://code.jquery.com/jquery-1.12.4.min.js" integrity="sha384-nvAa0+6Qg9clwYCGGPpDQLVpLNn0fRaROjHqs13t4Ggj3Ez50XnGQqc/r8MhnRDZ" crossorigin="anonymous"></script>

<div class="form_container">
	<div id="message"></div>
	<form id="form">
		<input type="text" name="login">
		<input type="text" name="password">
		<input type="submit" name="send" value="Отправить">
	</form>
</div>

<script>
$("#form").on("submit", function(){
	$.ajax({
		url: 'ecor.php',
		method: 'get',
		dataType: 'html',
		data: $(this).serialize(),
		success: function(data){
            alert(data);
			//$('#message').html(data);
		}
	});
});
</script>

</body>
</html>