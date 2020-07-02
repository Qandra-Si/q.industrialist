import json
from pathlib import Path

import q_industrialist_settings

from shared_flow import send_esi_request


g_cache_dir = ".q_industrialist"
g_server_url = "https://esi.evetech.net/latest/"


def get_cache_dir():
    f_dir = '{dir}/{cache}'.format(dir=q_industrialist_settings.g_tmp_directory, cache=g_cache_dir)
    return f_dir


def get_f_name(f_name):
    f_name = '{dir}/.debug_{nm}.json'.format(dir=get_cache_dir(), nm=f_name)
    return f_name


def dump_json_into_file(nm, data):
    f_name = get_f_name(nm)
    s = json.dumps(data, indent=1, sort_keys=False)
    Path(get_cache_dir()).mkdir(parents=True, exist_ok=True)
    with open(f_name, 'wt+', encoding='utf8') as f:
        try:
            f.write(s)
        finally:
            f.close()
    return


def take_json_from_file(nm):
    f_name = get_f_name(nm)
    with open(f_name, 'r', encoding='utf8') as f:
        try:
            s = f.read()
            json_data = (json.loads(s))
            return json_data
        finally:
            f.close()
    return None


def get_esi_data(access_token, url, nm, body=None):
    if not q_industrialist_settings.g_offline_mode:
        data_path = ("{srv}{url}".format(srv=g_server_url, url=url))
        data = send_esi_request(access_token, data_path, body)
        dump_json_into_file(nm, data)
    else:
        data = take_json_from_file(nm)
    return data


def get_esi_paged_data(access_token, url, nm):
    if not q_industrialist_settings.g_offline_mode:
        page = 1
        data = []
        while True:
            data_path = ("{srv}{url}?page={page}".format(srv=g_server_url, url=url, page=page))
            page_data = send_esi_request(access_token, data_path)
            page_len = len(page_data)
            if 0 == page_len:
                break
            # dump_json_into_file("{}.part{:03d}".format(nm,page), page_data)
            data.extend(page_data)
            page = page + 1
        dump_json_into_file(nm, data)
    else:
        data = take_json_from_file(nm)
    return data
