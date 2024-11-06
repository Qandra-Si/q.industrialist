"""Contains all shared OAuth 2.0 flow functions

This module contains all shared functions between the two different OAuth 2.0
flows recommended for web based and mobile/desktop applications. The functions
found here are used by the OAuth 2.0 contained in this project.

See https://github.com/esi/esi-docs
"""
import ssl
import typing
import urllib
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl
import sys
import base64
import hashlib
import secrets
import time
#import datetime
from dateutil.parser import parse as parsedate

from .auth_cache import EveESIAuth
from .error import EveOnlineClientError


class EveESIClient:
    class TLSAdapter(requests.adapters.HTTPAdapter):
        def __init__(self, ssl_options=0, **kwargs):
            self.ssl_options = ssl_options
            super(EveESIClient.TLSAdapter, self).__init__(**kwargs)

        def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
            ctx = ssl.create_default_context()
            ctx.maximum_version = ssl.TLSVersion.TLSv1_2
            ctx.options = self.ssl_options
            self.poolmanager = PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_context=ctx,
                **pool_kwargs)

    def __init__(self,
                 auth_cache,
                 client_id: str,
                 keep_alive: bool,
                 debug: bool = False,
                 logger: bool = True,
                 user_agent=None,
                 restrict_tls13: bool = False):
        """ constructor

        :param EveESIAuth auth_cache: authz tokens storage
        :param debug: flag which says that we are in debug mode
        :param logger: flag which says that we are in logger mode
        """
        self.__client_callback_url: str = 'https://localhost/callback/'
        # self.__eve_server: str = 'tranquility'  # eveonline' server
        self.__login_host: str = 'login.eveonline.com'
        self.__base_auth_url: str = 'https://login.eveonline.com/v2/oauth/authorize/'
        self.__token_req_url: str = 'https://login.eveonline.com/v2/oauth/token'
        self.__attempts_to_reconnect: int = 5
        self.__debug: bool = debug
        self.__logger: bool = logger

        # экземпляр объекта, кеширующий аутентификационные токену и хранящий их в указанной директории
        if not isinstance(auth_cache, EveESIAuth):
            raise EveOnlineClientError("You should use EveESIAuth to configure client")
        self.__auth_cache = auth_cache

        # для корректной работы с ESI Swagger Interface следует указать User-Agent в заголовках запросов
        self.__user_agent = user_agent

        # данные-состояния, которые были получены во время обработки http-запросов
        self.__last_modified = None

        # резервируем session-объект, для того чтобы не заниматься переподключениями, а пользоваться keep-alive
        self.__keep_alive: bool = keep_alive
        self.__restrict_tls13: bool = restrict_tls13
        self.__session = None
        self.__adapter: typing.Optional[EveESIClient.TLSAdapter] = None

    def __del__(self):
        # закрываем сессию
        if self.__session is not None:
            del self.__session
        if self.__adapter is not None:
            del self.__adapter

    @property
    def auth_cache(self):
        """ authz tokens storage
        """
        return self.__auth_cache

    @property
    def client_callback_url(self):
        """ url to send back authorization code
        """
        return self.__client_callback_url

    def setup_client_callback_url(self, client_callback_url):
        self.__client_callback_url = client_callback_url

    @property
    def debug(self):
        """ flag which says that we are in debug mode
        """
        return self.__debug

    def enable_debug(self):
        self.__debug = True

    def disable_debug(self):
        self.__debug = False

    @property
    def logger(self):
        """ flag which says that we are in logger mode
        """
        return self.__logger

    def enable_logger(self):
        self.__logger = True

    def disable_logger(self):
        self.__logger = False

    @property
    def user_agent(self):
        """ User-Agent which used in http requests to CCP Servers
        """
        return self.__user_agent

    def setup_user_agent(self, user_agent):
        """ configures User-Agent which used in http requests to CCP Servers, foe example:
        'https://github.com/Qandra-Si/ Maintainer: Qandra Si qandra.si@gmail.com'

        :param user_agent: format recomendation - '<project_url> Maintainer: <maintainer_name> <maintainer_email>'
        """
        self.__user_agent = user_agent

    @property
    def last_modified(self):
        """ Last-Modified property from http header
        :returns: :class:`datetime.datetime`
        """
        return self.__last_modified

    @staticmethod
    def __combine_client_scopes(scopes):
        return " ".join(scopes)

    def __establish(self) -> requests.Session:
        if self.__session is not None:
            del self.__session
        if self.__adapter is not None:
            del self.__adapter
        if self.__logger:
            print("starting new HTTPS connection: {}:443".format(self.__login_host))
        self.__session = requests.Session()
        if self.__restrict_tls13:
            self.__adapter = EveESIClient.TLSAdapter(ssl.OP_NO_TLSv1_3)
            self.__session.mount("https://", self.__adapter)
        return self.__session

    def __keep_connection(self) -> requests.Session:
        if self.__session is None:
            self.__session = requests.Session()
            if self.__restrict_tls13:
                self.__adapter = EveESIClient.TLSAdapter(ssl.OP_NO_TLSv1_3)
                self.__session.mount("https://", self.__adapter)
        return self.__session

    def __print_auth_url(self, client_id, client_scopes, code_challenge=None):
        """Prints the URL to redirect users to.

        :param client_id: the client ID of an EVE SSO application
        :param code_challenge: a PKCE code challenge
        """
        params = {
            "response_type": "code",
            "redirect_uri": self.__client_callback_url,
            "client_id": client_id,
            "scope": self.__combine_client_scopes(client_scopes),
            "state": "unique-state"
        }

        if code_challenge:
            params.update({
                "code_challenge": code_challenge,
                "code_challenge_method": "S256"
            })

        string_params = urllib.parse.urlencode(params)
        full_auth_url = "{}?{}".format(self.__base_auth_url, string_params)

        print("\nOpen the following link in your browser:\n\n {} \n\n Once you "
              "have logged in as a character you will get redirected to "
              "{}.".format(full_auth_url, self.__client_callback_url))

    def __send_token_request(self, client_id: str, auth_code: str, app_secret: str):
        """Sends a request for an authorization token to the EVE SSO.

        :param form_values: a dict containing the form encoded values that should be sent with the request
        :param add_headers: a dict containing additional headers to send
        :returns: requests.Response: A requests Response object
        """

        user_pass = "{}:{}".format(client_id, app_secret)
        basic_auth = base64.urlsafe_b64encode(user_pass.encode('utf-8')).decode()
        auth_header: str = "Basic {}".format(basic_auth)

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": self.__login_host,
            "Authorization": auth_header,
        }

        # if self.__user_agent:
        #     headers.update({"User-Agent": self.__user_agent})

        # code_verifier = random

        # интерфейс авторизации устарел: https://developers.eveonline.com/blog/article/sso-endpoint-deprecations-2
        form_encoded_values = {
            "grant_type": "authorization_code",
            "code": auth_code,
            # "client_id": client_id,
            # "code_verifier": code_verifier,
        }

        if self.__keep_alive:
            s: requests.Session = self.__establish()  # s может меняться, важно переиспользовать self.__session
            res = s.post(self.__token_req_url, data=form_encoded_values, headers=headers)
        else:
            res = requests.post(self.__token_req_url, data=form_encoded_values, headers=headers)

        if self.__debug:
            print("Request sent to URL {} with headers {} and form values: "
                  "{}, {}\n".format(res.url, headers, client_id, auth_code))
        res.raise_for_status()

        return res

    def __send_token_refresh(self, refresh_token, client_id, client_scopes=None):
        headers = {
            "Content-Type": 'application/x-www-form-urlencoded',
            "Host": self.__login_host}
        if self.__user_agent:
            headers.update({"User-Agent": self.__user_agent})
        form_values = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id
        }
        if not (client_scopes is None) and len(client_scopes) > 0:
            form_values.update({
                "scope": self.__combine_client_scopes(client_scopes)  # OPTIONAL
            })

        if self.__keep_alive:
            s: requests.Session = self.__establish()  # s может меняться, важно переиспользовать self.__session
            res = s.post(self.__token_req_url, data=form_values, headers=headers)
        else:
            res = requests.post(self.__token_req_url, data=form_values, headers=headers)

        if self.__debug:
            print("Request sent to URL {} with headers {} and form values: "
                  "{}\n".format(res.url, headers, form_values))
        res.raise_for_status()

        return res

    def send_esi_request_http(self, uri, etag, body=None):
        headers = {
            "Authorization": "Bearer {}".format(self.__auth_cache.access_token),
        }
        if not (etag is None) and (body is None):
            headers.update({"If-None-Match": etag})
        if self.__user_agent:
            headers.update({"User-Agent": self.__user_agent})

        res = None
        http_connection_times = 0
        self.__last_modified = None
        requests_get_times = 0
        timeout_connect = 3
        timeout_read = 7
        while True:
            try:
                proxy_error_times = 0
                throttle_error_times = 0
                while True:
                    if body is None:
                        requests_get_finished = False
                        while not requests_get_finished:
                            try:
                                # при попытке загружать рыночные данные (их и только их) начинает зависать
                                # метод get, и висит бесконечно - добавил таймауты на переподключения, которые
                                # подобрал экспериментально, см. также https://ru.stackoverflow.com/a/1189363
                                requests_get_times += 1
                                if self.__keep_alive:
                                    # s может меняться, важно переиспользовать self.__session
                                    s: requests.Session = self.__keep_connection()
                                    res = s.get(uri, headers=headers, timeout=(timeout_connect, timeout_read))
                                else:
                                    res = requests.get(uri, headers=headers, timeout=(timeout_connect, timeout_read))
                            except (requests.ConnectionError, requests.Timeout):
                                continue
                            else:
                                requests_get_finished = True
                        if self.__debug:
                            print("\nMade GET request to {} with headers: "
                                  "{}\nAnd the answer {} was received with "
                                  "headers {} and encoding {}".
                                  format(uri,
                                         res.request.headers,
                                         res.status_code,
                                         res.headers,
                                         res.encoding))
                    else:
                        headers.update({"Content-Type": "application/json"})
                        if self.__keep_alive:
                            # s может меняться, важно переиспользовать self.__session
                            s: requests.Session = self.__keep_connection()
                            res = s.post(uri, data=body, headers=headers)
                        else:
                            res = requests.post(uri, data=body, headers=headers)
                        if self.__debug:
                            print("\nMade POST request to {} with data {} and headers: "
                                  "{}\nAnd the answer {} was received with "
                                  "headers {} and encoding {}".
                                  format(uri,
                                         body,
                                         res.request.headers,
                                         res.status_code,
                                         res.headers,
                                         res.encoding))
                    # вывод отладочной информации : код, uri, last-modified, etag
                    if self.__logger:
                        log_line = str(res.status_code) + " " + uri[31:]
                        if 'Last-Modified' in res.headers:
                            url_time = str(res.headers['Last-Modified'])
                            self.__last_modified = parsedate(url_time)
                            log_line += " " + url_time[17:-4]
                        if 'Etag' in res.headers:
                            etag = str(res.headers['Etag'])
                            log_line += " " + etag[:9] + '"'
                        if requests_get_times > 1:
                            log_line += " (" + str(requests_get_times) + ")"
                        print(log_line)
                    if res.status_code == 401:
                        print(res.json())
                        # переаутентификация
                        self.re_auth(self.__auth_cache.auth_cache["scope"])
                        headers.update({"Authorization": "Bearer {}".format(self.__auth_cache.access_token)})
                        sys.stdout.flush()
                        continue
                    elif (res.status_code in [502, 504]) and (proxy_error_times < self.__attempts_to_reconnect):
                        # пять раз пытаемся повторить отправку сломанного запроса (часто случается
                        # при подключении через 3G-модем)
                        proxy_error_times = proxy_error_times + 1
                        continue
                    elif (res.status_code in [503]) and (proxy_error_times < self.__attempts_to_reconnect):
                        # иногда падает интерфейс к серверу tranquility (почему-то как правило на загрузке
                        # item-ов контракта)
                        print(res.json())
                        # 503 Server Error: service unavailable for url:
                        #     https://esi.evetech.net/latest/corporations/?/contracts/?/items/
                        # {'error': 'The datasource tranquility is temporarily unavailable'}
                        proxy_error_times = proxy_error_times + 1
                        time.sleep(2*proxy_error_times)
                        continue
                    elif (res.status_code in [520]) and (throttle_error_times < self.__attempts_to_reconnect):
                        # возможная ситация: сервер детектирует спам-запросы (на гитхабе написано, что порог
                        # срабатывания находится около 20 запросов в 10 секунд от одного персонажа), см. подробнее
                        # здесь: https://github.com/esi/esi-issues/issues/636#issuecomment-342150532
                        print(res.json())
                        # 520 Server Error: status code 520 for url:
                        #     https://esi.evetech.net/latest/corporations/?/contracts/?/items/
                        # {'error': 'ConStopSpamming, details: {"remainingTime": 12038505}'}
                        throttle_error_times = throttle_error_times + 1
                        time.sleep(5)
                        continue
                    res.raise_for_status()
                    break
            except requests.exceptions.ConnectionError as err:
                print(err)
                # возможная ситуация: наблюдаются проблемы с доступом к серверам CCP (обычно в те же самые
                # моменты, когда падают чаты...), возникает следующая ошибка:
                # HTTPSConnectionPool(host='esi.evetech.net', port=443):
                # Max retries exceeded with url: /latest/corporations/98615601/contracts/162519958/items/
                # Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7f948ecea780>:
                # Failed to establish a new connection: [Errno -3] Temporary failure in name resolution')
                if http_connection_times < self.__attempts_to_reconnect:
                    # повторям попытку подключения спустя секунду
                    http_connection_times += 1
                    time.sleep(1)
                    continue
                raise
            except requests.exceptions.HTTPError as err:
                # встречаются ошибки типа: 403 Client Error: Forbidden for url:
                #     https://esi.evetech.net/latest/corporations/98615601/contracts/163946879/items/
                # {'error': 'token is expired', 'sso_status': 200}
                if (res.status_code == 403) and (res.json().get('error', {'error': ''}) == 'token is expired'):
                    print(res.json())
                    # переаутентификация
                    self.re_auth(self.__auth_cache.auth_cache["scope"])
                    headers.update({"Authorization": "Bearer {}".format(self.__auth_cache.access_token)})
                    sys.stdout.flush()
                    continue
                # сюда попадают 403 и 404 ошибки, и это нормально, т.к. CCP использует их для передачи
                # application-информации
                print(err)
                print(res.json())
                raise
            except:
                print(sys.exc_info())
                raise
            break
        return res

    def send_esi_request_json(self, uri, etag, body=None):
        return self.send_esi_request_http(uri, etag, body).json()

    @staticmethod
    def __print_sso_failure(sso_response):
        print("\nSomething went wrong! Here's some debug info to help you out:")
        print("\nSent request with url: {} \nbody: {} \nheaders: {}".format(
            sso_response.request.url,
            sso_response.request.body,
            sso_response.request.headers
        ))
        print("\nSSO response code is: {}".format(sso_response.status_code))
        print("\nSSO response JSON is: {}".format(sso_response.json()))

    def auth(self, client_scopes, client_id: typing.Optional[str] = None):
        print("Follow the prompts and enter the info asked for.")

        # Generate the PKCE code challenge
        # не используется: random = base64.urlsafe_b64encode(secrets.token_bytes(32))
        # не используется: m = hashlib.sha256()
        # не используется: m.update(random)
        # не используется: d = m.digest()
        # не используется: code_challenge = base64.urlsafe_b64encode(d).decode().replace("=", "")

        if not client_id:
            client_id = input("Copy your SSO application's client ID and enter it "
                              "here [press 'Enter' for default Q.Industrialist app]: ")

        # Because this is a desktop/mobile application, you should use
        # the PKCE protocol when contacting the EVE SSO. In this case, that
        # means sending a base 64 encoded sha256 hashed 32 byte string
        # called a code challenge. This 32 byte string should be ephemeral
        # and never stored anywhere. The code challenge string generated for
        # this program is ${random} and the hashed code challenge is ${code_challenge}.
        # Notice that the query parameter of the following URL will contain this
        # code challenge.

        self.__print_auth_url(client_id, client_scopes)  # не используется: , code_challenge=code_challenge)

        auth_code = input("Copy the \"code\" query parameter and enter it here: ")
        app_secret = input("Copy your SSO application's secret key and enter it here: ")

        # Because this is using PCKE protocol, your application never has
        # to share its secret key with the SSO. Instead, this next request
        # will send the base 64 encoded unhashed value of the code
        # challenge, called the code verifier, in the request body so EVE's
        # SSO knows your application was not tampered with since the start
        # of this process. The code verifier generated for this program is
        # ${code_verifier} derived from the raw string ${random}

        sso_auth_response = self.__send_token_request(client_id, auth_code, app_secret)

        if sso_auth_response.status_code == 200:
            data = sso_auth_response.json()
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]
            auth_cache_data = self.__auth_cache.make_cache(access_token, refresh_token)
            return auth_cache_data
        else:
            self.__print_sso_failure(sso_auth_response)
            sys.exit(1)

    def re_auth(self, client_scopes, auth_cache_data=None):
        if auth_cache_data is None:
            auth_cache_data = self.__auth_cache.auth_cache
        refresh_token = self.__auth_cache.auth_cache["refresh_token"]
        client_id = self.__auth_cache.auth_cache["client_id"]

        sso_auth_response = self.__send_token_refresh(refresh_token, client_id, client_scopes)

        if sso_auth_response.status_code == 200:
            data = sso_auth_response.json()
            self.__auth_cache.refresh_cache(data["access_token"], data["refresh_token"], data["expires_in"])
            return auth_cache_data
        else:
            self.__print_sso_failure(sso_auth_response)
            sys.exit(1)
