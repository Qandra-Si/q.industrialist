import json
import os
import getopt
import sys
import time

from validate_jwt import validate_eve_jwt

import q_industrialist_settings


g_cache = {}


def read_cache(character_name):
    global g_cache
    f_name = '{dir}/.auth_cache/auth_cache.{pilot}.json'.format(
        dir=q_industrialist_settings.g_tmp_directory,
        pilot=character_name)
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
    f_name = '{dir}/.auth_cache/auth_cache.{pilot}.json'.format(
        dir=q_industrialist_settings.g_tmp_directory,
        pilot=cache["character_name"])
    s = json.dumps(cache, indent=1, sort_keys=False)
    f = open(f_name, "wt+")
    f.write(s)
    f.close()
    return


# intersection of two lists in most simple way
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3


def verify_auth_scope(cache, scope):
    """
    Проверяем: scope должен быть необходимым и достаточным для использования программой
    """
    if len(scope) == 0:
        return True
    if not ("scope" in cache):
        return False
    return intersection(cache["scope"], scope) == scope


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


def main(argv):
    """Manually input an auth token to refresh cache."""

    character_name = None  # for example : Qandra Si
    exit_or_wrong_getopt = None
    try:
        opts, args = getopt.getopt(argv, "hp:", ["help", "pilot="])
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2
    if exit_or_wrong_getopt is None:
        for opt, arg in opts:
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ("-p", "--pilot"):
                character_name = arg
        if character_name is None:
            exit_or_wrong_getopt = 0
    if not (exit_or_wrong_getopt is None):
        print('Usage: ' + os.path.basename(__file__) + ' --pilot=<name>')
        sys.exit(exit_or_wrong_getopt)

    cache = read_cache(character_name)
    print("\nThe previous contents of the cached data are {}".format(cache))

    access_token = input("Enter an access token to validate and cache: ")
    cache.update({"access_token": access_token})
    refresh_token = input("Enter an refresh token to remember: ")
    cache.update({"refresh_token": refresh_token})

    make_cache(access_token, refresh_token)


if __name__ == "__main__":
    main(sys.argv[1:])
