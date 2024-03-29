﻿""" Console application tools and utils
"""
import sys
import getopt
import typing
from pathlib import Path

from __init__ import __version__


def print_version_screen():
    print('q.industrialist {ver} - (c) 2020 qandra.si@gmail.com\n'
          'Released under the GNU GPL.\n'.format(ver=__version__))


def print_help_screen(exit_code: typing.Optional[int] = None):
    print('\n'
          '-h --help                   Print this help screen\n'
          '   --pilot=NAME             Character name previously signed in\n'
          '   --signup                 Signup new character\n'
          '   --offline                Flag which says that we are working offline\n'
          '   --online                 Flag which says that we are working online (default)\n'
          '   --cache_dir=PATH         Directory where esi/auth cache files stored\n'
          '   --verbose                Show additional information while working (verbose mode)'
          '-v --version                Print version info\n'
          '\n'
          'Usage: {app} --pilot="Qandra Si" --offline --cache_dir=/tmp\n'.
          format(app=sys.argv[0]))
    if exit_code is not None and isinstance(exit_code, int):
        sys.exit(exit_code)


def get_argv_prms(additional_longopts: typing.List[str] = None):
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    res = {
        "character_names": [],
        "signup_new_character": False,
        "offline_mode": False,
        "workspace_cache_files_dir": '{}/.q_industrialist'.format(str(Path.home())),
        "verbose_mode": False,
    }
    # для всех дополнительных (настраиваемых) длинных параметров запуска будет выдаваться список строк-значений, при
    # условии, что параметр содержит символ '=' в конце наименования, либо bool-значение в том случае, если не модержит
    if additional_longopts:
        for opt in additional_longopts:
            if opt[-1:] == '=':  # category=
                res[opt[:-1]]: typing.List[str] = []
            else:  # category
                res[opt]: bool = False
    # парсинг входных параметров командной строки
    exit_or_wrong_getopt = None
    print_version_only = False
    try:
        longopts = ["help", "version", "pilot=", "signup", "offline", "online", "cache_dir=", "verbose"]
        if additional_longopts:
            longopts.extend(additional_longopts)
        opts, args = getopt.getopt(sys.argv[1:], "hv", longopts)
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2

    if exit_or_wrong_getopt is None:
        for opt, arg in opts:  # noqa
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ('-v', "--version"):
                exit_or_wrong_getopt = 0
                print_version_only = True
                break
            elif opt in "--pilot":
                res["character_names"].append(arg)
            elif opt in "--signup":
                res["signup_new_character"] = True
            elif opt in "--offline":
                res["offline_mode"] = True
            elif opt in "--online":
                res["offline_mode"] = False
            elif opt in "--verbose":
                res["verbose_mode"] = True
            elif opt in "--cache_dir":
                res["workspace_cache_files_dir"] = arg[:-1] if arg[-1:] == '/' else arg
            elif opt.startswith('--') and (opt[2:]+'=' in additional_longopts):
                res[opt[2:]].append(arg)
            elif opt.startswith('--') and opt[2:] in additional_longopts:
                res[opt[2:]] = True
        # д.б. либо указано имя, либо флаг регистрации нового пилота
        # упразднено: if (len(res["character_names"]) == 0) == (res["signup_new_character"] == False):
        # упразднено:     exit_or_wrong_getopt = 0

    if exit_or_wrong_getopt is not None:
        print_version_screen()
        if print_version_only:
            sys.exit(exit_or_wrong_getopt)
        print_help_screen(exit_or_wrong_getopt)

    return res
