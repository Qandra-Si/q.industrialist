# -*- encoding: utf-8 -*-
import pytz


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

    def get_exist_ids(self, table, field, updated):
        """
        :param table: table name
        :param field: field name of identity
        :param updated: field name of updated_at
        :return: list of unique identities stored in the database
        """
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
            return None, None
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

    def get_exist_corporation_structures(self,):
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

    def insert_corporation_assets(self, data, corporation_id, updated_at):
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
            "INSERT INTO esi_corporation_assets(eca_item_id,eca_corporation_id,eca_type_id,eca_quantity,"
            " eca_location_id,eca_location_type,eca_location_flag,eca_is_singleton,eca_name,eca_created_at,"
            " eca_updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %s) "
            "ON CONFLICT ON CONSTRAINT pk_eca DO NOTHING;",
            data['item_id'],
            corporation_id,
            data['type_id'],
            data['quantity'],
            data['location_id'],
            data['location_type'],
            data['location_flag'],
            data['is_singleton'],
            None,
            updated_at
        )
