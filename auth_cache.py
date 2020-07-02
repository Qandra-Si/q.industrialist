import json
import os
import time

from validate_jwt import validate_eve_jwt

import q_industrialist_settings


g_cache = {}


def read_cache():
    global g_cache
    f_name = '{dir}/auth_cache.json'.format(dir=q_industrialist_settings.g_tmp_directory)
    if os.path.isfile(f_name):
        f = open(f_name, "rt")
        s = f.read()
        try:
            g_cache = (json.loads(s))
        except json.decoder.JSONDecodeError as e:
            print("Something went wrong when decoding data stored in auth_cache.json: {}".format(str(e)))
            g_cache = {}
        finally:
            f.close()
    else:
        g_cache = {}
    return g_cache


def is_timestamp_expired(expired):
    current = int(time.time())
    return expired <= current


def get_timestamp_expired(timeout):
    current = int(time.time())
    return current + timeout


def store_cache(cache=g_cache):
    f_name = '{dir}/auth_cache.json'.format(dir=q_industrialist_settings.g_tmp_directory)
    s = json.dumps(cache, indent=1, sort_keys=False)
    f = open(f_name, "wt+")
    f.write(s)
    f.close()
    return


def make_cache(access_token, refresh_token):
    cache = {}
    cache.update({"access_token": access_token})
    cache.update({"refresh_token": refresh_token})

    validated_jwt = validate_eve_jwt(access_token)
    print("\nThe contents of the access token are: {}".format(validated_jwt))

    character_id = validated_jwt["sub"].split(":")[2]
    character_name = validated_jwt["name"]
    expired = validated_jwt["exp"]
    client_id = validated_jwt["azp"]
    scope = validated_jwt["scp"]

    cache.update({"expired": expired,
                  "character_id": character_id,
                  "character_name": character_name,
                  "client_id": client_id,
                  "scope": scope})

    store_cache(cache)
    return cache


def main():
    """Manually input an auth token to refresh cache."""

    cache = read_cache()
    print("\nThe previous contents of the cached data are {}".format(cache))

    access_token = input("Enter an access token to validate and cache: ")
    cache.update({"access_token": access_token})
    refresh_token = input("Enter an refresh token to remember: ")
    cache.update({"refresh_token": refresh_token})

    make_cache(access_token, refresh_token)


if __name__ == "__main__":
    main()