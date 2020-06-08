import json

import q_industrialist_settings


def dump_json_into_file(f_name, data):
    f_name = '{dir}/{nm}'.format(dir=q_industrialist_settings.g_tmp_directory, nm=f_name)
    s = json.dumps(data, indent=1, sort_keys=False)
    f = open(f_name, "wt+")
    f.write(s)
    f.close()
    return
