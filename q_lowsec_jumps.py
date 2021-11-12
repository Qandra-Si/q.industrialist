""" Q.LowSec Jumps Stat (desktop/mobile)

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/).
    * Run pip install -r requirements.txt with this directory as your root.

    * Copy q_industrialist_settings.py.template into q_industrialist_settings.py and
      mood for your needs.
    * Copy q_logist_settings.py.template into q_logist_settings.py and
      mood for your needs.
    * Create an SSO application at developers.eveonline.com with the scopes
      from g_client_scope list declared in q_industrialist_settings.py and the
      callback URL "https://localhost/callback/".
      Note: never use localhost as a callback in released applications.

To run this example, make sure you have completed the prerequisites and then
run the following command from this directory as the root:

>>> python eve_sde_tools.py --cache_dir=~/.q_industrialist
>>> python q_lowsec_jumps.py --pilot="Qandra Si" --online --cache_dir=~/.q_industrialist

Required application scopes:
  * public access
"""
import sys
import json
import requests

import eve_esi_interface as esi

import eve_esi_tools
import eve_sde_tools
import console_app
import render_html_logist
import q_industrialist_settings
import q_logist_settings

from __init__ import __version__


def main():
    # работа с параметрами командной строки, получение настроек запуска программы, как то: работа в offline-режиме,
    # имя пилота ранее зарегистрированного и для которого имеется аутентификационный токен, регистрация нового и т.д.
    argv_prms = console_app.get_argv_prms()

    # sde_inv_names = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invNames")
    # sde_inv_items = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invItems")
    # sde_inv_positions = eve_sde_tools.read_converted(argv_prms["workspace_cache_files_dir"], "invPositions")

    for pilot_name in argv_prms["character_names"]:
        # настройка Eve Online ESI Swagger interface
        auth = esi.EveESIAuth(
            '{}/auth_cache'.format(argv_prms["workspace_cache_files_dir"]),
            debug=True)
        client = esi.EveESIClient(
            auth,
            debug=False,
            logger=True,
            user_agent='Q.Industrialist v{ver}'.format(ver=__version__))
        interface = esi.EveOnlineInterface(
            client,
            q_industrialist_settings.g_client_scope,
            cache_dir='{}/esi_cache'.format(argv_prms["workspace_cache_files_dir"]),
            offline_mode=argv_prms["offline_mode"])

        authz = interface.authenticate(pilot_name)
        character_id = authz["character_id"]
        character_name = authz["character_name"]

        # Public information about a character
        character_data = interface.get_esi_data(
            "characters/{}/".format(character_id),
            fully_trust_cache=True)
        # Public information about a corporation
        corporation_data = interface.get_esi_data(
            "corporations/{}/".format(character_data["corporation_id"]),
            fully_trust_cache=True)

        corporation_id = character_data["corporation_id"]
        corporation_name = corporation_data["name"]
        print("\n{} is from '{}' corporation".format(character_name, corporation_name))
        sys.stdout.flush()

        # Public access
        solar_systems = interface.get_esi_data(
            "universe/systems/",
            fully_trust_cache=True)
        print("Found {} solar systems on Tranquility".format(len(solar_systems)));
        sys.stdout.flush()

        # Public access
        region_ids = interface.get_esi_data(
            "universe/regions/",
            fully_trust_cache=True)

        # Public access
        regions_data = []
        for region_id in region_ids:
            region_desc = interface.get_esi_data(
                "universe/regions/{}/".format(region_id),
                fully_trust_cache=True);
            regions_data.append(region_desc)
        print("Found {} regions on Tranquility".format(len(regions_data)));
        sys.stdout.flush()

        # Public access
        system_jumps = interface.get_esi_paged_data("universe/system_jumps/")
        print("Found {} solar systems with jumps statistic on Tranquility".format(len(system_jumps)));
        sys.stdout.flush()

        # Public access
        low_sec_systems = []
        for system_id in solar_systems:
            system_desc = interface.get_esi_data(
                "universe/systems/{}/".format(system_id),
                fully_trust_cache=True);
            if system_desc:
                security_status = system_desc["security_status"]
                if security_status > 0 and security_status < 0.5:
                    low_sec_systems.append(system_desc);
        print("Found {} low sec systems on Tranquility".format(len(low_sec_systems)));

        for system_desc in low_sec_systems:
            constellation_id: int = system_desc["constellation_id"]
            system_id: int = system_desc["system_id"]
            ship_jumps: int = next((sj["ship_jumps"] for sj in system_jumps if sj["system_id"] == system_id), 0)
            region_name: str = next((r["name"] for r in regions_data if constellation_id in r["constellations"]), None)
            system_desc.update({"ship_jumps": ship_jumps, "region": region_name})

        low_sec_systems.sort(key=lambda s: s['ship_jumps'], reverse=False)

        print("Region\tSystem\tJumps\tGates")
        for system_desc in low_sec_systems:
            if system_desc["ship_jumps"] >= 10:
                break
            print("{}\t{}\t{}\t{}".format(
                system_desc["region"],
                system_desc["name"],
                system_desc["ship_jumps"],
                len(system_desc["stargates"])))

        break

    # Вывод в лог уведомления, что всё завершилось (для отслеживания с помощью tail)
    print("\nDone")


if __name__ == "__main__":
    main()
