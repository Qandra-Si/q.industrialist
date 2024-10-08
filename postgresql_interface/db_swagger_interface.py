# -*- encoding: utf-8 -*-
import pytz
import typing
import datetime


class QSwaggerInterface:
    def __init__(self, db):
        """ constructor

        :param db: instance of QIndustrialistDatabase
        """
        self.db = db

    def __del__(self):
        """ destructor
        """

    # -------------------------------------------------------------------------
    # u n i v e r s a l
    # -------------------------------------------------------------------------

    def is_exist_something(self, id, table, field):
        """
        :param table: table name
        :param field: field name
        :return: true - exist, false - absent
        """
        sdenid = self.db.select_one_row("SELECT 1 FROM {f} WHERE {t}=%s;".format(t=table, f=field), id)
        if sdenid is None:
            return False
        return True

    def get_exist_ids(self, table, field, updated=None):
        """
        :param table: table name
        :param field: field name of identity
        :param updated: field name of updated_at
        :return: list of unique identities stored in the database
        """
        if not updated:
            aids = self.db.select_all_rows("SELECT {f} FROM {t};".format(t=table, f=field))
        else:
            aids = self.db.select_all_rows("SELECT {f},{u} FROM {t};".format(t=table, f=field, u=updated))
        return aids

    def get_absent_ids(self, ids, table, field):
        """
        :param ids: list of unique identities to compare with ids, stored in the database
        :param table: table name
        :param field: field name
        :return: list of ids which are not in the database
        """
        aids = self.db.select_all_rows(
            "SELECT id FROM UNNEST(%s) AS a(id) "
            "WHERE id NOT IN (SELECT {f} FROM {t});".format(t=table, f=field),
            ids
        )
        return aids

    def select_region_id_by_name(self, region: str) -> typing.Optional[int]:
        row = self.db.select_one_row(
            "SELECT sden_id "
            "FROM eve_sde_names "
            "WHERE sden_name=%s and sden_category=3;",
            region
        )
        if row is None:
            return None
        return int(row[0])

    def select_station_id_by_name(self, station: str) -> typing.Optional[int]:
        row = self.db.select_one_row(
            "SELECT sden_id "
            "FROM eve_sde_names "
            "WHERE sden_name=%s and sden_category=3;",
            station
        )
        if row is None:
            return None
        return int(row[0])

    # -------------------------------------------------------------------------
    # characters/{character_id}/
    # -------------------------------------------------------------------------

    def is_exist_character_id(self, id):
        return self.is_exist_something(id, 'esi_characters', 'ech_character_id')

    def get_exist_character_ids(self):
        return self.get_exist_ids('esi_characters', 'ech_character_id', 'ech_updated_at')

    def get_absent_character_ids(self, ids):
        return self.get_absent_ids(ids, 'esi_characters', 'ech_character_id')

    def insert_or_update_character(self, id, data, updated_at):
        """ inserts character data into database

        :param id: unique character id
        :param data: character data
        :param updated_at: :class:`datetime.datetime`
        """
        # { "alliance_id": 99010134,
        #   "ancestry_id": 4,
        #   "birthday": "2009-08-19T19:23:00Z",
        #   "bloodline_id": 6,
        #   "corporation_id": 98553333,
        #   "description": "...",
        #   "gender": "male",
        #   "name": "olegez",
        #   "race_id": 4,
        #   "security_status": 3.960657443
        #  }
        self.db.execute(
            "INSERT INTO esi_characters("
            " ech_character_id,"
            " ech_name,"
            " ech_corporation_id,"
            " ech_birthday,"
            " ech_created_at,"
            " ech_updated_at) "
            "VALUES("
            " %(id)s,"
            " %(nm)s,"
            " %(co)s,"
            " %(bth)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ech DO UPDATE SET"
            " ech_corporation_id=%(co)s,"
            " ech_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'id': id,
             'nm': data['name'],
             'co': data['corporation_id'],
             'bth': data['birthday'],
             'at': updated_at,
             }
        )

    def select_character(self, id):
        row = self.db.select_one_row(
            "SELECT ech_name,ech_corporation_id,ech_birthday,ech_updated_at "
            "FROM esi_characters "
            "WHERE ech_character_id=%s;",
            id
        )
        if row is None:
            return None, None
        return {'name': row[0], 'corporation_id': row[1], 'birthday': row[2]}, row[3]

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/
    # -------------------------------------------------------------------------

    def is_exist_corporation_id(self, id):
        return self.is_exist_something(id, 'esi_corporations', 'eco_corporation_id')

    def get_exist_corporation_ids(self):
        return self.get_exist_ids('esi_corporations', 'eco_corporation_id', 'eco_updated_at')

    def get_absent_corporation_ids(self, ids):
        return self.get_absent_ids(ids, 'esi_corporations', 'eco_corporation_id')

    def insert_or_update_corporation(self, id, data, updated_at):
        """ inserts corporation data into database

        :param id: unique corporation id
        :param data: corporation data
        :param updated_at: :class:`datetime.datetime`
        """
        # { "alliance_id": 99007203,
        #   "ceo_id": 93531267,
        #   "creator_id": 93362315,
        #   "date_founded": "2019-09-27T20:27:54Z",
        #   "description": "...",
        #   "home_station_id": 60003064,
        #   "member_count": 215,
        #   "name": "R Initiative 4",
        #   "shares": 1000,
        #   "tax_rate": 0.1,
        #   "ticker": "RI4",
        #   "url": "",
        #   "war_eligible": true
        #  }
        self.db.execute(
            "INSERT INTO esi_corporations("
            " eco_corporation_id,"
            " eco_name,"
            " eco_ticker,"
            " eco_member_count,"
            " eco_ceo_id,"
            " eco_alliance_id,"
            " eco_tax_rate,"
            " eco_creator_id,"
            " eco_home_station_id,"
            " eco_shares,"
            " eco_created_at,"
            " eco_updated_at) "
            "VALUES ("
            " %(id)s,"
            " %(nm)s,"
            " %(ti)s,"
            " %(mem)s,"
            " %(ceo)s,"
            " %(ali)s,"
            " %(tax)s,"
            " %(own)s,"
            " %(hm)s,"
            " %(sh)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_eco DO UPDATE SET"
            " eco_name=%(nm)s,"
            " eco_ticker=%(ti)s,"
            " eco_member_count=%(mem)s,"
            " eco_ceo_id=%(ceo)s,"
            " eco_alliance_id=%(ali)s,"
            " eco_tax_rate=%(tax)s,"
            " eco_home_station_id=%(hm)s,"
            " eco_shares=%(sh)s,"
            " eco_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'id': id,
             'nm': data['name'],
             'ti': data['ticker'],
             'mem': data['member_count'],
             'ceo': data['ceo_id'],
             'ali': data.get('alliance_id', None),
             'tax': data['tax_rate'],
             'own': data['creator_id'],
             'hm': data.get('home_station_id', None),
             'sh': data.get('shares', None),
             'at': updated_at,
             }
        )

    def select_corporation(self, id):
        row = self.db.select_one_row(
            "SELECT eco_name,eco_ticker,eco_member_count,eco_ceo_id,eco_alliance_id,eco_tax_rate,"
            " eco_creator_id,eco_home_station_id,eco_shares,eco_updated_at "
            "FROM esi_corporations "
            "WHERE eco_corporation_id=%s;",
            id
        )
        if row is None:
            return None, None
        data = {
            'name': row[0],
            'ticker': row[1],
            'member_count': row[2],
            'ceo_id': row[3],
            'tax_rate': row[5],
            'creator_id': row[6],
            'shares': row[8]
        }
        if row[4]:
            data.update({'alliance_id': row[4]})
        if row[7]:
            data.update({'home_station_id': row[7]})
        return data, row[9]

    # -------------------------------------------------------------------------
    # universe/stations/
    # -------------------------------------------------------------------------

    def is_exist_station_id(self, id):
        return self.is_exist_something(id, 'esi_tranquility_stations', 'ets_station_id')

    def get_exist_universe_station_ids(self):
        return self.get_exist_ids('esi_tranquility_stations', 'ets_station_id', 'ets_updated_at')

    def get_absent_universe_station_ids(self, ids):
        return self.get_absent_ids(ids, 'esi_tranquility_stations', 'ets_station_id')

    def insert_or_update_universe_station(self, data, updated_at):
        """ inserts universe station data into database

        :param data: universe station data
        :param updated_at: :class:`datetime.datetime`
        """
        # { "max_dockable_ship_volume": 50000000,
        #   "name": "Jakanerva III - Moon 15 - Prompt Delivery Storage",
        #   "office_rental_cost": 10000,
        #   "owner": 1000003,
        #   "position": {
        #     "x": 165632286720,
        #     "y": 2771804160,
        #     "z": -2455331266560
        #   },
        #   "race_id": 1,
        #   "reprocessing_efficiency": 0.5,
        #   "reprocessing_stations_take": 0.05,
        #   "services": [
        #     "courier-missions",
        #     "reprocessing-plant",
        #     "market",
        #     "repair-facilities",
        #     "fitting",
        #     "news",
        #     "storage",
        #     "insurance",
        #     "docking",
        #     "office-rental",
        #     "loyalty-point-store",
        #     "navy-offices"
        #   ],
        #   "station_id": 60000277,
        #   "system_id": 30000148,
        #   "type_id": 1531
        # }
        self.db.execute(
            "INSERT INTO esi_tranquility_stations("
            " ets_station_id,"
            " ets_type_id,"
            " ets_name,"
            " ets_owner_id,"
            " ets_race_id,"
            " ets_x,ets_y,ets_z,"
            " ets_system_id,"
            " ets_reprocessing_efficiency,"
            " ets_reprocessing_stations_take,"
            " ets_max_dockable_ship_volume,"
            " ets_office_rental_cost,"
            " ets_created_at,"
            " ets_updated_at) "
            "VALUES ("
            " %(id)s,"
            " %(ty)s,"
            " %(nm)s,"
            " %(own)s,"
            " %(rc)s,"
            " %(x)s,%(y)s,%(z)s,"
            " %(ss)s,"
            " %(re)s,"
            " %(rt)s,"
            " %(vol)s,"
            " %(rnt)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ets DO UPDATE SET"
            " ets_type_id=%(ty)s,"
            " ets_name=%(nm)s,"
            " ets_owner_id=%(own)s,"
            " ets_race_id=%(rc)s,"
            " ets_x=%(x)s,ets_y=%(y)s,ets_z=%(z)s,"
            " ets_system_id=%(ss)s,"
            " ets_reprocessing_efficiency=%(re)s,"
            " ets_reprocessing_stations_take=%(rt)s,"
            " ets_max_dockable_ship_volume=%(vol)s,"
            " ets_office_rental_cost=%(rnt)s,"
            " ets_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'id': data['station_id'],
             'ty': data['type_id'],
             'nm': data['name'],
             'own': data.get('owner', None),  # ID of the corporation that controls this station
             'rc': data.get('race_id', None),
             'x': data['position']['x'],
             'y': data['position']['y'],
             'z': data['position']['z'],
             'ss': data['system_id'],
             're': data['reprocessing_efficiency'],
             'rt': data['reprocessing_stations_take'],
             'vol': data['max_dockable_ship_volume'],
             'rnt': data['office_rental_cost'],
             'at': updated_at,
             }
        )

    def select_universe_station(self, id):
        row = self.db.select_one_row(
            "SELECT ets_type_id,ets_name,ets_owner_id,ets_race_id,ets_x,ets_y,ets_z,ets_system_id,"
            " ets_reprocessing_efficiency,ets_reprocessing_stations_take,ets_max_dockable_ship_volume,"
            " ets_office_rental_cost,ets_updated_at "
            "FROM esi_tranquility_stations "
            "WHERE ets_station_id=%s;",
            id
        )
        if row is None:
            return None, None
        data = {
            'station_id': id,
            'type_id': row[0],
            'name': row[1],
            'position': {'x': row[4], 'y': row[5], 'z': row[6]},
            'system_id': row[7],
            'reprocessing_efficiency': row[8],
            'reprocessing_stations_take': row[9],
            'max_dockable_ship_volume': row[10],
            'office_rental_cost': row[11],
        }
        if row[2]:
            data.update({'owner': row[2]})
        if row[3]:
            data.update({'race_id': row[3]})
        return data, row[12]

    # -------------------------------------------------------------------------
    # universe/structures/
    # -------------------------------------------------------------------------

    def is_exist_structure_id(self, id):
        return self.is_exist_something(id, 'esi_universe_structures', 'eus_structure_id')

    def get_exist_universe_structure_ids(self):
        return self.get_exist_ids('esi_universe_structures', 'eus_structure_id', 'eus_updated_at')

    def get_absent_universe_structure_ids(self, ids):
        return self.get_absent_ids(ids, 'esi_universe_structures', 'eus_structure_id')

    def insert_or_update_universe_structure(self, id, data, forbidden, updated_at):
        """ inserts universe structure data into database

        :param id: unique structure id
        :param data: universe structure data
        :param updated_at: :class:`datetime.datetime`
        """
        # { "name": "Autama - Gunzey",
        #   "owner_id": 98285679,
        #   "position": {
        #    "x": 326015809896.0,
        #    "y": -3436537338.0,
        #    "z": 149013093495.0
        #   },
        #   "solar_system_id": 30001411,
        #   "type_id": 35825
        #  }
        if not forbidden:
            self.db.execute(
                "INSERT INTO esi_universe_structures("
                " eus_structure_id,"
                " eus_name,"
                " eus_owner_id,"
                " eus_system_id,"
                " eus_type_id,"
                " eus_x,eus_y,eus_z,"
                " eus_forbidden,"
                " eus_created_at,"
                " eus_updated_at) "
                "VALUES ("
                " %(id)s,"
                " %(nm)s,"
                " %(own)s,"
                " %(ss)s,"
                " %(ty)s,"
                " %(x)s,%(y)s,%(z)s,"
                " %(fbd)s,"
                " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
                " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
                "ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET"
                " eus_name=%(nm)s,"
                " eus_owner_id=%(own)s,"
                " eus_system_id=%(ss)s,"
                " eus_type_id=%(ty)s,"
                " eus_x=%(x)s,eus_y=%(y)s,eus_z=%(z)s,"
                " eus_forbidden=%(fbd)s,"
                " eus_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
                {'id': id,
                 'nm': data['name'],
                 'own': data['owner_id'],
                 'ss': data['solar_system_id'],
                 'ty': data.get('type_id', None),
                 'x': data['position']['x'],
                 'y': data['position']['y'],
                 'z': data['position']['z'],
                 'fbd': forbidden,
                 'at': updated_at,
                 }
            )
        else:
            self.db.execute(
                "INSERT INTO esi_universe_structures("
                " eus_structure_id,"
                " eus_name,"
                " eus_system_id,"
                " eus_x,eus_y,eus_z,"
                " eus_forbidden,"
                " eus_created_at,"
                " eus_updated_at) "
                "VALUES ("
                " %(id)s,"
                " 'Unknown Structure',"
                " 0,"
                " 0,0,0,"
                " true,"
                " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
                " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
                "ON CONFLICT ON CONSTRAINT pk_eus DO UPDATE SET"
                " eus_forbidden=true,"
                " eus_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
                {'id': id,
                 'at': updated_at,
                 }
            )

    def select_universe_structure(self, id):
        row = self.db.select_one_row(
            "SELECT eus_name,eus_owner_id,eus_system_id,eus_type_id,eus_x,eus_y,eus_z,eus_forbidden,"
            " eus_updated_at "
            "FROM esi_universe_structures "
            "WHERE eus_structure_id=%s;",
            id
        )
        if row is None:
            return None, None, None
        data = {
            'name': row[0],
            'owner_id': row[1],
            'solar_system_id': row[2],
            'position': {'x': row[4], 'y': row[5], 'z': row[6]},
        }
        if row[3]:
            data.update({'type_id': row[3]})
        forbidden: bool = False if row[7] is None else bool(row[7])
        return data, forbidden, row[8]

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/structures/
    # -------------------------------------------------------------------------

    def is_exist_corporation_structure(self, id):
        return self.is_exist_something(id, 'esi_corporation_structures', 'ecs_structure_id')

    def get_absent_corporation_structure_ids(self, ids):
        return self.get_absent_ids(ids, 'esi_corporation_structures', 'ecs_structure_id')

    def insert_or_update_corporation_structure(self, data, updated_at):
        """ inserts corporation structure data into database

        :param data: corporation structure data
        """
        # { "corporation_id": 98150545,
        #   "fuel_expires": "2021-03-28T09:00:00Z",
        #   "profile_id": 78795,
        #   "reinforce_hour": 16,
        #   "services": [
        #    {
        #     "name": "Manufacturing (Standard)",
        #     "state": "online"
        #    }
        #   ],
        #   "state": "shield_vulnerable",
        #   "structure_id": 1035620655696,
        #   "system_id": 30000153,
        #   "type_id": 35825
        # }
        self.db.execute(
            "INSERT INTO esi_corporation_structures("
            " ecs_structure_id,"
            " ecs_corporation_id,"
            " ecs_type_id,"
            " ecs_system_id,"
            " ecs_profile_id,"
            " ecs_created_at,"
            " ecs_updated_at) "
            "VALUES ("
            " %(id)s,"
            " %(co)s,"
            " %(ty)s,"
            " %(ss)s,"
            " %(pr)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ecs DO UPDATE SET"
            " ecs_corporation_id=%(co)s,"  # могут ли структуры передаваться другим корпорациям?
            " ecs_profile_id=%(pr)s,"
            " ecs_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'id': data['structure_id'],
             'co': data['corporation_id'],
             'ty': data['type_id'],
             'ss': data['system_id'],
             'pr': data['profile_id'],
             'at': updated_at,
             }
        )

    def get_exist_corporation_structures(self):
        rows = self.db.select_all_rows(
            "SELECT ecs_structure_id,ecs_corporation_id,ecs_type_id,ecs_system_id,ecs_profile_id,ecs_updated_at "
            "FROM esi_corporation_structures;"
        )
        if rows is None:
            return []
        data = []
        for row in rows:
            data.append({
                'structure_id': row[0],
                'corporation_id': row[1],
                'type_id': row[2],
                'system_id': row[3],
                'profile_id': row[4],
                'ext': {'updated_at': row[5]},
            })
        return data

    def mark_corporation_structures_updated(self, corporation_id, deleted_ids, updated_at):
        """ обновляет updated_at у существующих корп-структур и удаляет устаревшие (исчезнувшие) структуры

        :param corporation_id: corporation id to update its structure
        :param deleted_ids: obsolete corporation structure ids to remove from database
        :param updated_at: :class:`datetime.datetime`
        """
        if deleted_ids:
            self.db.execute(
                "DELETE FROM esi_corporation_structures "
                "WHERE ecs_structure_id IN (SELECT * FROM UNNEST(%s));",
                deleted_ids,
            )
        if updated_at:
            self.db.execute(
                "UPDATE esi_corporation_structures SET"
                " ecs_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s "
                "WHERE ecs_corporation_id=%(id)s;",
                {'id': corporation_id,
                 'at': updated_at,
                 }
            )

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/assets/
    # -------------------------------------------------------------------------

    def clear_corporation_assets(self, corporation_id):
        """ delete corporation assets data from database
        """
        self.db.execute(
            "DELETE FROM esi_corporation_assets WHERE eca_corporation_id=%s;",
            corporation_id
        )

    def insert_or_update_corporation_assets(self, data, corporation_id, updated_at):
        """ inserts corporation assets data into database

        :param data: corporation assets data
        """
        # { "is_singleton": true,
        #   "item_id": 1035620655696,
        #   "location_flag": "AutoFit",
        #   "location_id": 30000153,
        #   "location_type": "solar_system",
        #   "quantity": 1,
        #   "type_id": 35825
        # }
        self.db.execute(
            "INSERT INTO esi_corporation_assets("
            " eca_item_id,"
            " eca_corporation_id,"
            " eca_type_id,"
            " eca_quantity,"
            " eca_location_id,"
            " eca_location_type,"
            " eca_location_flag,"
            " eca_is_singleton,"
            " eca_name,"
            " eca_created_at,"
            " eca_updated_at) "
            "VALUES ("
            " %(id)s,"
            " %(co)s,"
            " %(ty)s,"
            " %(q)s,"
            " %(loc)s,"
            " %(lty)s,"
            " %(lfl)s,"
            " %(sn)s,"
            " %(nm)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_eca DO UPDATE SET"
            " eca_corporation_id=%(co)s,"  # ассеты могут перемещаться до того, как будет выяснено куда?
            " eca_quantity=%(q)s,"
            " eca_location_id=%(loc)s,"
            " eca_location_type=%(lty)s,"
            " eca_location_flag=%(lfl)s,"
            " eca_is_singleton=%(sn)s,"
            " eca_name=%(nm)s,"
            " eca_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'id': data['item_id'],
             'co': corporation_id,
             'ty': data['type_id'],
             'q': data['quantity'],
             'loc': data['location_id'],
             'lty': data['location_type'],
             'lfl': data['location_flag'],
             'sn': data['is_singleton'],
             'nm': data.get('name', None),
             'at': updated_at,
             }
        )

    def get_exist_corporation_assets(self):
        rows = self.db.select_all_rows(
            "SELECT"
            " eca_item_id,"
            " eca_corporation_id,"
            " eca_type_id,"
            " eca_quantity,"
            " eca_location_id,"
            " eca_location_type,"
            " eca_location_flag,"
            " eca_is_singleton,"
            " eca_name,"
            " eca_updated_at "
            "FROM esi_corporation_assets;"
        )
        if rows is None:
            return []
        data = []
        for row in rows:
            ext = {'updated_at': row[9], 'corporation_id': row[1]}
            if row[8]:
                ext.update({'name': row[8]})
            data.append({
                'item_id': row[0],
                'type_id': row[2],
                'quantity': row[3],
                'location_id': row[4],
                'location_type': row[5],
                'location_flag': row[6],
                'is_singleton': row[7],
                'ext': ext,
            })
        return data

    def get_exist_corporation_assets_names(self):
        rows = self.db.select_all_rows(
            "SELECT"
            " eca_item_id,"
            " eca_corporation_id,"
            " eca_name "
            "FROM esi_corporation_assets "
            "WHERE eca_name IS NOT NULL;"
        )
        return rows  # м.б. None

    def delete_obsolete_corporation_assets(self, deleted_ids):
        """ обновляет updated_at у существующих корп-ассетов и удаляет устаревшие (исчезнувшие) ассеты

        :param deleted_ids: obsolete corporation asset items ids to remove from database
        :param corporation_id: corporation id to update its assets
        :param updated_at: :class:`datetime.datetime`
        """
        if deleted_ids:
            self.db.execute(
                "DELETE FROM esi_corporation_assets "
                "WHERE eca_item_id IN (SELECT * FROM UNNEST(%s));",
                deleted_ids,
            )

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/blueprints/
    # -------------------------------------------------------------------------

    def clear_corporation_blueprints(self, corporation_id):
        """ delete corporation blueprints data from database
        """
        self.db.execute(
            "DELETE FROM esi_corporation_blueprints WHERE ecb_corporation_id=%s;",
            corporation_id
        )

    def insert_or_update_corporation_blueprints(self, data, corporation_id, updated_at):
        """ inserts corporation blueprints data into database

        :param data: corporation blueprints data
        """
        # { "item_id": 162478388,
        #   "location_flag": "CorpSAG4",
        #   "location_id": 1035318107573,
        #   "material_efficiency": 10,
        #   "quantity": -1,
        #   "runs": -1,
        #   "time_efficiency": 20,
        #   "type_id": 17860
        # }
        self.db.execute(
            "INSERT INTO esi_corporation_blueprints("
            " ecb_corporation_id,"
            " ecb_item_id,"
            " ecb_type_id,"
            " ecb_location_id,"
            " ecb_location_flag,"
            " ecb_quantity,"
            " ecb_time_efficiency,"
            " ecb_material_efficiency,"
            " ecb_runs,"
            " ecb_created_at,"
            " ecb_updated_at) "
            "VALUES ("
            " %(co)s,"
            " %(id)s,"
            " %(ty)s,"
            " %(loc)s,"
            " %(lfl)s,"
            " %(q)s,"
            " %(te)s,"
            " %(me)s,"
            " %(r)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ecb DO UPDATE SET"
            " ecb_corporation_id=%(co)s,"  # чертежи могут перемещаться до того, как будет выяснено куда?
            " ecb_type_id=%(ty)s,"
            " ecb_location_id=%(loc)s,"
            " ecb_location_flag=%(lfl)s,"
            " ecb_quantity=%(q)s,"
            " ecb_time_efficiency=%(te)s,"
            " ecb_material_efficiency=%(me)s,"
            " ecb_runs=%(r)s,"
            " ecb_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'co': corporation_id,
             'id': data['item_id'],
             'ty': data['type_id'],
             'loc': data['location_id'],
             'lfl': data['location_flag'],
             'q': data['quantity'],
             'me': data['material_efficiency'],
             'te': data['time_efficiency'],
             'r': data['runs'],
             'at': updated_at,
             }
        )

    def get_exist_corporation_blueprints(self, corporation_id):
        rows = self.db.select_all_rows(
            "SELECT"
            " ecb_item_id,"
            " ecb_type_id,"
            " ecb_location_id,"
            " ecb_location_flag,"
            " ecb_quantity,"
            " ecb_time_efficiency,"
            " ecb_material_efficiency,"
            " ecb_runs,"
            " ecb_updated_at "
            "FROM esi_corporation_blueprints "
            "WHERE ecb_corporation_id=%s;",
            int(corporation_id),
        )
        if rows is None:
            return []
        data = []
        for row in rows:
            ext = {'updated_at': row[8], 'corporation_id': corporation_id}
            data.append({
                'item_id': row[0],
                'type_id': row[1],
                'location_id': row[2],
                'location_flag': row[3],
                'quantity': row[4],
                'time_efficiency': row[5],
                'material_efficiency': row[6],
                'runs': row[7],
                'ext': ext,
            })
        return data

    def delete_obsolete_corporation_blueprints(self, deleted_ids):
        """ обновляет updated_at у существующих корп-чертежей и удаляет устаревшие (исчезнувшие) БП

        :param deleted_ids: obsolete corporation blueprint items ids to remove from database
        :param corporation_id: corporation id to update its blueprints
        :param updated_at: :class:`datetime.datetime`
        """
        if deleted_ids:
            self.db.execute(
                "DELETE FROM esi_corporation_blueprints "
                "WHERE ecb_item_id IN (SELECT * FROM UNNEST(%s));",
                deleted_ids,
            )

    # -------------------------------------------------------------------------
    # characters/{character_id}/blueprints/
    # -------------------------------------------------------------------------

    def clear_character_blueprints(self, character_id):
        """ delete corporation blueprints data from database
        """
        self.db.execute(
            "DELETE FROM esi_pilot_blueprints WHERE ecb_character_id=%s;",
            character_id
        )

    def insert_or_update_character_blueprints(self, data, character_id, updated_at):
        """ inserts character blueprints data into database

        :param data: character blueprints data
        """
        # { "item_id": 162478388,
        #   "location_flag": "CorpSAG4",
        #   "location_id": 1035318107573,
        #   "material_efficiency": 10,
        #   "quantity": -1,
        #   "runs": -1,
        #   "time_efficiency": 20,
        #   "type_id": 17860
        # }
        self.db.execute(
            "INSERT INTO esi_pilot_blueprints("
            " epb_character_id,"
            " epb_item_id,"
            " epb_type_id,"
            " epb_location_id,"
            " epb_location_flag,"
            " epb_quantity,"
            " epb_time_efficiency,"
            " epb_material_efficiency,"
            " epb_runs,"
            " epb_created_at,"
            " epb_updated_at) "
            "VALUES ("
            " %(ch)s,"
            " %(id)s,"
            " %(ty)s,"
            " %(loc)s,"
            " %(lfl)s,"
            " %(q)s,"
            " %(te)s,"
            " %(me)s,"
            " %(r)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_epb DO UPDATE SET"
            " epb_character_id=%(ch)s,"  # чертежи могут перемещаться до того, как будет выяснено куда?
            " epb_type_id=%(ty)s,"
            " epb_location_id=%(loc)s,"
            " epb_location_flag=%(lfl)s,"
            " epb_quantity=%(q)s,"
            " epb_time_efficiency=%(te)s,"
            " epb_material_efficiency=%(me)s,"
            " epb_runs=%(r)s,"
            " epb_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'ch': character_id,
             'id': data['item_id'],
             'ty': data['type_id'],
             'loc': data['location_id'],
             'lfl': data['location_flag'],
             'q': data['quantity'],
             'me': data['material_efficiency'],
             'te': data['time_efficiency'],
             'r': data['runs'],
             'at': updated_at,
             }
        )

    def get_exist_character_blueprints(self, character_id):
        rows = self.db.select_all_rows(
            "SELECT"
            " epb_item_id,"
            " epb_type_id,"
            " epb_location_id,"
            " epb_location_flag,"
            " epb_quantity,"
            " epb_time_efficiency,"
            " epb_material_efficiency,"
            " epb_runs,"
            " epb_updated_at "
            "FROM esi_pilot_blueprints "
            "WHERE epb_character_id=%s;",
            int(character_id),
        )
        if rows is None:
            return []
        data = []
        for row in rows:
            ext = {'updated_at': row[8], 'character_id': character_id}
            data.append({
                'item_id': row[0],
                'type_id': row[1],
                'location_id': row[2],
                'location_flag': row[3],
                'quantity': row[4],
                'time_efficiency': row[5],
                'material_efficiency': row[6],
                'runs': row[7],
                'ext': ext,
            })
        return data

    def delete_obsolete_character_blueprints(self, deleted_ids):
        """ обновляет updated_at у существующих перс-чертежей и удаляет устаревшие (исчезнувшие) БП

        :param deleted_ids: obsolete character blueprint items ids to remove from database
        """
        if deleted_ids:
            self.db.execute(
                "DELETE FROM esi_pilot_blueprints "
                "WHERE epb_item_id IN (SELECT * FROM UNNEST(%s));",
                deleted_ids,
            )

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/industry/jobs/
    # -------------------------------------------------------------------------

    def insert_or_update_corporation_industry_jobs(self, data, corporation_id, updated_at):
        """ inserts corporation industry job data into database

        :param data: corporation industry job data
        """
        # print("INSERT {} {} {}".format(data['job_id'], data['activity_id'], data['status']))
        # return
        # { "activity_id": 3,
        #   "blueprint_id": 1035690963115,
        #   "blueprint_location_id": 1035704750584,
        #   "blueprint_type_id": 12055,
        #   "cost": 319478.0,
        #   "duration": 617929,
        #   "end_date": "2021-03-24T21:42:07Z",
        #   "facility_id": 1035620697572,
        #   "installer_id": 2116252240,
        #   "job_id": 453460908,
        #   "licensed_runs": 60,
        #   "location_id": 1035620697572,
        #   "output_location_id": 1035704750584,
        #   "probability": 1.0,
        #   "product_type_id": 12055,
        #   "runs": 9,
        #   "start_date": "2021-03-17T18:03:18Z",
        #   "status": "active"
        # }
        self.db.execute(
            "INSERT INTO esi_corporation_industry_jobs("
            " ecj_corporation_id,"
            " ecj_job_id,"
            " ecj_installer_id,"
            " ecj_facility_id,"
            " ecj_location_id,"
            " ecj_activity_id,"
            " ecj_blueprint_id,"
            " ecj_blueprint_type_id,"
            " ecj_blueprint_location_id,"
            " ecj_output_location_id,"
            " ecj_runs,"
            " ecj_cost,"
            " ecj_licensed_runs,"
            " ecj_probability,"
            " ecj_product_type_id,"
            " ecj_status,"
            " ecj_duration,"
            " ecj_start_date,"
            " ecj_end_date,"
            " ecj_pause_date,"
            " ecj_completed_date,"
            " ecj_completed_character_id,"
            " ecj_successful_runs,"
            " ecj_created_at,"
            " ecj_updated_at) "
            "VALUES ("
            " %(co)s,"
            " %(id)s,"
            " %(who)s,"
            " %(fac)s,"
            " %(loc)s,"
            " %(a)s,"
            " %(bp)s,"
            " %(bty)s,"
            " %(bpl)s,"
            " %(out)s,"
            " %(r)s,"
            " %(c)s,"
            " %(lr)s,"
            " %(p)s,"
            " %(pty)s,"
            " %(s)s,"
            " %(d)s,"
            " %(sdt)s,"
            " %(edt)s,"
            " %(pdt)s,"
            " %(cdt)s,"
            " %(cwho)s,"
            " %(sr)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ecj DO UPDATE SET"
            " ecj_status=%(s)s,"
            " ecj_pause_date=%(pdt)s,"
            " ecj_completed_date=%(cdt)s,"
            " ecj_completed_character_id=%(cwho)s,"
            " ecj_successful_runs=%(sr)s,"
            " ecj_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'co': corporation_id,
             'id': data['job_id'],
             'who': data['installer_id'],
             'fac': data['facility_id'],
             'loc': data['location_id'],
             'a': data['activity_id'],
             'bp': data['blueprint_id'],
             'bty': data['blueprint_type_id'],
             'bpl': data['blueprint_location_id'],
             'out': data['output_location_id'],
             'r': data['runs'],
             'c': data.get('cost', None),
             'lr': data.get('licensed_runs', None),
             'p': data.get('probability', None),
             'pty': data.get('product_type_id', None),
             's': data['status'],
             'd': data['duration'],
             'sdt': data['start_date'],
             'edt': data['end_date'],
             'pdt': data.get('pause_date', None),
             'cdt': data.get('completed_date', None),
             'cwho': data.get('completed_character_id', None),
             'sr': data.get('successful_runs', None),
             'at': updated_at,
             }
        )

    def get_exist_corporation_industry_jobs(self, corporation_id: int, oldest_delivered_job=None):
        if oldest_delivered_job:
            where = "ecj_corporation_id={co} AND " \
                    "(ecj_completed_date IS NULL OR (" \
                    " ecj_status in ('delivered','cancelled') AND ecj_job_id>={job})" \
                    ")".\
                    format(co=corporation_id, job=oldest_delivered_job)
        else:
            where = "ecj_corporation_id={co} AND ecj_completed_date IS NULL".\
                    format(co=corporation_id)
        rows = self.db.select_all_rows(
            "SELECT"
            " ecj_corporation_id,"
            " ecj_job_id,"
            " ecj_installer_id,"
            " ecj_facility_id,"
            " ecj_location_id,"
            " ecj_activity_id,"
            " ecj_blueprint_id,"
            " ecj_blueprint_type_id,"
            " ecj_blueprint_location_id,"
            " ecj_output_location_id,"
            " ecj_runs,"
            " ecj_cost,"
            " ecj_licensed_runs,"
            " ecj_probability,"
            " ecj_product_type_id,"
            " ecj_status,"
            " ecj_duration,"
            " ecj_start_date,"
            " ecj_end_date,"
            " ecj_pause_date,"
            " ecj_completed_date,"
            " ecj_completed_character_id,"
            " ecj_successful_runs,"
            " ecj_updated_at "
            "FROM esi_corporation_industry_jobs "
            "WHERE {};".
            format(where)
        )
        if rows is None:
            return []
        data = []
        for row in rows:
            ext = {'updated_at': row[23], 'corporation_id': row[0]}
            data_item = {
                'job_id': row[1],
                'installer_id': row[2],
                'facility_id': row[3],
                'location_id': row[4],
                'activity_id': row[5],
                'blueprint_id': row[6],
                'blueprint_type_id': row[7],
                'blueprint_location_id': row[8],
                'output_location_id': row[9],
                'runs': row[10],
                'cost': row[11],
                'status': row[15],
                'duration': row[16],
                'start_date': row[17],
                'end_date': row[18],
                'ext': ext,
            }
            if row[12] is not None:
                data_item.update({'licensed_runs': row[12]})
            if row[13] is not None:
                data_item.update({'probability': row[13]})
            if row[14]:
                data_item.update({'product_type_id': row[14]})
            if row[19]:
                data_item.update({'pause_date': row[19]})
            if row[20]:
                data_item.update({'completed_date': row[20]})
            if row[21]:
                data_item.update({'completed_character_id': row[21]})
            if row[22] is not None:
                data_item.update({'successful_runs': row[22]})
            data.append(data_item)
        return data

    def discard_obsolete_corporation_jobs(self):
        # CCP отдают не более 2000 работ, соответственно если их будет больше, то часть работ не будет упомянута никогда
        self.db.execute(
            "UPDATE esi_corporation_industry_jobs "
            "SET ecj_status='delivered' "
            "FROM ("
            " SELECT ecj_corporation_id AS cid, ecj_job_id AS jid"
            " FROM esi_corporation_industry_jobs"
            " WHERE"
            "   ecj_status='active' AND"
            "   CURRENT_TIMESTAMP AT TIME ZONE 'GMT' > (ecj_end_date+interval '180 minute')"
            ") j "
            "WHERE ecj_job_id=j.jid AND ecj_corporation_id=j.cid;"
        )
        # ecj_updated_at не трогаем и он будет меньше end_date
        # автоматически завершаем только activity_id=1, т.к. у этих работ не меняются параметры при завершении
        # иначе возникают проблемы с формированием esi_blueprints_costs
        # TODO: отменил условие "   ecj_activity_id=1 AND", иначе годами копились незавершённые работы

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/blueprints/
    # corporations/{corporation_id}/industry/jobs/
    # -------------------------------------------------------------------------

    def link_wallet_journals_with_jobs(self):
        # список работ, которые пока что не имеют стоимости выполненных работ в базе данных
        self.db.execute(
            "update esi_blueprint_costs as ebc set"
            " ebc_industry_payment = a.pay,"
            " ebc_tax = a.tax "
            "from ("
            " select"
            "  ebc_id,"  # -- ebc_job_id,
            "  -t.ecwj_amount as tax,"
            "  -j.ecwj_amount as pay"
            " from"
            "  esi_blueprint_costs"  # -- платёж, который есть не всегда, т.к. налоги м.б. низкие
            "   left outer join esi_corporation_wallet_journals t on ("
            "   ebc_job_id = t.ecwj_context_id and"
            "   ebc_job_corporation_id = t.ecwj_corporation_id and"
            "   t.ecwj_context_id_type = 'industry_job_id' and"
            "   t.ecwj_ref_type = 'industry_job_tax'"
            " ),"
            " esi_corporation_wallet_journals j "
            "where"  # -- работы без платежей
            " ebc_transaction_type in ('f','j','p') and"
            " ebc_industry_payment is null and"
            # -- ограничение времени
            " (current_timestamp at time zone 'GMT' - interval '20 minutes') >= ebc_updated_at and"
            " ebc_updated_at >= (current_timestamp at time zone 'GMT' - interval '24 hours') and"
            # -- платёж, который есть всегда
            " ebc_job_id = j.ecwj_context_id and"
            " ebc_job_corporation_id = j.ecwj_corporation_id and"
            " j.ecwj_context_id_type = 'industry_job_id' and"
            " j.ecwj_ref_type != 'industry_job_tax'"
            ") a "
            "where a.ebc_id = ebc.ebc_id")

    def link_blueprint_copies_with_jobs(self):
        # настройки работы метода
        #  * deffered: время, после которого история не анализируется
        #  * missed: ждём кол-во часом не менее чем, чтобы дождаться когда будут добыты все недостающие данные
        missed_hours: int = 1
        deffered_hours: int = 24
        # формируем интервал анализа несвязанных чертежей и работ (ждём 2 часа, игнорируем слишком старые)
        where_hours: str = "((current_timestamp at time zone 'GMT' - interval '{mh} hours') >= ebc_updated_at and " \
                           "ebc_updated_at >= (current_timestamp at time zone 'GMT' - interval '{dh} hours'))".\
                           format(mh=missed_hours, dh=deffered_hours)

        # список продуктов, которые пока что являются не связанными в базе данных
        unlinked_blueprint_types = self.db.select_all_rows(
            "SELECT"
            " DISTINCT ebc_job_product_type_id "
            # debug: " ,(select sden_name from eve_sde_names"
            # debug: "  where sden_category=1 and sden_id=ebc_job_product_type_id) as type_name "
            "FROM esi_blueprint_costs "
            "WHERE"
            " ebc_job_activity=5 AND"  # copies
            " ebc_blueprint_id IS NULL AND"
            " ebc_transaction_type='f' AND"
            " {wh};".format(wh=where_hours)
        )

        for ubtype in unlinked_blueprint_types:
            type_id: int = int(ubtype[0])
            # debug: print(type_id, ubtype[1] if len(ubtype) == 2 else '')

            unlinked_bpcs_and_jobs = self.db.select_all_rows(
                "SELECT"
                " ebc_system_id as solar_system,"                                        # 0 *
                # " (select sden_name from eve_sde_names"
                # "  where sden_category=3 and sden_id=ebc_system_id) as solar_system,"  # 0 (debug only)
                " ebc_id as id,"                           # 1 *
                " ebc_blueprint_id as bpc_id,"             # 2 *
                # " ebc_blueprint_type_id as bpo_type,"
                " ebc_blueprint_runs as bp_runs,"          # 3 *
                " ebc_time_efficiency as te,"              # 4 *
                " ebc_material_efficiency as me,"          # 5 *
                # " ebc_job_id as job_id,"
                " ecj_blueprint_id as job_bp,"             # 6 *
                # " ebc_job_product_type_id as bpc_type,"
                " ebc_job_runs as rest_runs,"              # 7 * (меняется в процессе поиска чертежей)
                " ebc_job_time_efficiency as job_te,"      # 8 *
                " ebc_job_material_efficiency as job_me "  # 9 *
                "FROM"
                " esi_blueprint_costs"
                "  LEFT OUTER JOIN esi_corporation_industry_jobs ON (ebc_job_id=ecj_job_id) "
                "WHERE"
                " {wh} AND"
                " ((ebc_job_product_type_id=%(bty)s AND ebc_transaction_type='f' AND ebc_job_activity=5) OR"
                "  (ebc_blueprint_type_id=%(bty)s AND ebc_transaction_type='A' AND ebc_job_id IS NULL)"
                " )"
                "ORDER BY 2 DESC;".format(wh=where_hours),
                {'bty': type_id,
                 }
            )
            # debug: for unlinked in unlinked_bpcs_and_jobs:
            # debug:     print(unlinked)
            unlinked_jobs = [j for j in unlinked_bpcs_and_jobs if j[2] is None]

            # debug: print('unlinked_jobs', unlinked_jobs)
            used_ebc_ids = []
            for job in unlinked_jobs:
                solar_system = job[0]
                licensed_runs: int = job[3]
                blueprint_id: int = job[6]
                job_runs: int = job[7]
                te: int = job[8]
                me: int = job[9]
                found_ebc_ids = []
                for bpc in unlinked_bpcs_and_jobs:
                    if bpc[1] in used_ebc_ids:
                        continue
                    blueprint_copy_id: int = bpc[2]
                    # в списке имеются и работы и чертежи, пропускаем работы (ищем только чертежи)
                    if blueprint_copy_id is None:
                        continue
                    # если в список попал чертёж, который использовался в работе - он точно не её результат
                    if blueprint_id == blueprint_copy_id:
                        continue
                    # пропускаем те чертежи, которые сделаны в других солнечных системах
                    if bpc[0] == solar_system:
                        # пропускаем те чертежи, параметры которых отличаются от параметров работы
                        if (bpc[3] != licensed_runs) or (bpc[4] != te) or (bpc[5] != me):
                            continue
                        # debug: print("!!!!!!!! (", job_runs, ") : ", job[1], " -> ", blueprint_copy_id)
                        found_ebc_ids.append(bpc[1])
                        # как только найдено достаточное кол-во чертежей по этой работе, то прекращаем их поиск
                        job_runs -= 1
                        if job_runs == 0:
                            break
                # изменение связей в БД
                if found_ebc_ids:
                    self.db.execute(
                        "UPDATE esi_blueprint_costs SET("
                        " ebc_job_id,"
                        " ebc_job_corporation_id,"
                        " ebc_job_activity,"
                        " ebc_job_product_type_id,"
                        " ebc_industry_payment,"
                        " ebc_tax,"
                        " ebc_updated_at)="
                        "(SELECT"
                        "  ebc_job_id,"
                        "  ebc_job_corporation_id,"
                        "  ebc_job_activity,"
                        "  ebc_job_product_type_id,"
                        "  ebc_industry_payment,"
                        "  ebc_tax,"
                        "  CURRENT_TIMESTAMP AT TIME ZONE 'GMT'"
                        " FROM"
                        "  esi_blueprint_costs"
                        " WHERE"
                        "  ebc_id=%(jid)s"
                        ")"
                        "WHERE"
                        " ebc_id IN (SELECT * FROM UNNEST(%(ids)s));",
                        {'jid': job[1],
                         'ids': found_ebc_ids,
                         }
                    )
                    if job_runs == 0:
                        self.db.execute(
                            "UPDATE esi_blueprint_costs SET"
                            " ebc_job_runs=0,"
                            " ebc_transaction_type='p',"
                            " ebc_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT' "
                            "WHERE ebc_id=%(jid)s;",
                            {'jid': job[1],
                             }
                        )
                    else:
                        self.db.execute(
                            "UPDATE esi_blueprint_costs SET"
                            " ebc_job_runs=%(r)s,"
                            " ebc_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT' "
                            "WHERE ebc_id=%(jid)s;",
                            {'jid': job[1],
                             'r': job_runs,
                             }
                        )
                    used_ebc_ids += found_ebc_ids
            del used_ebc_ids

        del unlinked_blueprint_types

    def link_blueprint_invents_with_jobs(self):
        # настройки работы метода
        #  * deffered: время, после которого история не анализируется
        #  * missed: ждём кол-во часом не менее чем, чтобы дождаться когда будут добыты все недостающие данные
        missed_hours: int = 1
        deffered_hours: int = 24
        # формируем интервал анализа несвязанных чертежей и работ (ждём 2 часа, игнорируем слишком старые)
        where_hours: str = "((current_timestamp at time zone 'GMT' - interval '{mh} hours') >= ebc_updated_at and " \
                           "ebc_updated_at >= (current_timestamp at time zone 'GMT' - interval '{dh} hours'))".\
                           format(mh=missed_hours, dh=deffered_hours)

        # список продуктов, которые пока что являются не связанными в базе данных
        unlinked_blueprint_types = self.db.select_all_rows(
            "SELECT"
            " DISTINCT ebc_job_product_type_id "
            # debug: " ,(select sden_name from eve_sde_names"
            # debug: "  where sden_category=1 and sden_id=ebc_job_product_type_id) as type_name "
            "FROM esi_blueprint_costs "
            "WHERE"
            " ebc_job_activity=8 AND"  # invent
            " ebc_blueprint_id IS NULL AND"
            " ebc_transaction_type='f' AND"
            " ebc_job_successful_runs>0 AND"
            " {wh};".format(wh=where_hours)
        )

        for ubtype in unlinked_blueprint_types:
            type_id: int = int(ubtype[0])
            # debug: print(type_id, ubtype[1] if len(ubtype) == 2 else '')

            unlinked_bp2s_and_jobs = self.db.select_all_rows(
                "SELECT"
                " ebc_system_id,"                                                        # 0 *
                # " (select sden_name from eve_sde_names"
                # "  where sden_category=3 and sden_id=ebc_system_id) as solar_system,"  # 0 (debug only)
                " ebc_id,"                                 # 1 *
                " ebc_blueprint_id,"                       # 2 *
                " ebc_job_successful_runs "                # 3 * (меняется в процессе поиска чертежей)
                "FROM"
                " esi_blueprint_costs "
                "WHERE"
                " {wh} AND"
                " ((ebc_job_product_type_id=%(bty)s AND ebc_transaction_type='f' AND ebc_job_activity=8) OR"
                "  (ebc_blueprint_type_id=%(bty)s AND ebc_transaction_type='A' AND ebc_job_id IS NULL)"
                " )"
                "ORDER BY 2 DESC;".format(wh=where_hours),
                {'bty': type_id,
                 }
            )
            # debug: for unlinked in unlinked_bp2s_and_jobs:
            # debug:     print(unlinked)
            unlinked_jobs = [j for j in unlinked_bp2s_and_jobs if j[2] is None]

            # debug: print('unlinked_jobs', unlinked_jobs)
            used_ebc_ids = []
            for job in unlinked_jobs:
                successful_runs: typying.Optional[int] = job[3]
                if successful_runs is None:
                    continue
                solar_system = job[0]
                found_ebc_ids = []
                if successful_runs > 0:
                    for bpc in unlinked_bp2s_and_jobs:
                        if bpc[1] in used_ebc_ids:
                            continue
                        blueprint_t2_id: int = bpc[2]
                        # в списке имеются и работы и чертежи, пропускаем работы (ищем только чертежи)
                        if blueprint_t2_id is None:
                            continue
                        # пропускаем те чертежи, которые сделаны в других солнечных системах
                        if bpc[0] == solar_system:
                            # debug: print("!!!!!!!! (", successful_runs, ") : ", job[1], " -> ", job)
                            found_ebc_ids.append(bpc[1])
                            # как только найдено достаточное кол-во чертежей по этой работе, то прекращаем их поиск
                            successful_runs -= 1
                            if successful_runs == 0:
                                break
                    # изменение связей в БД
                    # debug: print('job_ebc_id', job[1], 'found_ebc_ids', found_ebc_ids)
                    if found_ebc_ids:
                        self.db.execute(
                            "UPDATE esi_blueprint_costs SET("
                            " ebc_job_id,"
                            " ebc_job_corporation_id,"
                            " ebc_job_activity,"
                            " ebc_job_product_type_id,"
                            " ebc_industry_payment,"
                            " ebc_tax,"
                            " ebc_updated_at)="
                            "(SELECT"
                            "  ebc_job_id,"
                            "  ebc_job_corporation_id,"
                            "  ebc_job_activity,"
                            "  ebc_job_product_type_id,"
                            "  ebc_industry_payment,"
                            "  ebc_tax,"
                            "  CURRENT_TIMESTAMP AT TIME ZONE 'GMT'"
                            " FROM"
                            "  esi_blueprint_costs"
                            " WHERE"
                            "  ebc_id=%(jid)s"
                            ")"
                            "WHERE"
                            " ebc_id IN (SELECT * FROM UNNEST(%(ids)s));",
                            {'jid': job[1],
                             'ids': found_ebc_ids,
                             }
                        )
                        if successful_runs == 0:
                            self.db.execute(
                                "UPDATE esi_blueprint_costs SET"
                                " ebc_job_successful_runs=0,"
                                " ebc_transaction_type='p',"
                                " ebc_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT' "
                                "WHERE ebc_id=%(jid)s;",
                                {'jid': job[1],
                                 }
                            )
                        else:
                            self.db.execute(
                                "UPDATE esi_blueprint_costs SET"
                                " ebc_job_successful_runs=%(sr)s,"
                                " ebc_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT' "
                                "WHERE ebc_id=%(jid)s;",
                                {'jid': job[1],
                                 'sr': successful_runs,
                                 }
                            )
                        used_ebc_ids += found_ebc_ids
            del used_ebc_ids

        del unlinked_blueprint_types

    # -------------------------------------------------------------------------
    # characters/{character_id}/industry/jobs/
    # -------------------------------------------------------------------------

    def insert_or_update_character_industry_jobs(self, data, character_id, updated_at):
        """ inserts character industry job data into database

        :param data: character industry job data
        """
        # print("INSERT {} {} {}".format(data['job_id'], data['activity_id'], data['status']))
        # return
        # { "activity_id": 3,
        #   "blueprint_id": 1035690963115,
        #   "blueprint_location_id": 1035704750584,
        #   "blueprint_type_id": 12055,
        #   "cost": 319478.0,
        #   "duration": 617929,
        #   "end_date": "2021-03-24T21:42:07Z",
        #   "facility_id": 1035620697572,
        #   "installer_id": 2116252240,
        #   "job_id": 453460908,
        #   "licensed_runs": 60,
        #   "station_id": 1035620697572,
        #   "output_location_id": 1035704750584,
        #   "probability": 1.0,
        #   "product_type_id": 12055,
        #   "runs": 9,
        #   "start_date": "2021-03-17T18:03:18Z",
        #   "status": "active"
        # }
        self.db.execute(
            "INSERT INTO esi_pilot_industry_jobs("
            " epj_character_id,"
            " epj_job_id,"
            " epj_installer_id,"
            " epj_facility_id,"
            " epj_station_id,"
            " epj_activity_id,"
            " epj_blueprint_id,"
            " epj_blueprint_type_id,"
            " epj_blueprint_location_id,"
            " epj_output_location_id,"
            " epj_runs,"
            " epj_cost,"
            " epj_licensed_runs,"
            " epj_probability,"
            " epj_product_type_id,"
            " epj_status,"
            " epj_duration,"
            " epj_start_date,"
            " epj_end_date,"
            " epj_pause_date,"
            " epj_completed_date,"
            " epj_completed_character_id,"
            " epj_successful_runs,"
            " epj_created_at,"
            " epj_updated_at) "
            "VALUES ("
            " %(ch)s,"
            " %(id)s,"
            " %(who)s,"
            " %(fac)s,"
            " %(loc)s,"
            " %(a)s,"
            " %(bp)s,"
            " %(bty)s,"
            " %(bpl)s,"
            " %(out)s,"
            " %(r)s,"
            " %(c)s,"
            " %(lr)s,"
            " %(p)s,"
            " %(pty)s,"
            " %(s)s,"
            " %(d)s,"
            " %(sdt)s,"
            " %(edt)s,"
            " %(pdt)s,"
            " %(cdt)s,"
            " %(cwho)s,"
            " %(sr)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_epj DO UPDATE SET"
            " epj_status=%(s)s,"
            " epj_pause_date=%(pdt)s,"
            " epj_completed_date=%(cdt)s,"
            " epj_completed_character_id=%(cwho)s,"
            " epj_successful_runs=%(sr)s,"
            " epj_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'ch': character_id,
             'id': data['job_id'],
             'who': data['installer_id'],
             'fac': data['facility_id'],
             'loc': data['station_id'],
             'a': data['activity_id'],
             'bp': data['blueprint_id'],
             'bty': data['blueprint_type_id'],
             'bpl': data['blueprint_location_id'],
             'out': data['output_location_id'],
             'r': data['runs'],
             'c': data.get('cost', None),
             'lr': data.get('licensed_runs', None),
             'p': data.get('probability', None),
             'pty': data.get('product_type_id', None),
             's': data['status'],
             'd': data['duration'],
             'sdt': data['start_date'],
             'edt': data['end_date'],
             'pdt': data.get('pause_date', None),
             'cdt': data.get('completed_date', None),
             'cwho': data.get('completed_character_id', None),
             'sr': data.get('successful_runs', None),
             'at': updated_at,
             }
        )

    def get_exist_character_industry_jobs(self, character_id: int, oldest_delivered_job=None):
        if oldest_delivered_job:
            where = "epj_character_id={ch} AND " \
                    "(epj_completed_date IS NULL OR (" \
                    " epj_status in ('delivered','cancelled') AND epj_job_id>={job})" \
                    ")".\
                    format(ch=character_id, job=oldest_delivered_job)
        else:
            where = "epj_character_id={ch} AND epj_completed_date IS NULL".\
                    format(ch=character_id)
        rows = self.db.select_all_rows(
            "SELECT"
            " epj_character_id,"
            " epj_job_id,"
            " epj_installer_id,"
            " epj_facility_id,"
            " epj_station_id,"
            " epj_activity_id,"
            " epj_blueprint_id,"
            " epj_blueprint_type_id,"
            " epj_blueprint_location_id,"
            " epj_output_location_id,"
            " epj_runs,"
            " epj_cost,"
            " epj_licensed_runs,"
            " epj_probability,"
            " epj_product_type_id,"
            " epj_status,"
            " epj_duration,"
            " epj_start_date,"
            " epj_end_date,"
            " epj_pause_date,"
            " epj_completed_date,"
            " epj_completed_character_id,"
            " epj_successful_runs,"
            " epj_updated_at "
            "FROM esi_pilot_industry_jobs "
            "WHERE {};".
            format(where)
        )
        if rows is None:
            return []
        data = []
        for row in rows:
            ext = {'updated_at': row[23], 'character_id': row[0]}
            data_item = {
                'job_id': row[1],
                'installer_id': row[2],
                'facility_id': row[3],
                'station_id': row[4],
                'activity_id': row[5],
                'blueprint_id': row[6],
                'blueprint_type_id': row[7],
                'blueprint_location_id': row[8],
                'output_location_id': row[9],
                'runs': row[10],
                'cost': row[11],
                'status': row[15],
                'duration': row[16],
                'start_date': row[17],
                'end_date': row[18],
                'ext': ext,
            }
            if row[12] is not None:
                data_item.update({'licensed_runs': row[12]})
            if row[13] is not None:
                data_item.update({'probability': row[13]})
            if row[14]:
                data_item.update({'product_type_id': row[14]})
            if row[19]:
                data_item.update({'pause_date': row[19]})
            if row[20]:
                data_item.update({'completed_date': row[20]})
            if row[21]:
                data_item.update({'completed_character_id': row[21]})
            if row[22] is not None:
                data_item.update({'successful_runs': row[22]})
            data.append(data_item)
        return data

    # -------------------------------------------------------------------------
    # /corporations/{corporation_id}/wallets/{division}/journal/
    # -------------------------------------------------------------------------

    def get_last_known_corporation_wallet_journal_ids(self, corporation_id: int):
        rows = self.db.select_all_rows(
            "SELECT MAX(ecwj_reference_id), ecwj_division "
            "FROM esi_corporation_wallet_journals "
            "WHERE ecwj_corporation_id=%s "
            "GROUP BY 2;",
            int(corporation_id),
        )
        if rows is None:
            return None
        return rows

    def insert_corporation_wallet_journals(self, data, corporation_id: int, division: int, updated_at):
        """ inserts corporation wallet journal data into database

        :param data: corporation wallet journal data
        """
        # { "amount": -6957699.0,
        #   "balance": 5659128174.57,
        #   "context_id": 455488775,
        #   "context_id_type": "industry_job_id",
        #   "date": "2021-04-08T20:53:27Z",
        #   "description": "Material efficiency research job fee between R Industry and Secure Commerce Commission (Job ID: 455488775)",
        #   "first_party_id": 98677876,
        #   "id": 19192237879,
        #   "reason": "",
        #   "ref_type": "researching_material_productivity",
        #   "second_party_id": 1000132
        # }
        self.db.execute(
            "INSERT INTO esi_corporation_wallet_journals("
            " ecwj_corporation_id,"
            " ecwj_division,"
            " ecwj_reference_id,"
            " ecwj_date,"
            " ecwj_ref_type,"
            " ecwj_first_party_id,"
            " ecwj_second_party_id,"
            " ecwj_amount,"
            " ecwj_balance,"
            " ecwj_reason,"
            " ecwj_tax_receiver_id,"
            " ecwj_tax,"
            " ecwj_context_id,"
            " ecwj_context_id_type,"
            " ecwj_description,"
            " ecwj_created_at) "
            "VALUES("
            " %(co)s,"
            " %(d)s,"
            " %(id)s,"
            " %(dt)s,"
            " %(rt)s,"
            " %(fp)s,"
            " %(sp)s,"
            " %(a)s,"
            " %(b)s,"
            " %(r)s,"
            " %(tr)s,"
            " %(t)s,"
            " %(c)s,"
            " %(ct)s,"
            " %(txt)s,"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ecwj DO NOTHING;",
            {'co': corporation_id,
             'd': division,
             'id': data['id'],
             'dt': data['date'],
             'rt': data['ref_type'],
             'fp': data.get('first_party_id', None),
             'sp': data.get('second_party_id', None),
             'a': data.get('amount', None),
             'b': data.get('balance', None),
             'r': data.get('reason', None),
             'tr': data.get('tax_receiver_id', None),
             't': data.get('tax', None),
             'c': data.get('context_id', None),
             'ct': data.get('context_id_type', None),
             'txt': data['description'],
             'at': updated_at,
             }
        )

    # -------------------------------------------------------------------------
    # /characters/{character_id}/wallet/journal/
    # -------------------------------------------------------------------------

    def get_last_known_character_wallet_journal_id(self, character_id: int):
        row = self.db.select_one_row(
            "SELECT MAX(epwj_reference_id) "
            "FROM esi_pilot_wallet_journals "
            "WHERE epwj_character_id=%s;",
            int(character_id),
        )
        if row is None:
            return None
        return row[0]

    def insert_character_wallet_journals(self, data, character_id: int, updated_at):
        """ inserts character wallet journal data into database

        :param data: character wallet journal data
        """
        # { "amount": -150000.0,
        #   "balance": 4504038849.3722,
        #   "date": "2021-09-21T17:50:57Z",
        #   "description": "Market order commission to broker authorized by: Qandra Si",
        #   "first_party_id": 2116129465,
        #   "id": 19690193063,
        #   "reason": "",
        #   "ref_type": "brokers_fee",
        #   "second_party_id": 98551088
        # }
        self.db.execute(
            "INSERT INTO esi_pilot_wallet_journals("
            " epwj_character_id,"
            " epwj_reference_id,"
            " epwj_date,"
            " epwj_ref_type,"
            " epwj_first_party_id,"
            " epwj_second_party_id,"
            " epwj_amount,"
            " epwj_balance,"
            " epwj_reason,"
            " epwj_tax_receiver_id,"
            " epwj_tax,"
            " epwj_context_id,"
            " epwj_context_id_type,"
            " epwj_description,"
            " epwj_created_at) "
            "VALUES("
            " %(ch)s,"
            " %(id)s,"
            " %(dt)s,"
            " %(rt)s,"
            " %(fp)s,"
            " %(sp)s,"
            " %(a)s,"
            " %(b)s,"
            " %(r)s,"
            " %(tr)s,"
            " %(t)s,"
            " %(c)s,"
            " %(ct)s,"
            " %(txt)s,"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_epwj DO NOTHING;",
            {'ch': character_id,
             'id': data['id'],
             'dt': data['date'],
             'rt': data['ref_type'],
             'fp': data.get('first_party_id', None),
             'sp': data.get('second_party_id', None),
             'a': data.get('amount', None),
             'b': data.get('balance', None),
             'r': data.get('reason', None),
             'tr': data.get('tax_receiver_id', None),
             't': data.get('tax', None),
             'c': data.get('context_id', None),
             'ct': data.get('context_id_type', None),
             'txt': data['description'],
             'at': updated_at,
             }
        )

    # -------------------------------------------------------------------------
    # /corporations/{corporation_id}/wallets/{division}/transactions/
    # -------------------------------------------------------------------------

    def get_last_known_corporation_wallet_transactions_ids(self, corporation_id: int):
        rows = self.db.select_all_rows(
            "SELECT MAX(ecwt_transaction_id), ecwt_division "
            "FROM esi_corporation_wallet_transactions "
            "WHERE ecwt_corporation_id=%s "
            "GROUP BY 2;",
            int(corporation_id),
        )
        if rows is None:
            return None
        return rows

    def insert_corporation_wallet_transactions(self, data, corporation_id: int, division: int, updated_at):
        """ inserts corporation wallet transactions data into database

        :param data: corporation wallet transactions data
        """
        # { "client_id": 2114281846,
        #   "date": "2021-08-15T18:32:38Z",
        #   "is_buy": false,
        #   "journal_ref_id": 19576191173,
        #   "location_id": 1030049082711,
        #   "quantity": 3,
        #   "transaction_id": 5673651174,
        #   "type_id": 21638,
        #   "unit_price": 1540000.0
        # }
        self.db.execute(
            "INSERT INTO esi_corporation_wallet_transactions("
            " ecwt_corporation_id,"
            " ecwt_division,"
            " ecwt_transaction_id,"
            " ecwt_date,"
            " ecwt_type_id,"
            " ecwt_location_id,"
            " ecwt_unit_price,"
            " ecwt_quantity,"
            " ecwt_client_id,"
            " ecwt_is_buy,"
            " ecwt_journal_ref_id,"
            " ecwt_created_at) "
            "VALUES("
            " %(co)s,"
            " %(d)s,"
            " %(id)s,"
            " %(dt)s,"
            " %(ty)s,"
            " %(loc)s,"
            " %(pr)s,"
            " %(q)s,"
            " %(cl)s,"
            " %(b)s,"
            " %(jr)s,"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ecwt DO NOTHING;",
            {'co': corporation_id,
             'd': division,
             'id': data['transaction_id'],
             'dt': data['date'],
             'ty': data['type_id'],
             'loc': data['location_id'],
             'pr': data['unit_price'],
             'q': data['quantity'],
             'cl': data['client_id'],
             'b': data['is_buy'],
             'jr': data['journal_ref_id'],
             'at': updated_at,
             }
        )

    # -------------------------------------------------------------------------
    # /characters/{character_id}/wallet/transactions/
    # -------------------------------------------------------------------------

    def get_last_known_character_wallet_transaction_id(self, character_id: int):
        row = self.db.select_one_row(
            "SELECT MAX(epwt_transaction_id) "
            "FROM esi_pilot_wallet_transactions "
            "WHERE epwt_character_id=%s;",
            int(character_id),
        )
        if row is None:
            return None
        return row[0]

    def insert_character_wallet_transactions(self, data, character_id: int, updated_at):
        """ inserts character wallet transactions data into database

        :param data: character wallet transactions data
        """
        # { "client_id": 2114844860,
        #   "date": "2021-09-22T18:30:48Z",
        #   "is_buy": false,
        #   "is_personal": false,
        #   "journal_ref_id": 19693288379,
        #   "location_id": 1034323745897,
        #   "quantity": 1,
        #   "transaction_id": 5697070564,
        #   "type_id": 2032,
        #   "unit_price": 853000.0
        #  }
        self.db.execute(
            "INSERT INTO esi_pilot_wallet_transactions("
            " epwt_character_id,"
            " epwt_transaction_id,"
            " epwt_date,"
            " epwt_type_id,"
            " epwt_location_id,"
            " epwt_unit_price,"
            " epwt_quantity,"
            " epwt_client_id,"
            " epwt_is_buy,"
            " epwt_is_personal,"
            " epwt_journal_ref_id,"
            " epwt_created_at) "
            "VALUES("
            " %(ch)s,"
            " %(id)s,"
            " %(dt)s,"
            " %(ty)s,"
            " %(loc)s,"
            " %(pr)s,"
            " %(q)s,"
            " %(cl)s,"
            " %(b)s,"
            " %(p)s,"
            " %(jr)s,"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_epwt DO NOTHING;",
            {'ch': character_id,
             'id': data['transaction_id'],
             'dt': data['date'],
             'ty': data['type_id'],
             'loc': data['location_id'],
             'pr': data['unit_price'],
             'q': data['quantity'],
             'cl': data['client_id'],
             'b': data['is_buy'],
             'p': data['is_personal'],
             'jr': data['journal_ref_id'],
             'at': updated_at,
             }
        )

    # -------------------------------------------------------------------------
    # /corporations/{corporation_id}/orders/
    # -------------------------------------------------------------------------

    def insert_or_update_corporation_orders(self, data, corporation_id: int, history, updated_at):
        """ inserts corporation order data into database

        :param data: corporation order data
        """
        # { "duration": 90,
        #   "issued": "2021-08-17T21:36:37Z",
        #   "issued_by": 2116129465,
        #   "location_id": 1036927076065,
        #   "order_id": 6061476548,
        #   "price": 28970000.0,
        #   "range": "region",
        #   "region_id": 10000050,
        #   "type_id": 28756,
        #   "volume_remain": 4,
        #   "volume_total": 4,
        #   "wallet_division": 1
        # }
        self.db.execute(
            "INSERT INTO esi_corporation_orders("
            " ecor_corporation_id,"
            " ecor_order_id,"
            " ecor_type_id,"
            " ecor_region_id,"
            " ecor_location_id,"
            " ecor_range,"
            " ecor_is_buy_order,"
            " ecor_price,"
            " ecor_volume_total,"
            " ecor_volume_remain,"
            " ecor_issued,"
            " ecor_issued_by,"
            " ecor_min_volume,"
            " ecor_wallet_division,"
            " ecor_duration,"
            " ecor_escrow,"
            " ecor_history,"
            " ecor_created_at,"
            " ecor_updated_at) "
            "VALUES ("
            " %(co)s,"
            " %(id)s,"
            " %(t)s,"
            " %(rid)s,"
            " %(loc)s,"
            " %(r)s,"
            " %(b)s,"
            " %(p)s,"
            " %(vt)s,"
            " %(vr)s,"
            " %(dt)s,"
            " %(who)s,"
            " %(mv)s,"
            " %(wd)s,"
            " %(d)s,"
            " %(e)s,"
            " %(h)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_ecor DO UPDATE SET"
            " ecor_price=%(p)s,"
            " ecor_volume_remain=%(vr)s,"
            " ecor_issued=%(dt)s,"
            " ecor_history=%(h)s,"
            " ecor_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'co': corporation_id,
             'id': data['order_id'],
             't': data['type_id'],
             'rid': data['region_id'],
             'loc': data['location_id'],
             'r': data['range'],
             'b': data.get('is_buy_order', False),  # esi все buy выдаёт как True, а все sell как None 
             'p': data['price'],
             'vt': data['volume_total'],
             'vr': data['volume_remain'],
             'dt': data['issued'],
             'who': data['issued_by'],
             'mv': data.get('min_volume', None),
             'wd': data['wallet_division'],
             'd': data['duration'],
             'e': data.get('escrow', None),
             'h': history,
             'at': updated_at,
             }
        )

    def get_active_corporation_orders(self, corporation_id: int):
        rows = self.db.select_all_rows(
            "SELECT"
            " ecor_corporation_id,"
            " ecor_order_id,"
            " ecor_type_id,"
            " ecor_region_id,"
            " ecor_location_id,"
            " ecor_range,"
            " ecor_is_buy_order,"
            " ecor_price,"
            " ecor_volume_total,"
            " ecor_volume_remain,"
            " ecor_issued,"
            " ecor_issued_by,"
            " ecor_min_volume,"
            " ecor_wallet_division,"
            " ecor_duration,"
            " ecor_escrow,"
            " ecor_updated_at "
            "FROM esi_corporation_orders "
            "WHERE ecor_corporation_id={co} AND NOT ecor_history;".
            format(co=corporation_id)
        )
        if rows is None:
            return []
        data = []
        for row in rows:
            ext = {'updated_at': row[16], 'corporation_id': row[0]}
            data_item = {
                'order_id': row[1],
                'type_id': row[2],
                'region_id': row[3],
                'location_id': row[4],
                'range': row[5],
                'price': row[7],
                'volume_total': row[8],
                'volume_remain': row[9],
                'issued': row[10],
                'issued_by': row[11],
                'wallet_division': row[13],
                'duration': row[14],
                'ext': ext,
            }
            if row[6]:
                data_item.update({'is_buy_order': row[6]})
            if row[12]:
                data_item.update({'min_volume': row[12]})
            if row[15]:
                data_item.update({'escrow': row[15]})
            data.append(data_item)
        return data

    def get_absent_corporation_orders_history(self, corporation_id: int, present_ids: typing.List[int]):
        rows = self.db.select_all_rows(
            "SELECT id FROM (SELECT UNNEST(ARRAY{ids}) as id) e "
            "WHERE e.id NOT IN (SELECT ecor_order_id FROM esi_corporation_orders WHERE ecor_corporation_id={co} AND ecor_history);".
            format(co=corporation_id, ids=present_ids)
        )
        data: typing.List[int] = []
        if rows is None:
            return data
        for row in rows:
            data.append(row[0])
        return data

    def discard_absent_corporation_orders(self, corporation_id: int, absent_ids: typing.List[int]):
        # тут иногда происходят исключения, добавляю отладку:
        print(corporation_id)
        print(absent_ids)
        self.db.execute(
            "UPDATE esi_corporation_orders "
            "SET ecor_history=true "
            "WHERE NOT ecor_history AND ecor_corporation_id=%s AND ecor_order_id IN (SELECT * FROM UNNEST(%s));",
            corporation_id,
            absent_ids
        )

    def discard_obsolete_corporation_orders(self):
        self.db.execute(
            "UPDATE esi_corporation_orders "
            "SET ecor_history=true "
            "FROM ("
            " SELECT ecor_corporation_id cid, ecor_order_id oid"
            " FROM esi_corporation_orders"
            " WHERE NOT ecor_history AND current_date > (ecor_issued+interval '1 day') + ecor_duration * interval '1 day'"
            ") o "
            "WHERE ecor_corporation_id=cid and ecor_order_id=oid;"
        )

    # -------------------------------------------------------------------------
    # /markets/prices/
    # -------------------------------------------------------------------------

    def get_last_known_markets_prices(self) \
            -> typing.Optional[typing.Tuple[typing.List[typing.Any], typing.List[typing.Any]]]:
        rows = self.db.select_all_rows(
            "SELECT"
            " emp_type_id,"
            " emp_adjusted_price,"
            " emp_average_price,"
            " emp_adj_updated_at,"
            " emp_avg_updated_at "
            "FROM esi_markets_prices;",
        )
        if rows is None:
            return None
        avg_data, adj_data = [], []
        for row in rows:
            data_item = {
                'type_id': row[0],
                'ext': {'updated_at': row[4]},
            }
            if row[2] is not None:
                data_item.update({'average_price': row[2]})
            avg_data.append(data_item)
            # ---
            data_item = {
                'type_id': row[0],
                'ext': {'updated_at': row[3]},
            }
            if row[1] is not None:
                data_item.update({'adjusted_price': row[1]})
            adj_data.append(data_item)
        return avg_data, adj_data

    def insert_or_update_markets_price(
            self,
            data,
            updated_avg_at: typing.Optional[datetime.datetime],
            updated_adj_at: typing.Optional[datetime.datetime]) -> None:
        """ inserts markets price data into database

        :param data: market price data
        :param updated_avg_at: время обновления average_price
        :param updated_adj_at: время обновления adjusted_price
        """
        # { "adjusted_price": 306988.09,
        #   "average_price": 306292.67,
        #   "type_id": 32772
        # }

        if updated_adj_at is not None:
            if updated_avg_at is not None:
                on_conflict: str = \
                    "emp_adjusted_price=%(aj)s," \
                    "emp_average_price=%(av)s," \
                    "emp_adj_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s," \
                    "emp_avg_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s"
            else:
                on_conflict: str = \
                    "emp_adjusted_price=%(aj)s," \
                    "emp_adj_updated_at=TIMESTAMP WITHOUT TIME ZONE %(atj)s"
        else:
            on_conflict: str = \
                "emp_average_price=%(av)s," \
                "emp_avg_updated_at=TIMESTAMP WITHOUT TIME ZONE %(atv)s"

        self.db.execute(
            "INSERT INTO esi_markets_prices("
            " emp_type_id,"
            " emp_adjusted_price,"
            " emp_average_price,"
            " emp_created_at,"
            " emp_adj_updated_at,"
            " emp_avg_updated_at) "
            "VALUES ("
            " %(t)s,"
            " %(aj)s,"
            " %(av)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s,"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_emp DO UPDATE SET " + on_conflict + ";",
            {'t': data['type_id'],
             'aj': data.get('adjusted_price', None),
             'av': data.get('average_price', None),
             'at': updated_adj_at if updated_adj_at is not None else updated_avg_at,
             'atj': updated_adj_at,
             'atv': updated_avg_at,
             }
        )

    # -------------------------------------------------------------------------
    # /markets/{region_id}/history/
    # -------------------------------------------------------------------------

    def select_market_type_ids(self, region_id: int):
        rows = self.db.select_all_rows(
            "SELECT"
            " sdet_type_id,"
            " mrh.last_date "
            "FROM eve_sde_type_ids"
            " LEFT OUTER JOIN ("
            "  SELECT emrh_type_id AS type_id, MAX(emrh_date) AS last_date"
            "  FROM esi_markets_region_history"
            "  WHERE emrh_region_id = %s"
            "  GROUP BY emrh_type_id"
            " ) mrh ON (mrh.type_id = sdet_type_id) "
            "WHERE"
            #debug:" sdet_type_id in (40556, 2195) AND"
            " sdet_published AND"
            " sdet_market_group_id IS NOT NULL;",
            region_id
        )
        if rows is None:
            return None
        return rows

    def insert_or_update_region_market_history(self, region_id: int, type_id: int, data, updated_at):
        """ inserts region' market price history data into database

        :param data: region market history data
        """
        # { "average": 11490000,
        #   "date": "2020-07-03",
        #   "highest": 11490000,
        #   "lowest": 11490000,
        #   "order_count": 1,
        #   "volume": 22
        # }
        self.db.execute(
            "INSERT INTO esi_markets_region_history("
            " emrh_region_id,"
            " emrh_type_id,"
            " emrh_date,"
            " emrh_average,"
            " emrh_highest,"
            " emrh_lowest,"
            " emrh_order_count,"
            " emrh_volume) "
            "VALUES ("
            " %(r)s,"
            " %(t)s,"
            " %(dt)s,"
            " %(a)s,"
            " %(h)s,"
            " %(l)s,"
            " %(o)s,"
            " %(v)s) "
            "ON CONFLICT ON CONSTRAINT pk_emrh DO NOTHING;",
            {'r': region_id,
             't': type_id,
             'dt': data['date'],
             'a': data['average'],
             'h': data['highest'],
             'l': data['lowest'],
             'o': data['order_count'],
             'v': data['volume'],
             }
        )

    # -------------------------------------------------------------------------
    # /markets/region_id/orders/
    # /markets/structures/structure_id/
    # -------------------------------------------------------------------------

    def get_market_location_orders_to_compare(self, location_id: int):
        data: typing.Dict[int, typing.Any] = {}
        rows = self.db.select_all_rows(
            "SELECT"
            " etho_order_id,"
            " etho_price,"
            " etho_volume_remain "
            # " etho_type_id,"
            # " etho_duration,"
            # " etho_is_buy,"
            # " etho_issued,"
            # " etho_min_volume,"
            # " etho_range,"
            # " etho_volume_total "
            "FROM esi_trade_hub_orders "
            "WHERE etho_location_id=%s;",
            location_id
        )
        if rows is None:
            return data
        for row in rows:
            order_id: int = int(row[0])
            data[order_id] = {
                'order_id': order_id,
                'price': row[1],
                'volume_remain': row[2],
                # остальные поля ордера не меняются (выдаём набор данных только для сравнения)
                # 'duration': row[2],
                # 'is_buy_order': row[3],
                # 'issued': row[4],
                # 'location_id': location_id,
                # 'min_volume': row[5],
                # 'range': row[7],
                # 'system_id': row[?],  # этого параметра у структур нет
                # 'type_id': row[1],
                # 'volume_total': row[8],
            }
        return data

    def insert_or_update_market_location_order(self, location_id: int, data, updated_at):
        """ inserts markets order data into database

        :param data: market price data
        """
        # { "duration": 90,
        #   "is_buy_order": false,
        #   "issued": "2021-12-28T09:13:08Z",
        #   "location_id": 60003760,
        #   "min_volume": 1,
        #   "order_id": 6160167353,
        #   "price": 13000.0,
        #   "range": "region",
        #   "system_id": 30000142,
        #   "type_id": 57457,
        #   "volume_remain": 20000,
        #   "volume_total": 20000
        # }
        self.db.execute(
            "INSERT INTO esi_trade_hub_orders("
            " etho_location_id,"
            " etho_order_id,"
            " etho_type_id,"
            " etho_duration,"
            " etho_is_buy,"
            " etho_issued,"
            " etho_min_volume,"
            " etho_price,"
            " etho_range,"
            " etho_volume_remain,"
            " etho_volume_total,"
            " etho_created_at,"
            " etho_updated_at) "
            "VALUES ("
            " %(l)s,"
            " %(o)s,"
            " %(t)s,"
            " %(d)s,"
            " %(b)s,"
            " %(dt)s,"
            " %(mv)s,"
            " %(p)s,"
            " %(r)s,"
            " %(vr)s,"
            " %(vt)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_etho DO UPDATE SET"
            " etho_price=%(p)s,"
            " etho_volume_remain=%(vr)s,"
            " etho_issued=%(dt)s,"
            " etho_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'l': location_id,
             'o': data['order_id'],
             't': data['type_id'],
             'd': data['duration'],
             'b': data['is_buy_order'],
             'dt': data['issued'],
             'mv': data['min_volume'],
             'p': data['price'],
             'r': data['range'],
             'vr': data['volume_remain'],
             'vt': data['volume_total'],
             'at': updated_at,
             }
        )

    def delete_market_location_order(self, location_id: int, order_id: int):
        self.db.execute(
            "DELETE FROM esi_trade_hub_orders "
            "WHERE etho_location_id=%s AND etho_order_id=%s;",
            location_id,
            order_id
        )

    def sync_market_location_prices_with_orders(self, location_id: int):
        # синхронизация данных в таблице esi_trade_hub_prices (с сохранением
        # накопленных данных, по сведениям из таблицы esi_trade_hub_orders)
        self.db.execute(
            "CALL ethp_sync_with_etho(%s);",
            location_id
        )

    def sync_market_location_history_with_orders(self, location_id: int):
        # синхронизация данных в таблице esi_trade_hub_history (с сохранением
        # накопленных данных, по сведениям из таблицы esi_trade_hub_orders)
        self.db.execute(
            "CALL ethh_sync_with_etho(%s);",
            location_id
        )

    def sync_market_location_history_with_corp_orders_by_loc(self, location_id: int):
        # синхронизация данных в таблице esi_trade_hub_history (с сохранением
        # накопленных данных, по сведениям из таблицы esi_corporation_orders)
        self.db.execute(
            "CALL ethh_sync_with_ecor_by_loc(%s);",
            location_id
        )

    def sync_market_location_history_with_corp_orders_by_corp(self, corporation_id: int):
        # синхронизация данных в таблице esi_trade_hub_history (с сохранением
        # накопленных данных, по сведениям из таблицы esi_corporation_orders)
        self.db.execute(
            "CALL ethh_sync_with_ecor_by_corp(%s);",
            corporation_id
        )

    # -------------------------------------------------------------------------
    # /universe/categories/
    # /universe/categories/{category_id}/
    # -------------------------------------------------------------------------

    def is_exist_category_id(self, id: int):
        return self.is_exist_something(id, 'eve_sde_category_ids', 'sdec_category_id')

    def get_exist_category_ids(self):
        return self.get_exist_ids('eve_sde_category_ids', 'sdec_category_id')

    def insert_or_update_category_id(self, data):
        """ inserts category_id' data into database
        """
        # { "category_id": 17,
        #   "groups": [267, 280, ... 4165],
        #   "name": "Commodity",
        #   "published": true
        # }
        self.db.execute(
            "INSERT INTO eve_sde_category_ids("
            " sdec_category_id,"
            " sdec_category_name,"
            " sdec_published) "
            "VALUES ("
            " %(c)s,"
            " %(nm)s,"
            " %(p)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdec DO UPDATE SET"
            " sdec_category_name=%(nm)s,"
            " sdec_published=%(p)s;",
            {'c': data['category_id'],
             'nm': data['name'],
             'p': data['published'],
             }
        )

    def update_category_id_as_not_published(self, category_id: int):
        """ mark category_id as unpublished
        """
        self.db.execute(
            "UPDATE eve_sde_category_ids SET"
            " sdec_published=false "
            "WHERE sdec_category_id=%s;",
            category_id
        )

    # -------------------------------------------------------------------------
    # /universe/groups/
    # /universe/groups/{group_id}/
    # -------------------------------------------------------------------------

    def is_exist_group_id(self, id: int):
        return self.is_exist_something(id, 'eve_sde_group_ids', 'sdecg_group_id')

    def get_exist_group_ids(self):
        return self.get_exist_ids('eve_sde_group_ids', 'sdecg_group_id')

    def insert_or_update_group_id(self, data):
        """ inserts group_id' data into database
        """
        # { "category_id": 17,
        #   "group_id": 4145,
        #   "name": "Warp Matrix Filaments",
        #   "published": true,
        #   "types": [60633, 61654, 61655, 61656, 62055, 62056, 62057]
        # }
        self.db.execute(
            "INSERT INTO eve_sde_group_ids("
            " sdecg_group_id,"
            " sdecg_category_id,"
            " sdecg_group_name,"
            " sdecg_published) "
            "VALUES ("
            " %(g)s,"
            " %(c)s,"
            " %(nm)s,"
            " %(p)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdecg DO UPDATE SET"
            " sdecg_category_id=%(c)s,"
            " sdecg_group_name=%(nm)s,"
            " sdecg_published=%(p)s;",
            {'g': data['group_id'],
             'c': data['category_id'],
             'nm': data['name'],
             'p': data['published'],
             }
        )

    def update_group_id_as_not_published(self, group_id: int):
        """ mark group_id as unpublished
        """
        self.db.execute(
            "UPDATE eve_sde_group_ids SET"
            " sdecg_published=false "
            "WHERE sdecg_group_id=%s;",
            group_id
        )

    # -------------------------------------------------------------------------
    # /markets/groups/
    # /markets/groups/{market_group_id}/
    # -------------------------------------------------------------------------

    def is_exist_market_group_id(self, id: int):
        return self.is_exist_something(id, 'eve_sde_market_groups', 'sdeg_group_id')

    def get_exist_market_group_ids(self):
        return self.get_exist_ids('eve_sde_market_groups', 'sdeg_group_id')

    def insert_or_update_market_group_id(self, data):
        """ inserts market_group_id' data into database
        """
        # { "description": "Filaments connected to Abyssal pockets with Exotic Particle Storms",
        #   "market_group_id": 2457,
        #   "name": "Exotic Filaments",
        #   "parent_group_id": 2456,
        #   "types": [56133, 47889, 62056, 62057, 62055, 56141, 47888, 47761, 47890, 47891, 61654, 61655, 61656, 60633]
        # }
        self.db.execute(
            "INSERT INTO eve_sde_market_groups("
            " sdeg_group_id,"
            " sdeg_parent_id,"
            " sdeg_semantic_id,"  # TODO: доделать импорт идентификатора семантики
            " sdeg_group_name) "
            "VALUES ("
            " %(g)s,"
            " %(p)s,"
            " %(g)s,"
            " %(nm)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdeg DO UPDATE SET"
            " sdeg_parent_id=%(p)s,"
            " sdeg_group_name=%(nm)s;",
            {'g': data['market_group_id'],
             'p': data.get('parent_group_id'),
             'nm': data['name'],
             }
        )

    # -------------------------------------------------------------------------
    # /universe/types/
    # /universe/types/{type_id}/
    # -------------------------------------------------------------------------

    def is_exist_type_id(self, id: int):
        return self.is_exist_something(id, 'eve_sde_type_ids', 'sdet_type_id')

    def get_exist_type_ids(self):
        return self.get_exist_ids('eve_sde_type_ids', 'sdet_type_id')

    def get_universe_items_with_names(self):
        # выбираем (пока) только идентификаторы предметов типа 379 Cargo Containers
        """
        # 2233,  # Customs Office
        3293,  # Medium Standard Container
        3296,  # Large Standard Container
        3297,  # Small Standard Container
        3465,  # Large Secure Container
        3466,  # Medium Secure Container
        3467,  # Small Secure Container
        11488,  # Huge Secure Container
        11489,  # Giant Secure Container
        17363,  # Small Audit Log Secure Container
        17364,  # Medium Audit Log Secure Container
        17365,  # Large Audit Log Secure Container
        17366,  # Station Container
        17367,  # Station Vault Container
        17368,  # Station Warehouse Container
        24445,  # Giant Freight Container
        33003,  # Enormous Freight Container
        33005,  # Huge Freight Container
        33007,  # Large Freight Container
        33009,  # Medium Freight Container
        33011,  # Small Freight Container
        # 35825,  # Raitaru
        # 35826,  # Azbel
        # 35827,  # Sotiyo
        # 35828,  # Medium Laboratory
        # 35829,  # Large Laboratory
        # 35830,  # X-Large Laboratory
        # 35832,  # Astrahus
        # 35833,  # Fortizar
        # 35834,  # Keepstar
        # 35835,  # Athanor
        # 35836,  # Tatara
        # 11192,  # Buzzard ... (market_group_semantic=4)
        """
        tids = self.db.select_all_rows(
            "SELECT sdet_type_id "
            "FROM eve_sde_type_ids "
            "WHERE sdet_market_group_id IN ("
            " SELECT sdeg_group_id"
            " FROM eve_sde_market_groups"
            " WHERE sdeg_parent_id=379"
            " union"
            " SELECT id"
            " FROM eve_sde_market_groups_semantic"
            " WHERE semantic_id=4"
            ");"
        )
        return tids

    def remove_obsolete_type_ids_marker_from_dictionary(self):
        """ removes type_id=-1 from database (Waiting automatic data update from ESI)
        """
        self.db.execute("DELETE FROM eve_sde_type_ids WHERE sdet_type_id=-1;")

    def get_obsolete_type_ids_from_dictionary(self):
        # данные о packed volume нельзя получить из Static Data Interface, приходится загружать по ESI, а это значит,
        # что если в БД нет этих данных то данные в БД были добавлены из SDI... проверяем
        rows = self.db.select_all_rows(
            "SELECT t.sdet_type_id "
            "FROM"
            " eve_sde_type_ids t,"
            " (SELECT count(1) AS refresh FROM eve_sde_type_ids WHERE sdet_type_id=-1) need "
            "WHERE"
            " sdet_type_id>=0 and ("
            "  need.refresh<>0 or"
            "  sdet_packaged_volume is null"
            " );"
        )
        if rows is None:
            return None
        return [int(r[0]) for r in rows]

    def select_unknown_type_ids(self):
        rows = self.db.select_all_rows(
            "SELECT DISTINCT t.id "
            "FROM ("
            " SELECT DISTINCT eca_type_id AS id FROM esi_corporation_assets"
            " union"
            " SELECT DISTINCT ecb_type_id FROM esi_corporation_blueprints"
            " union"
            " SELECT DISTINCT ecj_blueprint_type_id FROM esi_corporation_industry_jobs"
            " union"
            " SELECT DISTINCT ecj_product_type_id FROM esi_corporation_industry_jobs"
            " union"
            " SELECT DISTINCT ecwt_type_id FROM esi_corporation_wallet_transactions"
            " union"
            " SELECT DISTINCT ecor_type_id FROM esi_corporation_orders"
            " union"
            " SELECT DISTINCT emp_type_id FROM esi_markets_prices"
            " union"
            " SELECT DISTINCT ethp_type_id FROM esi_trade_hub_prices"
            # те же данные: " union"
            # те же данные: " SELECT DISTINCT etho_type_id FROM esi_trade_hub_orders"
            " union"
            " SELECT DISTINCT ethh_type_id FROM esi_trade_hub_history"
            ") t "
            "except "
            "SELECT sdet_type_id FROM eve_sde_type_ids;"
        )
        if rows is None:
            return None
        return [int(r[0]) for r in rows if r[0] is not None]

    def update_type_id_as_not_published(self, type_id: int):
        """ mark type_id as unpublished
        """
        self.db.execute(
            "UPDATE eve_sde_type_ids SET"
            " sdet_published=false,"
            " sdet_packaged_volume=COALESCE(sdet_packaged_volume,0) "  # важно отсутствующий в ESI предмет пометить packed not null, иначе он постоянно будет проситься обновления
            "WHERE sdet_type_id=%s;",
            type_id
        )

    def insert_or_update_type_id(self, type_id: int, data, updated_at):
        """ inserts type_id' data into database

        :param data: item type market history data
        """
        # { "capacity": 0,
        #   "description": "Contains stylish 'Imperial Loyalist' pants for both men and women to celebrate Foundation Day YC123.",
        #   "group_id": 1194,
        #   "icon_id": 24297,
        #   "mass": 0,
        #   "name": "Amarr Foundation Day Pants Crate",
        #   "packaged_volume": 0.1,
        #   "portion_size": 1,
        #   "published": true,
        #   "radius": 1,
        #   "type_id": 59978,
        #   "volume": 0.1
        # }
        self.db.execute(
            "INSERT INTO eve_sde_type_ids("
            " sdet_type_id,"
            " sdet_type_name,"
            " sdet_group_id,"
            " sdet_volume,"
            " sdet_capacity,"
            # не передаётся: " sdet_base_price,"
            " sdet_published,"
            " sdet_market_group_id,"
            # не передаётся: " sdet_meta_group_id,"  # этот параметр получаем из sde (esi его не выдаёт)
            " sdet_tech_level,"  # этот параметр получаем только по esi (из sde его надо читать из атрибутов)
            " sdet_icon_id,"
            " sdet_packaged_volume,"
            " sdet_created_at) "
            "VALUES ("
            " %(t)s,"
            " %(nm)s,"
            " %(g)s,"
            " %(v)s,"
            " %(c)s,"
            # не передаётся: " %(bp)s,"
            " %(p)s,"
            " %(mkg)s,"
            # не передаётся: " %(mtg)s,"  # этот параметр получаем из sde (esi его не выдаёт)
            " %(tl)s,"
            " %(i)s,"
            " %(pv)s,"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdet DO UPDATE SET"
            " sdet_type_name=%(nm)s,"
            " sdet_group_id=%(g)s,"
            " sdet_volume=%(v)s,"
            " sdet_capacity=%(c)s,"
            " sdet_published=%(p)s,"
            " sdet_market_group_id=%(mkg)s,"
            # " sdet_meta_group_id=%(mtg)s,"  # этот параметр получаем из sde (esi его не выдаёт)
            " sdet_tech_level=%(tl)s,"
            " sdet_icon_id=%(i)s,"
            " sdet_packaged_volume=%(pv)s;",
            {'t': type_id,
             'nm': data['name'],
             'g': data['group_id'],
             'v': data.get('volume', None),
             'c': data.get('capacity', None),
             # не передаётся: 'bp': None,
             'p': data['published'],
             'mkg': data.get('market_group_id', None),
             'tl': next((x['value'] for x in data.get('dogma_attributes', []) if x['attribute_id'] == 422), None),
             'i': data.get('icon_id', None),
             'pv': data.get('packaged_volume', None),
             'at': updated_at
             }
        )

    # -------------------------------------------------------------------------
    # /industry/systems/
    # -------------------------------------------------------------------------

    def get_industry_systems(self):
        rows = self.db.select_all_rows(
            "SELECT"
            " eis_system_id,"
            " eis_manufacturing,"
            " eis_research_te,"
            " eis_research_me,"
            " eis_copying,"
            " eis_invention,"
            " eis_reaction,"
            " eis_updated_at "
            "FROM esi_industry_systems;",
        )
        if rows is None:
            return None
        data = []
        for row in rows:
            ext = {'updated_at': row[7]}
            data_item = {
                'system_id': row[0],
                'manufacturing': row[1],
                'research_te': row[2],
                'research_me': row[3],
                'copying': row[4],
                'invention': row[5],
                'reaction': row[6],
                'ext': ext,
            }
            data.append(data_item)
        return data

    def insert_or_update_industry_systems(self, data, updated_at):
        """ inserts industry systems data into database

        :param data: industry cost inicies data in solar system
        """
        # {"cost_indices":
        #  [
        #   {"activity": "manufacturing",
        #    "cost_index": 0.0625
        #   },
        #   {"activity": "researching_time_efficiency",
        #    "cost_index": 0.0161
        #   },
        #   {"activity": "researching_material_efficiency",
        #    "cost_index": 0.0178
        #   },
        #   {"activity": "copying",
        #    "cost_index": 0.0381
        #   },
        #   {"activity": "invention",
        #    "cost_index": 0.1446
        #   },
        #   {"activity": "reaction",
        #    "cost_index": 0.0306
        #   }
        #  ],
        #  "solar_system_id": 30001115
        # }
        self.db.execute(
            "INSERT INTO esi_industry_systems("
            " eis_system_id,"
            " eis_manufacturing,"
            " eis_research_te,"
            " eis_research_me,"
            " eis_copying,"
            " eis_invention,"
            " eis_reaction,"
            " eis_created_at,"
            " eis_updated_at) "
            "VALUES ("
            " %(ss)s,"
            " %(m)s,"
            " %(me)s,"
            " %(te)s,"
            " %(c)s,"
            " %(i)s,"
            " %(r)s,"
            " CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %(at)s) "
            "ON CONFLICT ON CONSTRAINT pk_eis DO UPDATE SET"
            " eis_manufacturing=%(m)s,"
            " eis_research_te=%(te)s,"
            " eis_research_me=%(me)s,"
            " eis_copying=%(c)s,"
            " eis_invention=%(i)s,"
            " eis_reaction=%(r)s,"
            " eis_updated_at=TIMESTAMP WITHOUT TIME ZONE %(at)s;",
            {'ss': data['system_id'],
             'm': data['manufacturing'],
             'te': data['research_te'],
             'me': data['research_me'],
             'c': data['copying'],
             'i': data['invention'],
             'r': data['reaction'],
             'at': updated_at,
             }
        )

    # -------------------------------------------------------------------------
    # [<conveyor_formulas]
    # -------------------------------------------------------------------------

    def actualize_conveyor_formulas_calculus(self):
        self.db.execute("CALL cfc_full_calculus();")

    # -------------------------------------------------------------------------
    # [<market_hubs]
    # -------------------------------------------------------------------------

    class MarketHub:
        def __init__(self, row: typing.Dict[int, typing.Union[int, str, bool]]):
            self.region_id: int = int(row[0])  # 'region_id'
            self.constellation_id: int = int(row[1])  # 'constellation_id'
            self.solar_system_id: int = int(row[2])  # 'solar_system_id'
            self.trade_hub_id: int = int(row[3])  # 'trade_hub_id'
            self.region: str = row[4]  # 'region'
            self.constellation: str = row[5]  # 'constellation'
            self.solar_system: str = row[6]  # 'solar_system'
            self.trade_hub: str = row[7]  # 'trade_hub'
            self.archive: bool = row[8]  # 'archive'
            self.active: bool = not self.archive
            self.trader_corporation: typing.Optional[str] = row[9]  # trader_corporation
            self.is_user_structure: bool = self.trade_hub_id >= 1000000000000
            self.is_nonuser_station: bool = not self.is_user_structure

    def get_active_market_hubs(self) -> typing.Optional[typing.List[MarketHub]]:
        rows = self.db.select_all_rows("""
select
 solar_systems.region_id,
 solar_systems.constellation_id,
 solar_systems.solar_system_id,
 hubs.mh_hub_id trade_hub_id,
 solar_systems.region,
 solar_systems.constellation,
 solar_systems.solar_system,
 stations.name trade_hub,
 hubs.mh_archive archive,
 corporations.eco_name trader_corporation
from
 qi.market_hubs hubs
  left outer join qi.esi_corporations corporations on (corporations.eco_corporation_id=hubs.mh_trader_corp),
 qi.esi_known_stations stations,
 qi.eve_sde_solar_systems solar_systems
where
 hubs.mh_hub_id=stations.location_id and
 solar_systems.solar_system_id=stations.solar_system_id;""")
        if rows is None:
            return None
        data: typing.Optional[typing.List[QSwaggerInterface.MarketHub]] = []
        for row in rows:
            data.append(QSwaggerInterface.MarketHub(row))
        del rows
        return data
