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
        del s
        del cache
        del f_name
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
    def __get_merged_pages(cached_data):
        if "json" in cached_data:
            merged = []
            for p in cached_data["json"]:
                merged += p
            return merged
        return None

    @staticmethod
    def __esi_raise_for_status(code, message):
        """ generates HTTPError to emulate 403, 404 exceptions when working in offline mode
        """
        rsp = requests.Response()
        rsp.status_code = code
        raise requests.exceptions.HTTPError(message, response=rsp)

    def get_esi_data(self, url, body=None, fully_trust_cache=False):
        """ performs ESI GET/POST-requests in online mode,
        or returns early retrieved data when working on offline mode

        :param url: EVE Swagger Interface ulr
        :param body: parameters to send to ESI API with POST request
        :param fully_trust_cache: if cache exists, trust it! (filesystem cache priority)
        """
        cached_data = self.__take_cache_from_file(url)
        if not self.__offline_mode and fully_trust_cache and not (cached_data is None) and ("json" in cached_data):
            # иногда возникает ситуация, когда данные по указанному url не закачались (упали с ошибкой), и так
            # и будут вечно восстанавливаться из кеша, - все ошибки обновляем в online-режиме!
            if not ("Http-Error" in cached_data["headers"]):
                return cached_data["json"] if "json" in cached_data else None
        if self.__offline_mode:
            if cached_data is None:
                return None
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
                elif status_code == 404:  # это нормально, CCP используют 404-ответ для индикации "нет данных" ingame-доступа
                    # сохраняем информацию в кеше и выходим с тем же кодом ошибки
                    self.__dump_cache_into_file(url, {"Http-Error": 404}, None)
                    raise
            except:
                raise

    def get_esi_paged_data(self, url, fully_trust_cache=False):
        """ performs ESI GET-request in online mode and loads paginated data,
        or returns early retrieved paginated data when working on offline mode
        """
        cached_data = self.__take_cache_from_file(url)
        if not self.__offline_mode and fully_trust_cache and not (cached_data is None) and ("json" in cached_data):
            # аналогично методу get_esi_data, хотя вроде в этом методе HttpError-ы не ожидаются?!
            if not ("Http-Error" in cached_data["headers"][0]):
                return self.__get_merged_pages(cached_data)
        if self.__offline_mode:
            if cached_data is None:
                return None
            # Offline mode (выдаёт ранее сохранённый кэшированный набор json-данных)
            if "Http-Error" in cached_data["headers"][0]:
                code = int(cached_data["headers"][0]["Http-Error"])
                self.__esi_raise_for_status(
                    code,
                    '{} Client Error: Offline-cache for url: {}'.format(code, url))
            # Offline mode (выдаёт ранее сохранённый кэшированный набор json-данных)
            return self.__get_merged_pages(cached_data)
        else:
            # Online mode (отправляем запрос, сохраняем кеш данных, перепроверяем по ETag обновления)
            restart = True
            restart_cache = False
            diff_pages = 0
            match_pages = 0
            data_headers = []
            data_pages = []
            while True:
                if restart:
                    page = 1
                    diff_pages = 0
                    match_pages = 0
                    all_pages = None
                    if data_headers:
                        del data_headers
                    data_headers = []
                    if data_pages:
                        del data_pages
                    data_pages = []
                    if restart_cache:
                        cached_data = None
                    restart = False
                data_path = ("{srv}{url}?page={page}".format(
                    srv=self.server_url,
                    url=url,
                    page=page))  # noqa
                # см. рекомендации по программированию тут
                #  https://developers.eveonline.com/blog/article/esi-etag-best-practices
                if not (cached_data is None) and \
                   ("headers" in cached_data) and \
                   (len(cached_data["headers"]) >= page) and \
                   ("etag" in cached_data["headers"][page-1]):
                    etag = cached_data["headers"][page-1]["etag"]
                else:
                    etag = None
                # возможна ситуация, когда page=1 считался с кодом 200, причём в кеше имеется
                # page=2, при этом X-Pages=2:
                #   200 corporations/98615601/contracts/?page=1 14:10:23 "3f60dac1..."
                #   304 corporations/98615601/contracts/?page=2 14:10:23 "fb294fda..." (из кеша)
                # в этом случае, если уже встречались 200-коды, то etag не отправляем
                try:
                    page_data = self.__client.send_esi_request_http(data_path, etag)
                except requests.exceptions.HTTPError as err:
                    status_code = err.response.status_code
                    if status_code == 404:  # это нормально, CCP используют 404-ответ для индикации "нет данных" ingame-доступа
                        if 1 == page:
                            # сохраняем информацию в кеше и выходим с тем же кодом ошибки
                            self.__dump_cache_into_file(url, [{"Http-Error": 404}], None)
                        raise
                    raise
                except:
                    raise
                if page_data.status_code == 304:
                    # возможна ситуация, когда etag у первых 3х страниц не меняется несколько суток подряд, тогда
                    # как страницы с 4й по ...20ю (например) меняются часто; такое поведение нередко наблюдается
                    # у corporation/blueprints отчёта, где первые страницы хранят младшие идентификаторы и долгое
                    # время не будут обновлятся потому, что чертежи не используются, лежат к хранилищах
                    # нет никакого смысла проверять только первых 3и страницы, - их надо проверять все, т.к.
                    # изменениям могут быть подвержены часть данных (в середине отчёта)
                    match_pages += 1
                    # если известны etag-параметры, то все страницы должны совпасть, тогда набор данных
                    # считаем полностью валидным
                    if len(data_pages) < page:
                        data_headers.append(cached_data["headers"][page-1])
                        data_pages.append(cached_data["json"][page-1])
                    else:
                        data_headers[page-1] = cached_data["headers"][page-1]
                        data_pages[page-1] = cached_data["json"][page-1]
                    if 1 == page:
                        all_pages = len(cached_data["headers"])
                else:
                    diff_pages += 1
                    # если какая-либо страница посреди набора данных не совпала с ранее известным etag,
                    # то обновляем только её, причём данные по другим страницам продолжаем считать валидными
                    if len(data_pages) < page:
                        data_headers.append(self.__get_cached_headers(page_data))
                        data_pages.append(page_data.json())
                    else:
                        data_headers[page-1] = self.__get_cached_headers(page_data)
                        data_pages[page-1] = page_data.json()
                    if 1 == page:
                        all_pages = int(page_data.headers["X-Pages"]) if "X-Pages" in page_data.headers else 1
                    elif (int(all_pages) != int(page_data.headers["X-Pages"])):  # noqa
                        # если в процессе загрузки данных, изменился last-modified или num-pages у
                        # элемента этого набора, то весь набор признаётся невалидным
                        restart = True
                        restart_cache = True
                        continue
                if page == all_pages:
                    break
                page = page + 1
            if (diff_pages > 0) or (match_pages == 0):
                self.__dump_cache_into_file(url, data_headers, data_pages)
                merged = []
                for p in data_pages:
                    merged += p
                return merged
            elif len(cached_data["headers"]) == match_pages:
                return self.__get_merged_pages(cached_data)
            else:
                print("ERROR! : ", match_pages, diff_pages)
                print("ERROR! : ", cached_data["headers"])
                raise

    def get_esi_piece_data(self, url, body: list, fully_trust_cache=False):
        # Получение названий контейнеров, станций, и т.п. - всё что переименовывается ingame
        piece_data = []
        problem_ids = []
        if body:
            try:
                # Requires role(s): Director
                piece_data = self.get_esi_data(
                    url,
                    json.dumps(body, indent=0, sort_keys=False),
                    fully_trust_cache)
            except requests.exceptions.HTTPError as err:
                status_code = err.response.status_code
                if not self.__offline_mode and (status_code == 404):
                    # изредка бывает так, что corp_assets_data включает в себя id, которые уже удалены, т.е. в ассетах
                    # контейнер ещё есть, а в names уже нет (вот такая печальная ситуация по синхронизации данных у ССР)
                    # какой именно id из сотни возможных оказался "битым" неизвестно, поэтому разбиваем список id по частям
                    # пытаемся их скачать по отдельности
                    # а во время активных мувопсов и перетаскивании ассетов, ситуация усугубляется - множество названий
                    # разом исчезает из списков и подолгу мешает грузить данные (значит будем грузить частями)
                    parted_body = body[:]
                    while parted_body:
                        parted_ids = parted_body[:10]
                        parted_body = parted_body[10:]
                        try:
                            parted_names = self.get_esi_data(
                                url,
                                json.dumps(parted_ids, indent=0, sort_keys=False),
                                False)
                            piece_data.extend(parted_names)
                        except requests.exceptions.HTTPError as err:
                            status_code = err.response.status_code
                            if status_code == 404:
                                for single_id in parted_ids:
                                    try:
                                        single_name = self.get_esi_data(
                                            url,
                                            json.dumps([single_id], indent=0, sort_keys=False),
                                            False)
                                        piece_data.append(single_name[0])
                                    except requests.exceptions.HTTPError as err:
                                        status_code = err.response.status_code
                                        if status_code == 404:
                                            problem_ids.append(single_id)
                                        else:
                                            raise
                            else:
                                raise
                    # после того как все данные успешно загрузились... повторяем!!! операцию чтения, чтобы
                    # кеш с данными был корректно сформирован
                    body = [b for b in body if b not in problem_ids]
                    piece_data = self.get_esi_data(
                        url,
                        json.dumps(body, indent=0, sort_keys=False),
                        fully_trust_cache)
                else:
                    raise
            except:
                raise
        return piece_data

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
