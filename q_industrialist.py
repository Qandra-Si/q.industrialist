""" Q.Industrialist (desktop/mobile)

Prerequisites:
    * Create an SSO application at developers.eveonline.com with the scope
      "esi-characters.read_blueprints.v1" and the callback URL
      "https://localhost/callback/". Note: never use localhost as a callback
      in released applications.
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.
    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python manipulate_yaml_and_json.py
>>> python q_industrialist.py
"""
import base64
import hashlib
import secrets
import sys
import json

from shared_flow import print_auth_url
from shared_flow import send_token_request
from shared_flow import send_token_refresh
from shared_flow import send_esi_request
from auth_cache import read_cache
from auth_cache import make_cache
from auth_cache import store_cache
from auth_cache import is_timestamp_expired
from auth_cache import get_timestamp_expired
from debug import dump_json_into_file
from render_html import dump_into_report


# R Initiative 4 Q.Industrialist
g_ri4_client_id = "022ea197e3f2414f913b789e016990c8"
g_client_scope = ["esi-characters.read_blueprints.v1",
                  "esi-wallet.read_character_wallet.v1",
                  "esi-assets.read_assets.v1",
                  # "esi-contracts.read_character_contracts.v1",
                  "esi-fittings.read_fittings.v1",
                  "esi-assets.read_corporation_assets.v1",
                  "esi-corporations.read_blueprints.v1",
                  "esi-corporations.read_titles.v1"]


def print_sso_failure(sso_response):
    print("\nSomething went wrong! Here's some debug info to help you out:")
    print("\nSent request with url: {} \nbody: {} \nheaders: {}".format(
        sso_response.request.url,
        sso_response.request.body,
        sso_response.request.headers
    ))
    print("\nSSO response code is: {}".format(sso_response.status_code))
    print("\nSSO response JSON is: {}".format(sso_response.json()))


def auth(client_id=""):
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

    global g_client_scope
    print_auth_url(client_id, g_client_scope, code_challenge=code_challenge)

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
        auth_cache = make_cache(access_token, refresh_token)
        return auth_cache
    else:
        print_sso_failure(sso_auth_response)
        sys.exit(1)

    # handle_sso_token_response(sso_auth_response)


def re_auth(auth_cache):
    refresh_token = auth_cache["refresh_token"]
    client_id = auth_cache["client_id"]

    sso_auth_response = send_token_refresh(refresh_token, client_id, g_client_scope)

    if sso_auth_response.status_code == 200:
        data = sso_auth_response.json()

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        expired = get_timestamp_expired(int(data["expires_in"]))

        auth_cache.update({"access_token": access_token})
        auth_cache.update({"refresh_token": refresh_token})
        auth_cache.update({"expired": expired})
        store_cache(auth_cache)
        return auth_cache
    else:
        print_sso_failure(sso_auth_response)
        sys.exit(1)


def main():
    global g_client_scope
    cache = read_cache()
    if not ('access_token' in cache) or not ('refresh_token' in cache) or (not 'expired' in cache):
        cache = auth()
    elif not ('scope' in cache) or (cache["scope"] != g_client_scope):
        cache = auth(cache["client_id"])
    elif is_timestamp_expired(int(cache["expired"])):
        cache = re_auth(cache)

    access_token = cache["access_token"]
    character_id = cache["character_id"]
    character_name = cache["character_name"]

    character_path = ("https://esi.evetech.net/latest/characters/{}/".format(character_id))
    character_data = send_esi_request(access_token, character_path)
    print("\n{} is from {} corporation".format(character_name, character_data["corporation_id"]))
    sys.stdout.flush()
    dump_json_into_file("character", character_data)

    corporation_id = character_data["corporation_id"]

    blueprint_path = ("https://esi.evetech.net/latest/characters/{}/blueprints/".format(character_id))
    blueprint_data = send_esi_request(access_token, blueprint_path)
    print("\n{} has {} blueprints".format(character_name, len(blueprint_data)))
    sys.stdout.flush()
    dump_json_into_file("blueprints", blueprint_data)

    wallet_path = ("https://esi.evetech.net/latest/characters/{}/wallet/".format(character_id))
    wallet_data = send_esi_request(access_token, wallet_path)
    print("\n{} has {} ISK".format(character_name, wallet_data))
    sys.stdout.flush()
    dump_json_into_file("wallet", wallet_data)

    assets_path = ("https://esi.evetech.net/latest/characters/{}/assets/".format(character_id))
    assets_data = send_esi_request(access_token, assets_path)
    print("\n{} has {} assets".format(character_name, len(assets_data)))
    sys.stdout.flush()
    dump_json_into_file("assets", assets_data)

    corp_assets_path = ("https://esi.evetech.net/latest/corporations/{}/assets/".format(corporation_id))
    corp_assets_data = send_esi_request(access_token, corp_assets_path)
    print("\n{}' corporation has {} assets".format(character_name, len(corp_assets_data)))
    sys.stdout.flush()
    dump_json_into_file("corp_assets", corp_assets_data)

    """contracts_path = ("https://esi.evetech.net/latest/characters/{}/contracts/".format(character_id))
    contracts_data = send_esi_request(access_token, contracts_path)
    print("\n{} has {} contracts".format(character_name, len(contracts_data)))
    sys.stdout.flush()
    dump_json_into_file("contracts", contracts_data)

    contract158928740_path = ("https://esi.evetech.net/latest/characters/{}/contracts/{}/items/".format(character_id, 158928740))
    contract158928740_data = send_esi_request(access_token, contract158928740_path)
    print("\n{} has {} contract158928740".format(character_name, len(contract158928740_data)))
    sys.stdout.flush()
    dump_json_into_file("contract158928740", contract158928740_data)"""

    fittings_path = ("https://esi.evetech.net/latest/characters/{}/fittings/".format(character_id))
    fittings_data = send_esi_request(access_token, fittings_path)
    print("\n{} has {} fittings".format(character_name, len(fittings_data)))
    sys.stdout.flush()
    dump_json_into_file("fittings", fittings_data)

    names_data = []
    for ass in assets_data:
        if ass["type_id"] in [17363,   # Small Audit Log Secure Container
                              17364,   # Medium Audit Log Secure Container
                              17365,   # Large Audit Log Secure Container
                              17366,   # Station Container
                              17367,   # Station Vault Container
                              17368]:  # Station Warehouse Container
            names_data.append(ass["item_id"])
    if len(names_data):
        names_path = ("https://esi.evetech.net/latest/characters/{}/assets/names/".format(character_id))
        names_data = send_esi_request(access_token, names_path, json.dumps(names_data))
        sys.stdout.flush()
        dump_json_into_file("assets_names", names_data)

    dump_into_report(wallet_data, blueprint_data, assets_data, names_data)


if __name__ == "__main__":
    main()
