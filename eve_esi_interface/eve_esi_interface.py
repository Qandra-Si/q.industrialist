import json
import os.path
from pathlib import Path

import requests

import q_industrialist_settings

from shared_flow import send_esi_request_http


g_cache_dir = ".q_industrialist"
g_server_url = "https://esi.evetech.net/latest/"


def get_cache_dir():
    f_dir = '{dir}/{cache}'.format(dir=q_industrialist_settings.g_tmp_directory, cache=g_cache_dir)
    return f_dir


def get_f_name(url):
    if url[-1:] == '/':
        url = url[:-1]
    url = url.replace('/', '_')
    url = url.replace('=', '-')
    url = url.replace('?', '')
    url = url.replace('&', '.')
    f_name = '{dir}/.cache_{nm}.json'.format(dir=get_cache_dir(), nm=url)
    return f_name


def get_f_name_debug(f_name):
    f_name = '{dir}/.debug_{nm}.json'.format(dir=get_cache_dir(), nm=f_name)
    return f_name


def dump_debug_into_file(nm, data):
    f_name = get_f_name_debug(nm)
    s = json.dumps(data, indent=1, sort_keys=False)
    Path(get_cache_dir()).mkdir(parents=True, exist_ok=True)
    with open(f_name, 'wt+', encoding='utf8') as f:
        try:
            f.write(s)
        finally:
            f.close()
    return


def get_cached_headers(data):
    cached_headers = {}
    if "ETag" in data.headers:
        cached_headers.update({"etag": data.headers["ETag"]})
    if "Date" in data.headers:
        cached_headers.update({"date": data.headers["Date"]})
    if "Expires" in data.headers:
        cached_headers.update({"expires": data.headers["Expires"]})
    if "Last-Modified" in data.headers:
        cached_headers.update({"last-modified": data.headers["Last-Modified"]})
    return cached_headers


def dump_cache_into_file(url, data_headers, data_json):
    f_name = get_f_name(url)
    cache = {"headers": data_headers, "json": data_json}
    s = json.dumps(cache, indent=1, sort_keys=False)
    Path(get_cache_dir()).mkdir(parents=True, exist_ok=True)
    with open(f_name, 'wt+', encoding='utf8') as f:
        try:
            f.write(s)
        finally:
            f.close()
    return


def take_cache_from_file(url):
    f_name = get_f_name(url)
    if os.path.exists(f_name):
        with open(f_name, 'r', encoding='utf8') as f:
            try:
                s = f.read()
                cache_data = (json.loads(s))
                return cache_data
            finally:
                f.close()
    return None


def esi_raise_for_status(code, message):
    rsp = requests.Response()
    rsp.status_code = code
    raise requests.exceptions.HTTPError(message, response=rsp)


def get_esi_data(access_token, url, body=None):
    cached_data = take_cache_from_file(url)
    if q_industrialist_settings.g_offline_mode:
        # Offline mode (выдаёт ранее сохранённый кэшированный набор json-данных)
        if "Http-Error" in cached_data["headers"]:
            code = int(cached_data["headers"]["Http-Error"])
            esi_raise_for_status(
                code,
                '{} Client Error: Offline-cache for url: {}'.format(code, url))
        return cached_data["json"] if "json" in cached_data else None
    else:
        # Online mode (отправляем запрос, сохраняем кеш данных, перепроверяем по ETag обновления)
        data_path = ("{srv}{url}".format(srv=g_server_url, url=url))
        # см. рекомендации по программированию тут https://developers.eveonline.com/blog/article/esi-etag-best-practices
        etag = cached_data["headers"]["etag"] if not (cached_data is None) and ("headers" in cached_data) and (
                "etag" in cached_data["headers"]) else None
        try:
            data = send_esi_request_http(access_token, data_path, etag, body)
            if data.status_code == 304:
                return cached_data["json"] if "json" in cached_data else None
            else:
                dump_cache_into_file(url, get_cached_headers(data), data.json())
                return data.json()
        except requests.exceptions.HTTPError as err:
            status_code = err.response.status_code
            if status_code == 403:  # это нормально, CCP используют 403-ответ для индикации запретов ingame-доступа
                # сохраняем информацию в кеше и выходим с тем же кодом ошибки
                dump_cache_into_file(url, {"Http-Error": 403}, None)
                raise
        else:
            raise


def get_esi_paged_data(access_token, url):
    cached_data = take_cache_from_file(url)
    if q_industrialist_settings.g_offline_mode:
        # Offline mode (выдаёт ранее сохранённый кэшированный набор json-данных)
        return cached_data["json"] if "json" in cached_data else None
    else:
        # Online mode (отправляем запрос, сохраняем кеш данных, перепроверяем по ETag обновления)
        restart = True
        restart_cache = False
        while True:
            if restart:
                page = 1
                match_pages = 0
                all_pages = None
                data_headers = []
                data_json = []
                if restart_cache:
                    cached_data = None
                restart = False
            data_path = ("{srv}{url}?page={page}".format(srv=g_server_url, url=url, page=page))
            # см. рекомендации по программированию тут https://developers.eveonline.com/blog/article/esi-etag-best-practices
            etag = cached_data["headers"][page-1]["etag"] if not (cached_data is None) and ("headers" in cached_data) and (
                    len(cached_data["headers"]) >= page) and ("etag" in cached_data["headers"][page-1]) else None
            page_data = send_esi_request_http(access_token, data_path, etag)
            if page_data.status_code == 304:
                # если известны etag-параметры, то все страницы должны совпасть, тогда набор данных
                # считаем полностью валидным
                match_pages = match_pages + 1
                if 1 == page:
                    all_pages = len(cached_data["headers"])
                    last_modified = cached_data["headers"][page-1]["last-modified"]
            else:
                if match_pages > 0:
                    # если какая-либо страница посреди набора данных не совпала с ранее известным etag, то весь набор
                    # данных будем считать невалидным, а ранее загруженные данные устаревшими полностью
                    page = 1
                    match_pages = 0
                    all_pages = None
                    data_headers = []
                    data_json = []
                    cached_data = None
                    restart = True
                    restart_cache = True
                    continue
                data_headers.append(get_cached_headers(page_data))
                data_json.extend(page_data.json())
                if 1 == page:
                    all_pages = int(page_data.headers["X-Pages"]) if "X-Pages" in page_data.headers else 1
                    last_modified = page_data.headers["Last-Modified"]
                elif (last_modified != page_data.headers["Last-Modified"]) and (
                      all_pages != page_data.headers["X-Pages"]):
                    # если в процессе загрузки данных, изменился last-modified или num-pages у
                    # элемента этого набора, то весь набор признаётся невалидным
                    restart = True
                    restart_cache = True
                    continue
            if page == all_pages:
                break
            page = page + 1
        if 0 == match_pages:
            dump_cache_into_file(url, data_headers, data_json)
            return data_json
        elif len(cached_data["headers"]) == match_pages:
            return cached_data["json"] if "json" in cached_data else None
        else:
            raise
