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

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python eve_sde_tools.py
>>> python q_dictionaries.py --cache_dir=~/.q_industrialist
"""
import sys
import getopt

import postgresql_interface as db

import q_industrialist_settings
import eve_sde_tools


def main():
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
                category = int(arg)
        if workspace_cache_files_dir is None:
            exit_or_wrong_getopt = 0
    if not (exit_or_wrong_getopt is None):
        print('Usage: {app} --category=4 --cache_dir=/tmp\n'.
            format(app=sys.argv[0]))
        sys.exit(exit_or_wrong_getopt)

    qidb = db.QIndustrialistDatabase("dictionaries", debug=False)
    qidb.connect(q_industrialist_settings.g_database)
    qidbdics = db.QDictionaries(qidb)

    if (category is None) or (category == 0):
        sde_meta_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "metaGroups")
        qidbdics.actualize_names(sde_meta_groups, 0, "nameID")
        del sde_meta_groups

    if (category is None) or (category == 1):
        sde_type_ids = eve_sde_tools.read_converted(workspace_cache_files_dir, "typeIDs")
        qidbdics.actualize_names(sde_type_ids, 1, "name")
        del sde_type_ids

    if (category is None) or (category == 2):
        sde_market_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "marketGroups")
        qidbdics.actualize_names(sde_market_groups, 2, "nameID")
        del sde_market_groups

    if (category is None) or (category == 3):
        sde_inv_names = eve_sde_tools.read_converted(workspace_cache_files_dir, "invNames")
        qidbdics.actualize_names(sde_inv_names, 3, None)
        del sde_inv_names

    if (category is None) or (category == 4):
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

    if (category is None) or (category in [5,6,7]):
        if (category is None) or (category == 5):
            qidbdics.clean_integers(5)
        if (category is None) or (category == 6):
            qidbdics.clean_integers(6)
        if (category is None) or (category == 7):
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
            if not (__bpam is None) and ((category is None) or (category == 5)):
                if "products" in __bpam:
                    __products_quantity = __bpam["products"][0]["quantity"]
                    qidbdics.insert_integer(__blueprint_type_id, 5, __products_quantity)
            if not (__bpai is None) and ((category is None) or (category == 6)):
                if "products" in __bpai:
                    __products_quantity = __bpai["products"][0]["quantity"]
                    qidbdics.insert_integer(__blueprint_type_id, 6, __products_quantity)
            if not (__bpar is None) and ((category is None) or (category == 7)):
                if "products" in __bpar:
                    __products_quantity = __bpar["products"][0]["quantity"]
                    qidbdics.insert_integer(__blueprint_type_id, 7, __products_quantity)


        #qidbdics.actualize_names(sde_meta_groups, 0, "nameID")
        del sde_blueprints

    del qidbdics
    del qidb
    sys.exit(0)  # code 0, all ok


if __name__ == "__main__":
    main()
