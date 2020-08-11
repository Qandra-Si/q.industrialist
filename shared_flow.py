"""Contains all shared OAuth 2.0 flow functions

This module contains all shared functions between the two different OAuth 2.0
flows recommended for web based and mobile/desktop applications. The functions
found here are used by the OAuth 2.0 contained in this project.
"""
import urllib
import requests
import sys
import base64
import hashlib
import secrets

import q_industrialist_settings
import auth_cache


# R Initiative 4 Q.Industrialist
g_ri4_client_id = "022ea197e3f2414f913b789e016990c8"

g_client_callback_url = "https://localhost/callback/"
g_content_type = "application/x-www-form-urlencoded"
g_login_host = "login.eveonline.com"
g_base_auth_url = "https://login.eveonline.com/v2/oauth/authorize/"
g_token_req_url = "https://login.eveonline.com/v2/oauth/token"
g_debug = False


def combine_client_scopes(scopes):
    res = ""
    for scope in scopes:
        if res:
            res = res + " "
        res = res + scope
    return res


def print_auth_url(client_id, client_scopes, code_challenge=None):
    """Prints the URL to redirect users to.

    Args:
        client_id: The client ID of an EVE SSO application
        code_challenge: A PKCE code challenge
    """

    params = {
        "response_type": "code",
        "redirect_uri": g_client_callback_url,
        "client_id": client_id,
        "scope": combine_client_scopes(client_scopes),
        "state": "unique-state"
    }

    if code_challenge:
        params.update({
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        })

    string_params = urllib.parse.urlencode(params)
    full_auth_url = "{}?{}".format(g_base_auth_url, string_params)

    print("\nOpen the following link in your browser:\n\n {} \n\n Once you "
          "have logged in as a character you will get redirected to "
          "{}.".format(full_auth_url, g_client_callback_url))


def send_token_request(form_values, add_headers={}):
    """Sends a request for an authorization token to the EVE SSO.

    Args:
        form_values: A dict containing the form encoded values that should be
                     sent with the request
        add_headers: A dict containing additional headers to send
    Returns:
        requests.Response: A requests Response object
    """

    headers = {
        "Content-Type": g_content_type,
        "Host": g_login_host
    }
    if q_industrialist_settings.g_user_agent:
        headers.update({"User-Agent": q_industrialist_settings.g_user_agent})

    if add_headers:
        headers.update(add_headers)

    res = requests.post(
        g_token_req_url,
        data=form_values,
        headers=headers,
    )

    print("Request sent to URL {} with headers {} and form values: "
          "{}\n".format(res.url, headers, form_values))
    res.raise_for_status()

    return res


def send_token_refresh(refresh_token, client_id, client_scopes=[]):
    headers = {
        "Content-Type": g_content_type,
        "Host": g_login_host,
    }
    if q_industrialist_settings.g_user_agent:
        headers.update({"User-Agent": q_industrialist_settings.g_user_agent})

    form_values = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id
    }
    if len(client_scopes):
        form_values.update({
            "scope": combine_client_scopes(client_scopes)  # OPTIONAL
        })

    res = requests.post(
        g_token_req_url,
        data=form_values,
        headers=headers,
    )

    print("Request sent to URL {} with headers {} and form values: "
          "{}\n".format(res.url, headers, form_values))
    res.raise_for_status()

    return res


def send_esi_request_http(access_token, uri, etag, body=None):
    headers = {
        "Authorization": "Bearer {}".format(access_token),
    }
    if not (etag is None) and (body is None):
        headers.update({"If-None-Match": etag})
    if q_industrialist_settings.g_user_agent:
        headers.update({"User-Agent": q_industrialist_settings.g_user_agent})

    try:
        res = None
        proxy_error_times = 0  # трижды пытаемся повторить отправку сломанного запроса (часто случается при подключении через 3G-модем)
        while True:
            if body is None:
                res = requests.get(uri, headers=headers)
                if g_debug:
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
                res = requests.post(uri, data=body, headers=headers)
                if g_debug:
                    print("\nMade POST request to {} with data {} and headers: "
                          "{}\nAnd the answer {} was received with "
                          "headers {} and encoding {}".
                          format(uri,
                                 body,
                                 res.request.headers,
                                 res.status_code,
                                 res.headers,
                                 res.encoding))
            if (res.status_code in [502,504]) and (proxy_error_times < 3):
                proxy_error_times = proxy_error_times + 1
                continue
            res.raise_for_status()
            break
    except requests.exceptions.HTTPError as err:
        print(err)
        print(res.json())
        raise
    except:
        print(sys.exc_info())
        raise

    debug = str(res.status_code) + " " + uri[31:]
    if ('Last-Modified' in res.headers):
        debug = debug + " " + str(res.headers['Last-Modified'])[17:-4]
    if ('Etag' in res.headers):
        debug = debug + " " + str(res.headers['Etag'])
    print(debug)

    return res


def send_esi_request_json(access_token, uri, etag, body=None):
    return send_esi_request_http(access_token, uri, etag, body).json()


def print_sso_failure(sso_response):
    print("\nSomething went wrong! Here's some debug info to help you out:")
    print("\nSent request with url: {} \nbody: {} \nheaders: {}".format(
        sso_response.request.url,
        sso_response.request.body,
        sso_response.request.headers
    ))
    print("\nSSO response code is: {}".format(sso_response.status_code))
    print("\nSSO response JSON is: {}".format(sso_response.json()))


def auth(client_scopes, client_id=""):
    print("Follow the prompts and enter the info asked for.")

    # Generate the PKCE code challenge
    random = base64.urlsafe_b64encode(secrets.token_bytes(32))
    m = hashlib.sha256()
    m.update(random)
    d = m.digest()
    code_challenge = base64.urlsafe_b64encode(d).decode().replace("=", "")

    if not client_id:
        client_id = input("Copy your SSO application's client ID and enter it "
                          "here [press 'Enter' for R Initiative 4 app]: ")
        if not client_id:
            global g_ri4_client_id
            client_id = g_ri4_client_id

    # Because this is a desktop/mobile application, you should use
    # the PKCE protocol when contacting the EVE SSO. In this case, that
    # means sending a base 64 encoded sha256 hashed 32 byte string
    # called a code challenge. This 32 byte string should be ephemeral
    # and never stored anywhere. The code challenge string generated for
    # this program is ${random} and the hashed code challenge is ${code_challenge}.
    # Notice that the query parameter of the following URL will contain this
    # code challenge.

    print_auth_url(client_id, client_scopes, code_challenge=code_challenge)

    auth_code = input("Copy the \"code\" query parameter and enter it here: ")

    code_verifier = random

    form_values = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": auth_code,
        "code_verifier": code_verifier
    }

    # Because this is using PCKE protocol, your application never has
    # to share its secret key with the SSO. Instead, this next request
    # will send the base 64 encoded unhashed value of the code
    # challenge, called the code verifier, in the request body so EVE's
    # SSO knows your application was not tampered with since the start
    # of this process. The code verifier generated for this program is
    # ${code_verifier} derived from the raw string ${random}

    sso_auth_response = send_token_request(form_values)

    if sso_auth_response.status_code == 200:
        data = sso_auth_response.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        auth_cache_data = auth_cache.make_cache(access_token, refresh_token)
        return auth_cache_data
    else:
        print_sso_failure(sso_auth_response)
        sys.exit(1)

    # handle_sso_token_response(sso_auth_response)


def re_auth(client_scopes, auth_cache_data):
    refresh_token = auth_cache_data["refresh_token"]
    client_id = auth_cache_data["client_id"]

    sso_auth_response = send_token_refresh(refresh_token, client_id, client_scopes)

    if sso_auth_response.status_code == 200:
        data = sso_auth_response.json()

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        expired = auth_cache.get_timestamp_expired(int(data["expires_in"]))

        auth_cache_data.update({"access_token": access_token})
        auth_cache_data.update({"refresh_token": refresh_token})
        auth_cache_data.update({"expired": expired})
        auth_cache.store_cache(auth_cache_data)
        return auth_cache_data
    else:
        print_sso_failure(sso_auth_response)
        sys.exit(1)
