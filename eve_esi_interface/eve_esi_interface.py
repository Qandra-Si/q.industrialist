# -*- encoding: utf-8 -*-
import json
import os.path
from pathlib import Path
import requests

from .error import EveOnlineClientError
from .eve_esi_client import EveESIClient


class EveOnlineInterface:
    def __init__(self, client, scopes, cache_dir, offline_mode=False):
        """ constructor

        :param EveOnlineConfig config: configuration of Eve Online Client
        """
        self.__server_url = "https://esi.evetech.net/latest/"
        self.__scopes = scopes
        self.__offline_mode = offline_mode

        self.__cache_dir = cache_dir  # {tmp_dir}/.esi_cache/
        self.setup_cache_dir(cache_dir)

        if not isinstance(client, EveESIClient):
            raise EveOnlineClientError("You should use EveESIClient to configure interface")
        self.__client = client

    @property
    def client(self):
        """ Eve Online ESI Swagger https client implementation
        """
        return self.__client

    @property
    def server_url(self):
        """ url to ESI Swagger interface (CCP' servers)
        """
        return self.__server_url

    @property
    def scopes(self):
        """ Eve Online Application client scopes
        """
        return self.__scopes

    @property
    def cache_dir(self):
        """ path to directory with cache files
        """
        return self.__cache_dir

    def setup_cache_dir(self, cache_dir):
        """ configures path to directory where esi/http cache files stored
        """
        if cache_dir[-1:] == '/':
            cache_dir = cache_dir[:-1]
        self.__cache_dir = cache_dir
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    @property
    def offline_mode(self):
        """ flag which says that we are working offline, so eve_esi_interface will read data from file system
        (to optimize interaction with CCP servers)
        """
        return self.__offline_mode

    @property
    def online_mode(self):
        """ flag which says that we are working offline, so eve_esi_interface will download & save data from CCP servers
        """
        return not self.__offline_mode

    def __get_f_name(self, url):
        """ converts urls to filename to store it in filesystem, for example:
        url=/corporations/98553333/assets/names/
        filename=.cache_corporations_98553333_assets_names.json

        :param url: Eve Online ESI Swagger interface url
        :return: patched url to name of file
        """
        if url[-1:] == '/':
            url = url[:-1]
        url = url.replace('/', '_')
        url = url.replace('=', '-')
        url = url.replace('?', '')
        url = url.replace('&', '.')
        f_name = '{dir}/.cache_{nm}.json'.format(dir=self.__cache_dir, nm=url)
        return f_name

    @staticmethod
    def __get_cached_headers(data):
        """ gets http response headers and converts it data stored on cache files
        """
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

    def __dump_cache_into_file(self, url, data_headers, data_json):
        """ dumps data received from CCP Servers into cache files
        """
        f_name = self.__get_f_name(url)
        cache = {"headers": data_headers, "json": data_json}
        s = json.dumps(cache, indent=1, sort_keys=False)
        with open(f_name, 'wt+', encoding='utf8') as f:
            try:
                f.write(s)
            finally:
                f.close()
        return

    def __take_cache_from_file(self, url):
        """ reads cache data early received from CCP Servers
        """
        f_name = self.__get_f_name(url)
        if os.path.isfile(f_name):
            with open(f_name, 'rt', encoding='utf8') as f:
                try:
                    s = f.read()
                    cache_data = (json.loads(s))
                    return cache_data
                finally:
                    f.close()
        return None

    @staticmethod
    def __esi_raise_for_status(code, message):
        """ generates HTTPError to emulate 403 exceptions when working in offline mode
        """
        rsp = requests.Response()
        rsp.status_code = code
        raise requests.exceptions.HTTPError(message, response=rsp)

    def get_esi_data(self, url, body=None):
        """ performs ESI GET/POST-requests in online mode,
        or returns early retrieved data when working on offline mode
        """
        cached_data = self.__take_cache_from_file(url)
        if self.__offline_mode:
            # Offline mode (выдаёт ранее сохранённый кэшированный набор json-данных)
            if "Http-Error" in cached_data["headers"]:
                code = int(cached_data["headers"]["Http-Error"])
                self.__esi_raise_for_status(
                    code,
                    '{} Client Error: Offline-cache for url: {}'.format(code, url))
            return cached_data["json"] if "json" in cached_data else None
        else:
            # Online mode (отправляем запрос, сохраняем кеш данных, перепроверяем по ETag обновления)
            data_path = ("{srv}{url}".format(srv=self.server_url, url=url))
            # см. рекомендации по программированию тут
            # https://developers.eveonline.com/blog/article/esi-etag-best-practices
            etag = cached_data["headers"]["etag"] if not (cached_data is None) and ("headers" in cached_data) and (
                    "etag" in cached_data["headers"]) else None
            try:
                data = self.__client.send_esi_request_http(data_path, etag, body)
                if data.status_code == 304:
                    return cached_data["json"] if "json" in cached_data else None
                else:
                    self.__dump_cache_into_file(url, self.__get_cached_headers(data), data.json())
                    return data.json()
            except requests.exceptions.HTTPError as err:
                status_code = err.response.status_code
                if status_code == 403:  # это нормально, CCP используют 403-ответ для индикации запретов ingame-доступа
                    # сохраняем информацию в кеше и выходим с тем же кодом ошибки
                    self.__dump_cache_into_file(url, {"Http-Error": 403}, None)
                    raise
            except:
                raise

    def get_esi_paged_data(self, url):
        """ performs ESI GET-request in online mode and loads paginated data,
        or returns early retrieved paginated data when working on offline mode
        """
        cached_data = self.__take_cache_from_file(url)
        if self.__offline_mode:
            # Offline mode (выдаёт ранее сохранённый кэшированный набор json-данных)
            return cached_data["json"] if "json" in cached_data else None
        else:
            # Online mode (отправляем запрос, сохраняем кеш данных, перепроверяем по ETag обновления)
            restart = True
            restart_cache = False
            first_start = True
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
                data_path = ("{srv}{url}?page={page}".format(
                    srv=self.server_url,
                    url=url,
                    page=page))  # noqa
                # см. рекомендации по программированию тут
                #  https://developers.eveonline.com/blog/article/esi-etag-best-practices
                etag = cached_data["headers"][page-1]["etag"] if not (cached_data is None) and ("headers" in cached_data) and (
                        len(cached_data["headers"]) >= page) and ("etag" in cached_data["headers"][page-1]) else None
                page_data = self.__client.send_esi_request_http(data_path, etag)
                if page_data.status_code == 304:
                    # ускоренный вывод данных из этого метода - если находимся в цикле загрузке данных с сервера
                    # и при первом же обращении к первой же странице совпал etag, следовательно весь набор актуален
                    # и заниматься загрузкой остальных страниц (дожидаясь, а может быть на этот раз именно во время
                    # загрузки данные обновятся) - нет никакого смысла! (О) - оптимизация! :)
                    if first_start and 1 == page:
                        return cached_data["json"] if "json" in cached_data else None
                    # если известны etag-параметры, то все страницы должны совпасть, тогда набор данных
                    # считаем полностью валидным
                    match_pages = match_pages + 1  # noqa
                    if 1 == page:
                        all_pages = len(cached_data["headers"])
                        last_modified = cached_data["headers"][page-1]["last-modified"]
                else:
                    if match_pages > 0:  # noqa
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
                        first_start = False
                        continue
                    data_headers.append(self.__get_cached_headers(page_data))  # noqa
                    data_json.extend(page_data.json())  # noqa
                    if 1 == page:
                        all_pages = int(page_data.headers["X-Pages"]) if "X-Pages" in page_data.headers else 1
                        last_modified = page_data.headers["Last-Modified"]
                    elif (last_modified != page_data.headers["Last-Modified"]) and (  # noqa
                          all_pages != page_data.headers["X-Pages"]):  # noqa
                        # если в процессе загрузки данных, изменился last-modified или num-pages у
                        # элемента этого набора, то весь набор признаётся невалидным
                        restart = True
                        restart_cache = True
                        first_start = False
                        continue
                if page == all_pages:
                    break
                page = page + 1
                first_start = False
            if 0 == match_pages:
                self.__dump_cache_into_file(url, data_headers, data_json)
                return data_json
            elif len(cached_data["headers"]) == match_pages:
                return cached_data["json"] if "json" in cached_data else None
            else:
                raise

    def authenticate(self, character_name=None):
        """ Main authenticate method to login character into system

        :param character_name: pilot' name for signin, or None value for signup new pilot into system
        """
        authz = {} if character_name is None else self.__client.auth_cache.read_cache(character_name)
        if not self.__offline_mode:
            if not ('access_token' in authz) or not ('refresh_token' in authz) or not ('expired' in authz):
                authz = self.__client.auth(self.__scopes)
            elif not ('scope' in authz) or not self.__client.auth_cache.verify_auth_scope(authz, self.__scopes):
                authz = self.__client.auth(self.__scopes, authz["client_id"])
            elif self.__client.auth_cache.is_timestamp_expired(int(authz["expired"])):
                authz = self.__client.re_auth(self.__scopes, authz)
        else:
            if not ('access_token' in authz):
                raise EveOnlineClientError("There is no way to continue working offline (you should authorize at least once)")
        return authz
