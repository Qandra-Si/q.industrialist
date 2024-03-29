﻿import sys
import getopt
import typing

import q_capital_settings
import q_market_analyzer_settings
import render_html


def __dump_index(glf):
    glf.write("""
<div class="well center-block" style="max-width: 400px;">
  <a href="accounting.html" class="btn btn-primary btn-lg btn-block" role="button">Accounting</a>
  <a href="blueprints.html" class="btn btn-primary btn-lg btn-block" role="button">Blueprints</a>
  <div class="btn-group btn-block">
    <a href="conveyor.html" class="btn btn-primary btn-lg" role="button" style="width:320px;">Conveyor</a>
    <button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <span class="caret"></span>
      <span class="sr-only">Variants</span>
    </button>
    <ul class="dropdown-menu" style="left:201px;">
      <li><a href="conveyor.html">Malpais</a></li>
      <li><a href="conveyor-querious.html">Querious</a></li>
    </ul>
  </div>
  <a href="router.html" class="btn btn-primary btn-lg btn-block" role="button">Router</a>
  <a href="cynonetwork.html" class="btn btn-primary btn-lg btn-block" role="button">Cyno Network</a>
""")
    if q_market_analyzer_settings.g_regions:
        glf.write("""
  <div class="btn-group btn-block">
""")
        glf.write("<a href='{rfn}.html'".format(rfn=q_market_analyzer_settings.g_report_filename))
        glf.write(""" class="btn btn-primary btn-lg" role="button" style="width:320px;">Markets</a>
    <button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <span class="caret"></span>
      <span class="sr-only">Variants</span>
    </button>
    <ul class="dropdown-menu" style="left:201px;">
""")
        for rg in q_market_analyzer_settings.g_regions:
            glf.write("<li><a href='{rfn}-{fnm}.html'>{nm}</a></li>\n".
                      format(rfn=q_market_analyzer_settings.g_report_filename, fnm=render_html.__camel_to_snake(rg, True), nm=rg))
        glf.write("""
    </ul>
  </div>
""")
    glf.write("""
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
  <div class="btn-group btn-block">
    <a href="regroup.html" class="btn btn-primary btn-lg" role="button" style="width:320px;">Regroup</a>
    <button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <span class="caret"></span>
      <span class="sr-only">Variants</span>
    </button>
    <ul class="dropdown-menu" style="left:201px;">
      <li><a href="qi_regroup.php">Settings</a></li>
    </ul>
  </div>
  <div class="btn-group btn-block">
    <a href="shareholders_r_initiative4.html" class="btn btn-primary btn-lg" role="button" style="width:320px;">Shareholders</a>
    <button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <span class="caret"></span>
      <span class="sr-only">Variants</span>
    </button>
    <ul class="dropdown-menu" style="left:201px;">
      <li><a href="shareholders_r_industry.html">R Industry</a></li>
      <li><a href="shareholders_r_initiative4.html">R Initiative 4</a></li>
      <li><a href="shareholders_r_initiative5.html">R Initiative 5</a></li>
      <li><a href="shareholders_r_strike.html">R Strike</a></li>
      <li><a href="shareholders_night_trade_team.html">Night Trade Team</a></li>
      <li><a href="shareholders_just_a_trade_corp.html">Just A Trade Corp</a></li>
    </ul>
  </div>
""")
    if q_capital_settings.g_night_factory_rest_ships:
        glf.write("""
  <div class="btn-group btn-block">
    <a href="/" class="btn btn-primary btn-lg" role="button" style="width:320px;">Night Factory</a>
    <button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
      <span class="caret"></span>
      <span class="sr-only">Variants</span>
    </button>
    <ul class="dropdown-menu" style="left:201px;">
""")
        ships: typing.List[str] = sorted([s for s in q_capital_settings.g_night_factory_rest_ships])
        for ship in ships:
            glf.write('      <li><a href="{fnm}.html">{s}</a></li>\n'.
                      format(s=ship, fnm=render_html.__camel_to_snake('{s} For Night Factory'.format(s=ship), True)))
        glf.write("""
    </ul>
  </div>
""")

    if q_capital_settings.g_report_options:
        products: typing.List[str] = sorted([p for p in set([ro['product'] for ro in q_capital_settings.g_report_options])])
        for product in products:
            report_options = [ro for ro in q_capital_settings.g_report_options if ro['product'] == product]
            if len(report_options) == 1:
                ro = report_options[0]
                fname: str = ro.get('assignment', ro['product'])
                glf.write('<a href="{fnm}.html" class="btn btn-primary btn-lg btn-block" role="button">{nm}</a>\n'.format(
                    fnm=render_html.__camel_to_snake(fname, True),
                    nm=product
                ))
            else:
                ro_first = report_options[0]
                fname_first: str = ro_first.get('assignment', ro_first['product'])
                glf.write(
                    '<div class="btn-group btn-block">\n'
                    '<a href="{fnm}.html" '
                    'class="btn btn-primary btn-lg" role="button" style="width:320px;">{nm}</a>\n'.
                    format(fnm=render_html.__camel_to_snake(fname_first, True),
                           nm=product,
                ))
                glf.write("""<button type="button" class="btn btn-primary btn-lg dropdown-toggle" style="width:39px; float:right;" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
  <span class="caret"></span>
  <span class="sr-only">Variants</span>
</button>
<ul class="dropdown-menu" style="left:201px;">
""")
                for ro in report_options:
                    fname: str = ro.get('assignment', ro['product'])
                    glf.write(
                        "<li><a href='{fnm}.html'>{nm}</a></li>\n".
                        format(fnm=render_html.__camel_to_snake(fname, True),
                               nm=fname,
                    ))
                glf.write("</ul>\n</div>\n")

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
        # инициализируем корабли Ночного цеха
        #не требуется:q_capital_settings.init_night_factory_rest_ships(q_capital_settings.g_night_factory_rest_ships)
        render_html.__dump_header(glf, None)
        __dump_index(glf)
        render_html.__dump_footer(glf, show_generated_datetime=False)
    finally:
        glf.close()
    sys.exit(0)  # code 0, all ok


if __name__ == "__main__":
    main()
