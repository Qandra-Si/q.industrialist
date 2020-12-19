import sys
import getopt

import q_capital_settings
import render_html


def __dump_index(glf):
    glf.write("""
<div class="well center-block" style="max-width: 400px;">
  <a href="accounting.html" class="btn btn-primary btn-lg btn-block" role="button">Accounting</a>
  <a href="blueprints.html" class="btn btn-primary btn-lg btn-block" role="button">Blueprints</a>
  <a href="conveyor.html" class="btn btn-primary btn-lg btn-block" role="button">Conveyor</a>
  <a href="cynonetwork.html" class="btn btn-primary btn-lg btn-block" role="button">Cyno Network</a>
  <div class="btn-group btn-block">
    <a href="industry.html" class="btn btn-primary btn-lg" role="button" style="width:320px;">Industry</a>
    <button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <span class="caret"></span>
      <span class="sr-only">Variants</span>
    </button>
    <ul class="dropdown-menu" style="left:201px;">
      <li><a href="qi_industry.php">Archive</a></li>
    </ul>
  </div>
  <div class="btn-group btn-block">
    <a href="workflow.html" class="btn btn-primary btn-lg" role="button" style="width:320px;">Workflow</a>
    <button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <span class="caret"></span>
      <span class="sr-only">Variants</span>
    </button>
    <ul class="dropdown-menu" style="left:201px;">
      <li><a href="qi_workflow.php">Settings</a></li>
    </ul>
  </div>
""")
    for ro in q_capital_settings.g_report_options:
        glf.write('<a href="{fnm}.html" class="btn btn-primary btn-lg btn-block" role="button">{nm}</a>\n'.
                  format(fnm=render_html.__camel_to_snake(ro['product'], True), nm=ro['product']))
    glf.write("""
</div>
""")


def main():
    exit_or_wrong_getopt = None
    workspace_cache_files_dir = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "cache_dir="])
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2
    if exit_or_wrong_getopt is None:
        for opt, arg in opts:  # noqa
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ("--cache_dir"):
                workspace_cache_files_dir = arg[:-1] if arg[-1:] == '/' else arg
        if workspace_cache_files_dir is None:
            exit_or_wrong_getopt = 0
    if not (exit_or_wrong_getopt is None):
        print('Usage: {app} --cache_dir=/tmp\n'.
            format(app=sys.argv[0]))
        sys.exit(exit_or_wrong_getopt)

    glf = open('{dir}/index.html'.format(dir=workspace_cache_files_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, None)
        __dump_index(glf)
        render_html.__dump_footer(glf, show_generated_datetime=False)
    finally:
        glf.close()
    sys.exit(0)  # code 0, all ok


if __name__ == "__main__":
    main()
