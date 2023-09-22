<?php
include 'qi_render_html.php';
include 'qi_tools_and_utils.php';
include_once '.settings.php';

__dump_header("Praisal", FS_RESOURCES, $html_style);
if (!extension_loaded('pgsql')) return;
?>
<div class="container-fluid">
</div> <!--container-fluid-->
<?php __dump_footer(); ?>
