import json

import q_industrialist_settings


def get_debug_f_name(f_name):
    f_name = '{dir}/.debug_{nm}.json'.format(dir=q_industrialist_settings.g_tmp_directory, nm=f_name)
    return f_name


def dump_json_into_file(nm, data):
    f_name = get_debug_f_name(nm)
    s = json.dumps(data, indent=1, sort_keys=False)
    with open(f_name, 'wt+', encoding='utf8') as f:
        try:
            f.write(s)
        finally:
            f.close()
    return


def take_json_from_file(nm):
    f_name = get_debug_f_name(nm)
    with open(f_name, 'r', encoding='utf8') as f:
        try:
            s = f.read()
            json_data = (json.loads(s))
            return json_data
        finally:
            f.close()
    return None
