import render_html
import eve_sde_tools


def __dump_sde_type_ids_to_js(glf, sde_type_ids):
    type_id_keys = sde_type_ids.keys()
    sorted_type_id_keys = sorted(type_id_keys, key=lambda x: int(x))
    glf.write('<script>\nvar g_sde_max_type_id={max};\nvar g_sde_type_ids=['.format(max=sorted_type_id_keys[-1]))
    for type_id in sorted_type_id_keys:
        # экранируем " (двойные кавычки), т.к. они встречаются реже, чем ' (одинарные кавычки)
        glf.write('{end}[{id},"{nm}"]'.format(
            id=type_id,
            nm=sde_type_ids[str(type_id)]["name"]["en"].replace('"', '\\\"'),
            end="\n" if type_id == "0" else ","))
    glf.write("""
];
function getSdeItemName(id) {
 if ((id < 0) || (id > g_sde_max_type_id)) return null;
 for (var i=0; i<=g_sde_max_type_id; ++i)
  if (id == g_sde_type_ids[i][0])
   return g_sde_type_ids[i][1];
 return null;
};
var nm = getSdeItemName(0);
alert(nm);
var nm = getSdeItemName(3958);
alert(nm);
</script>
""")


def __dump_industrialist_tools(
        glf,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids):
    glf.write("""
<div class="container-fluid">
""")

    glf.write("...")

    glf.write("""
</div> <!--container-fluid-->
""")
    __dump_sde_type_ids_to_js(glf, sde_type_ids)

def dump_industrialist_into_report(
        # путь, где будет сохранён отчёт
        ws_dir,
        # sde данные, загруженные из .converted_xxx.json файлов
        sde_type_ids,
        # esi данные, загруженные с серверов CCP
        corp_assets_data,
        corp_ass_names_data,
        # данные, полученные в результате анализа и перекомпоновки входных списков
        corp_assets_tree):
    glf = open('{dir}/industrialist.html'.format(dir=ws_dir), "wt+", encoding='utf8')
    try:
        render_html.__dump_header(glf, "Workflow")
        __dump_industrialist_tools(
            glf,
            sde_type_ids)
        render_html.__dump_footer(glf)
    finally:
        glf.close()
