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
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "cache_dir="])
    except getopt.GetoptError:
        exit_or_wrong_getopt = 2
    if exit_or_wrong_getopt is None:
        for opt, arg in opts:  # noqa
            if opt in ('-h', "--help"):
                exit_or_wrong_getopt = 0
                break
            elif opt in ("--cache_dir"):
                workspace_cache_files_dir = arg[:-1] if arg[-1:] == '/' else arg
        if workspace_cache_files_dir is None:
            exit_or_wrong_getopt = 0
    if not (exit_or_wrong_getopt is None):
        print('Usage: {app} --cache_dir=/tmp\n'.
            format(app=sys.argv[0]))
        sys.exit(exit_or_wrong_getopt)

    qidb = db.QIndustrialistDatabase("dictionaries", debug=False)
    qidb.connect(q_industrialist_settings.g_database)
    qidbdics = db.QDictionaries(qidb)

    sde_meta_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "metaGroups")
    qidbdics.actualize(sde_meta_groups, 0, "nameID")
    del sde_meta_groups

    sde_type_ids = eve_sde_tools.read_converted(workspace_cache_files_dir, "typeIDs")
    qidbdics.actualize(sde_type_ids, 1, "name")
    del sde_type_ids

    sde_market_groups = eve_sde_tools.read_converted(workspace_cache_files_dir, "marketGroups")
    qidbdics.actualize(sde_market_groups, 2, "nameID")
    del sde_market_groups

    sde_inv_names = eve_sde_tools.read_converted(workspace_cache_files_dir, "invNames")
    qidbdics.actualize(sde_inv_names, 3, None)
    del sde_inv_names

    del qidbdics
    del qidb
    sys.exit(0)  # code 0, all ok


if __name__ == "__main__":
    main()
