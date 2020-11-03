import sys
import os
import getopt

import render_html


def __dump_index(glf):
    glf.write("""
<div class="well center-block" style="max-width: 400px;">
  <button type="button" class="btn btn-primary btn-lg btn-block">Accounting</button>
  <button type="button" class="btn btn-primary btn-lg btn-block">Blueprints</button>
  <button type="button" class="btn btn-primary btn-lg btn-block">Conveyor</button>
  <button type="button" class="btn btn-primary btn-lg btn-block">Cyno Network</button>
  <button type="button" class="btn btn-primary btn-lg btn-block">Industry</button>
  <button type="button" class="btn btn-primary btn-lg btn-block">Vanquisher</button>
  <div class="btn-group">
    <button type="button" class="btn btn-primary btn-lg btn-block">Workflow</button>
    <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
    <span class="caret"></span>
    <span class="sr-only">Toggle Dropdown</span>
  </button>
  <ul class="dropdown-menu">
    <li><a href="#">Action</a></li>
    <li><a href="#">Another action</a></li>
    <li><a href="#">Something else here</a></li>
    <li role="separator" class="divider"></li>
    <li><a href="#">Separated link</a></li>
  </ul>
  </div>
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
