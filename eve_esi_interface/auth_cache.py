"""Contains all shared OAuth 2.0 flow functions

This module contains all shared functions between the two different OAuth 2.0
flows recommended for web based and mobile/desktop applications. The functions
found here are used by the OAuth 2.0 contained in this project.

See https://github.com/esi/esi-docs
"""
import json
import os
import getopt
import sys
import time
from pathlib import Path

try:
    from .validate_jwt import validate_eve_jwt
except ImportError:  # pragma: no cover
    # to use main() function in this file directly
    from validate_jwt import validate_eve_jwt


class EveESIAuth:
    def __init__(self, cache_dir, debug=False):
        self.__auth_cache = {}
        self.__debug = debug
        self.__cache_dir = cache_dir
        self.setup_cache_dir(cache_dir)  # {tmp_dir}/.auth_cache/

    @property
    def auth_cache(self):
        """ authorization token, stored application scopes, character name and so others
        """
        return self.__auth_cache

    @property
    def character_id(self):
        """ character_id from auth_cache data
        """
        return self.__auth_cache["character_id"]

    @property
    def character_name(self):
        """ character_name from auth_cache data
        """
        return self.__auth_cache["character_name"]

    @property
    def access_token(self):
        """ access_token from auth_cache data
        """
        return self.__auth_cache["access_token"]

    @property
    def cache_dir(self):
        """ path to directory with cache files
        """
        return self.__cache_dir

    def setup_cache_dir(self, cache_dir):
        """ configures path to directory where auth cache files stored
        """
        if cache_dir[-1:] == '/':
            cache_dir = cache_dir[:-1]
        self.__cache_dir = cache_dir
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

    @property
    def debug(self):
        """ flag which says that we are in debug mode
        """
        return self.__debug

    def enable_debug(self):
        self.__debug = True

    def disable_debug(self):
        self.__debug = False

    def __get_f_name(self, character_name):
        f_name = '{dir}/auth_cache.{pilot}.json'.format(dir=self.__cache_dir, pilot=character_name)
        return f_name

    def read_cache(self, character_name):
        f_name = self.__get_f_name(character_name)
        if os.path.isfile(f_name):
            with open(f_name, 'rt', encoding='utf8') as f:
                try:
                    s = f.read()
                    self.__auth_cache = (json.loads(s))
                except json.decoder.JSONDecodeError as e:
                    print("Something went wrong when decoding data stored in auth_cache.json: {}".format(str(e)))
                    self.__auth_cache = {}
                finally:
                    f.close()
        else:
            self.__auth_cache = {}
        return self.__auth_cache

    @staticmethod
    def is_timestamp_expired(expired):
        current = int(time.time())
        return expired <= current

    @staticmethod
    def __get_timestamp_expired(timeout):
        current = int(time.time())
        return current + timeout

    def __store_cache(self):
        f_name = self.__get_f_name(self.__auth_cache["character_name"])
        s = json.dumps(self.__auth_cache, indent=1, sort_keys=False)
        with open(f_name, 'wt+', encoding='utf8') as f:
            try:
                f.write(s)
            finally:
                f.close()
        return

    def refresh_cache(self, access_token, refresh_token, expires_in):
        expired = self.__get_timestamp_expired(int(expires_in))
        self.__auth_cache.update({"access_token": access_token})
        self.__auth_cache.update({"refresh_token": refresh_token})
        self.__auth_cache.update({"expired": expired})
        self.__store_cache()

    @staticmethod
    def __intersection(lst1, lst2):
        """ intersection of two lists in most simple way
        """
        lst3 = [value for value in lst1 if value in lst2]
        return lst3

    @staticmethod
    def verify_auth_scope(auth_cache, scope):
        """ Проверяем: scope должен быть необходимым и достаточным для использования программой
        """
        if len(scope) == 0:
            return True
        if not ("scope" in auth_cache):
            return False
        return EveESIAuth.__intersection(auth_cache["scope"], scope) == scope

    def make_cache(self, access_token, refresh_token):
        self.__auth_cache = {
            "access_token": access_token,
            "refresh_token": refresh_token}

        validated_jwt = validate_eve_jwt(access_token)
        if self.__debug:
            print("\nThe contents of the access token are: {}".format(validated_jwt))

        character_id = validated_jwt["sub"].split(":")[2]
        character_name = validated_jwt["name"]
        expired = validated_jwt["exp"]
        client_id = validated_jwt["azp"]
        scope = validated_jwt["scp"]

        self.__auth_cache.update({
            "expired": expired,
            "character_id": character_id,
            "character_name": character_name,
            "client_id": client_id,
            "scope": scope})

        self.__store_cache()
        return self.__auth_cache


def main(argv):
    """Manually input an auth token to refresh cache."""

    character_name = None  # for example : Qandra Si
    cache_dir = None  # for example : /tmp/.auth_cache
    exit_or_wrong_getopt = None
    try:
        opts, args = getopt.getopt(argv, "hp:a:", ["help", "pilot=", "authz_dir="])
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2
    if exit_or_wrong_getopt is None:
        for opt, arg in opts:  # noqa
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ("-p", "--pilot"):
                character_name = arg
            elif opt in ("-a", "--authz_dir"):
                cache_dir = arg
        if (character_name is None) or (cache_dir is None):
            exit_or_wrong_getopt = 0
    if not (exit_or_wrong_getopt is None):
        print('Usage: ' + os.path.basename(__file__) + ' --pilot=<name> --authz_dir=<cache_dir>')
        print('Example: ' + os.path.basename(__file__) + ' --pilot="Qandra Si" --authz_dir=../.auth_cache')
        sys.exit(exit_or_wrong_getopt)

    auth = EveESIAuth(cache_dir, debug=True)
    cache = auth.read_cache(character_name)
    print("\nThe previous contents of the cached data are {}".format(cache))

    access_token = input("Enter an access token to validate and cache: ")
    cache.update({"access_token": access_token})
    refresh_token = input("Enter an refresh token to remember: ")
    cache.update({"refresh_token": refresh_token})

    auth.make_cache(access_token, refresh_token)


if __name__ == "__main__":
    main(sys.argv[1:])
