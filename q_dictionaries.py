""" Q.Dictionaries (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

$ chcp 65001 & @rem on Windows only!
$ python eve_sde_tools.py --cache_dir=~/.q_industrialist
$ python q_dictionaries.py --category=all --cache_dir=~/.q_industrialist
"""
import sys
import getopt

import postgresql_interface as db

import q_industrialist_settings
import eve_sde_tools


def main():
    possible_categories = [
        # запуск скрипта со вводом всех возможных данных в БД (крайне не рекомендуется
        # запускать в этом режиме без необходимости, т.к. часть данных актуализируется по
        # ESI будучи первично добавлено этим скриптом, что к сожалению порой занимает много
        # времени)
        'all',
        # быстрый и унифицированный справочник по названиям, используемым во вселенной,
        # который разделяется по категориям в зависимости от типа
        'names',
        # ввод данных по чертежам, продуктам производста, типам произвосдва и материалам,
        # используемым при работе с чертежами (данные не могут быть получены по ESI), поэтому
        # это единстенный способ актаулизации информации при обновлении во вселейнной)
        'blueprints',
        # ввод данных по категориям групп предметов во вселенной
        'categories',
        # ввод данных по группам предметов во вселенной
        'groups',
        # ввод данных по типам во вселенной (впоследствии актуализируется автоматически по ESI,
        # а также дополняется параметром packaged_volume (что является очень длительной процедурой
        # и крайне не рекомендуются запускать скрипт с этим параметром без необходимости)
        'type_ids',
        # ввод данных по market группам, которые хранятся в БД в рекурсивном виде и хранят также
        # семантику по подтипам в зависимости от полезности группы (например все виды патронов
        # семантически относятся к патронам, а все виды руд, минералов относятся к материалам)
        'market_groups',
    ]

    exit_or_wrong_getopt = None
    workspace_cache_files_dir = None
    category = None
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "cache_dir=", "category="])
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2
    if exit_or_wrong_getopt is None:
        for opt, arg in opts:  # noqa
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ("--cache_dir"):
                workspace_cache_files_dir = arg[:-1] if arg[-1:] == '/' else arg
            elif opt in ("--category"):
                category = arg
        if workspace_cache_files_dir is None:
            exit_or_wrong_getopt = 0
        if not category or (category not in possible_categories):
            exit_or_wrong_getopt = 1
    if not (exit_or_wrong_getopt is None):
        print("Usage: {app} --category=names --cache_dir=/tmp\n"
              "Possible categories: {cats}\n"
              "Don't use 'type_ids' or 'all' category indiscriminately (too much afterward overheads)!".
              format(app=sys.argv[0], cats=possible_categories))
        sys.exit(exit_or_wrong_getopt)

    qidb = db.QIndustrialistDatabase("dictionaries", debug=False)
    qidb.connect(q_industrialist_settings.g_database)
    qidbdics = db.QDictionaries(qidb)

    if category in ['all', 'names']:
        sde_meta_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "metaGroups")
        qidbdics.actualize_names(sde_meta_groups, 0, "nameID")
        del sde_meta_groups

        sde_type_ids = eve_sde_tools.read_converted(workspace_cache_files_dir, "typeIDs")
        qidbdics.actualize_names(sde_type_ids, 1, "name")
        del sde_type_ids

        sde_market_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "marketGroups")
        qidbdics.actualize_names(sde_market_groups, 2, "nameID")
        del sde_market_groups

        sde_inv_names = eve_sde_tools.read_converted(workspace_cache_files_dir, "invNames")
        qidbdics.actualize_names(sde_inv_names, 3, None)
        del sde_inv_names

        # [1..6] : https://support.eveonline.com/hc/en-us/articles/203210272-Activities-and-Job-Types
        # [0,1,3,4,5,7,8,11, +9?] : https://github.com/esi/esi-issues/issues/894
        qidbdics.clean_names(4)
        qidbdics.insert_name(1, 4, "manufacturing")  # Manufacturing
        qidbdics.insert_name(3, 4, "te")  # Science
        qidbdics.insert_name(4, 4, "me")  # Science
        qidbdics.insert_name(5, 4, "copying")  # Science
        qidbdics.insert_name(7, 4, "reverse")  # Science
        qidbdics.insert_name(8, 4, "invention")  # Science
        qidbdics.insert_name(9, 4, "reaction")  # Reaction
        qidbdics.insert_name(11, 4, "reaction")  # Reaction
        qidb.commit()

        qidbdics.clean_integers(5)
        qidbdics.clean_integers(6)
        qidbdics.clean_integers(7)
        sde_blueprints = eve_sde_tools.read_converted(workspace_cache_files_dir, "blueprints")
        for bp in sde_blueprints.items():
            __blueprint_type_id = int(bp[0])
            __bpa = bp[1].get("activities", None)
            if __bpa is None:
                continue
            __bpam = __bpa.get("manufacturing", None)
            __bpai = __bpa.get("invention", None)
            __bpar = __bpa.get("reaction", None)
            if __bpam is not None:
                if "products" in __bpam:
                    __products_quantity = __bpam["products"][0]["quantity"]
                    qidbdics.insert_integer(__blueprint_type_id, 5, __products_quantity)
            if __bpai is not None:
                if "products" in __bpai:
                    __products_quantity = __bpai["products"][0]["quantity"]
                    qidbdics.insert_integer(__blueprint_type_id, 6, __products_quantity)
            if __bpar is not None:
                if "products" in __bpar:
                    __products_quantity = __bpar["products"][0]["quantity"]
                    qidbdics.insert_integer(__blueprint_type_id, 7, __products_quantity)
        # qidbdics.actualize_names(sde_meta_groups, 0, "nameID")
        del sde_blueprints

    if category in ['all', 'blueprints']:
        sde_bp_materials = eve_sde_tools.read_converted(workspace_cache_files_dir, "blueprints")
        qidbdics.clean_blueprints()
        qidbdics.actualize_blueprints(sde_bp_materials)
        del sde_bp_materials

    # при удалении type_ids, market_groups, groups и categories важно соблюсти последовательность
    # с тем, чтобы каскадоне удаление данных из связанных таблиц не уничтожало только что
    # добавленные данные

    if category in ['all', 'categories']:
        sde_categories = eve_sde_tools.read_converted(workspace_cache_files_dir, "categoryIDs")
        #qidbdics.clean_categories()
        qidbdics.actualize_categories(sde_categories)
        del sde_categories

    if category in ['all', 'groups']:
        sde_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "groupIDs")
        #qidbdics.clean_groups()
        qidbdics.actualize_groups(sde_groups)
        del sde_groups

    if category in ['all', 'market_groups']:
        sde_market_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "marketGroups")
        sde_market_groups_keys = sde_market_groups.keys()
        for group_id in sde_market_groups_keys:
            mg = sde_market_groups[str(group_id)]
            group_id: int = int(group_id)
            semantic_id = eve_sde_tools.get_basis_market_group_by_group_id(sde_market_groups, group_id)
            mg.update({'semanticGroupID': semantic_id if semantic_id else group_id})
        del sde_market_groups_keys
        #qidbdics.clean_market_groups()
        qidbdics.actualize_market_groups(sde_market_groups)
        del sde_market_groups

    if category in ['all', 'type_ids']:
        value = input("Are you sure to cleanup type_ids in database?\n"
                      "Too much afterward overheads!!!\n"
                      "Please type 'yes': ")
        if value == 'yes':
            sde_type_ids = eve_sde_tools.read_converted(workspace_cache_files_dir, "typeIDs")
            qidbdics.actualize_type_ids(sde_type_ids)
            del sde_type_ids

    del qidbdics
    del qidb
    sys.exit(0)  # code 0, all ok


if __name__ == "__main__":
    main()
