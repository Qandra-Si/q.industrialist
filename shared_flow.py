"""Contains all shared OAuth 2.0 flow functions

This module contains all shared functions between the two different OAuth 2.0
flows recommended for web based and mobile/desktop applications. The functions
found here are used by the OAuth 2.0 contained in this project.
"""
import urllib

import requests

from validate_jwt import validate_eve_jwt

import q_industrialist_settings


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


# def handle_sso_token_response(sso_response):
#     """Handles the authorization code response from the EVE SSO.
# 
#     Args:
#         sso_response: A requests Response object gotten by calling the EVE
#                       SSO /v2/oauth/token endpoint
#     """
# 
#     if sso_response.status_code == 200:
#         data = sso_response.json()
#         access_token = data["access_token"]
# 
#         print("\nVerifying access token JWT...")
# 
#         jwt = validate_eve_jwt(access_token)
#         character_id = jwt["sub"].split(":")[2]
#         character_name = jwt["name"]
#         blueprint_path = ("https://esi.evetech.net/latest/characters/{}/"
#                           "blueprints/".format(character_id))
# 
#         print("\nSuccess! Here is the payload received from the EVE SSO: {}"
#               "\nYou can use the access_token to make an authenticated "
#               "request to {}".format(data, blueprint_path))
# 
#         input("\nPress any key to have this program make the request for you:")
# 
#         headers = {
#             "Authorization": "Bearer {}".format(access_token)
#         }
# 
#         res = requests.get(blueprint_path, headers=headers)
#         print("\nMade request to {} with headers: "
#               "{}".format(blueprint_path, res.request.headers))
#         res.raise_for_status()
# 
#         data = res.json()
#         print("\n{} has {} blueprints".format(character_name, len(data)))
#     else:
#         print("\nSomething went wrong! Re read the comment at the top of this "
#               "file and make sure you completed all the prerequisites then "
#               "try again. Here's some debug info to help you out:")
#         print("\nSent request with url: {} \nbody: {} \nheaders: {}".format(
#             sso_response.request.url,
#             sso_response.request.body,
#             sso_response.request.headers
#         ))
#         print("\nSSO response code is: {}".format(sso_response.status_code))
#         print("\nSSO response JSON is: {}".format(sso_response.json()))
#     return


def send_esi_request(access_token, uri, body=None):
    headers = {
        "Authorization": "Bearer {}".format(access_token)
    }
    if q_industrialist_settings.g_user_agent:
        headers.update({"User-Agent": q_industrialist_settings.g_user_agent})

    if body is None:
        res = requests.get(uri, headers=headers)
        if g_debug:
            print("\nMade GET request to {} with headers: "
                  "{}".format(uri, res.request.headers))
    else:
        res = requests.post(uri, data=body, headers=headers)
        if g_debug:
            print("\nMade POST request to {} with data {} and headers: "
                  "{}".format(uri, body, res.request.headers))
    res.raise_for_status()

    return res.json()
