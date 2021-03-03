# -*- encoding: utf-8 -*-


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
    # universe/stations/
    # -------------------------------------------------------------------------

    def is_exist_station_id(self, id):
        """

        :param id: unique station id
        :return: true - exist, false - absent
        """

        sdenid = self.db.select_one_row(
            "SELECT 1 FROM esi_tranquility_stations WHERE ets_station_id=%s;",
            id
        )
        if sdenid is None:
            return False
        return True

    def get_absent_universe_station_ids(self, ids):
        """

        :param ids: list of unique station identities
        :return: list of station ids which are not in the database
        """

        aids = self.db.select_all_rows(
            "SELECT id FROM UNNEST(%s) AS a(id) "
            "WHERE id NOT IN (SELECT ets_station_id FROM esi_tranquility_stations);",
            ids
        )
        return aids

    def insert_universe_station(self, data, updated_at):
        """ inserts universe station data into database

        :param id: unique station id
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
            "INSERT INTO esi_tranquility_stations(ets_station_id,ets_type_id,ets_name,ets_owner_id,ets_race_id,"
            " ets_x,ets_y,ets_z,ets_system_id,ets_reprocessing_efficiency,ets_reprocessing_stations_take,"
            " ets_max_dockable_ship_volume,ets_office_rental_cost,ets_created_at,ets_updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %s) "
            "ON CONFLICT ON CONSTRAINT pk_ets DO NOTHING;",
            data['station_id'],
            data['type_id'],
            data['name'],
            data.get('owner', None),  # ID of the corporation that controls this station
            data.get('race_id', None),
            data['position']['x'],
            data['position']['y'],
            data['position']['z'],
            data['system_id'],
            data['reprocessing_efficiency'],
            data['reprocessing_stations_take'],
            data['max_dockable_ship_volume'],
            data['office_rental_cost'],
            updated_at
        )

    # -------------------------------------------------------------------------
    # universe/structures/
    # -------------------------------------------------------------------------

    def is_exist_structure_id(self, id):
        """

        :param id: unique structure id
        :return: true - exist, false - absent
        """

        sdenid = self.db.select_one_row(
            "SELECT 1 FROM esi_universe_structures WHERE eus_structure_id=%s;",
            id
        )
        if sdenid is None:
            return False
        return True

    def get_absent_universe_structure_ids(self, ids):
        """

        :param ids: list of unique structure identities
        :return: list of structure ids which are not in the database
        """

        aids = self.db.select_all_rows(
            "SELECT id FROM UNNEST(%s) AS a(id) "
            "WHERE id NOT IN (SELECT eus_structure_id FROM esi_universe_structures);",
            ids
        )
        return aids

    def insert_universe_structure(self, id, data, updated_at):
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
        self.db.execute(
            "INSERT INTO esi_universe_structures(eus_structure_id,eus_name,eus_owner_id,eus_system_id,"
            " eus_type_id,eus_x,eus_y,eus_z,eus_created_at,eus_updated_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            " TIMESTAMP WITHOUT TIME ZONE %s) "
            "ON CONFLICT ON CONSTRAINT pk_eus DO NOTHING;",
            id,
            data['name'],
            data['owner_id'],
            data['solar_system_id'],
            data.get('type_id', None),
            data['position']['x'],
            data['position']['y'],
            data['position']['z'],
            updated_at
        )

    # def mark_universe_structures_updated(self, ids):
    #    """
    #
    #    :param ids: list of unique structure identities to update
    #    """
    #
    #    self.db.execute(
    #        "UPDATE esi_universe_structures"
    #        " SET eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT' "
    #        "WHERE eus_structure_id IN (SELECT * FROM UNNEST(%s));",
    #        ids
    #    )

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/structures/
    # -------------------------------------------------------------------------

    def get_absent_corporation_structure_ids(self, ids):
        """

        :param ids: list of corporation structure identities
        :return: list of structure ids which are not in the database
        """

        aids = self.db.select_all_rows(
            "SELECT id FROM UNNEST(%s) AS a(id) "
            "WHERE id NOT IN (SELECT ecs_structure_id FROM esi_corporation_structures);",
            ids
        )
        return aids

    def insert_corporation_structure(self, data, updated_at=None):
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
        if updated_at is None:
            self.db.execute(
                "INSERT INTO esi_corporation_structures(ecs_structure_id,ecs_corporation_id,ecs_type_id,"
                " ecs_system_id,ecs_profile_id,ecs_created_at,ecs_updated_at) "
                "VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',CURRENT_TIMESTAMP AT TIME ZONE 'GMT') "
                "ON CONFLICT ON CONSTRAINT pk_ecs DO NOTHING;",
                data['structure_id'],
                data['corporation_id'],
                data['type_id'],
                data['system_id'],
                data['profile_id']
            )
        else:
            self.db.execute(
                "INSERT INTO esi_corporation_structures(ecs_structure_id,ecs_corporation_id,ecs_type_id,"
                " ecs_system_id,ecs_profile_id,ecs_created_at,ecs_updated_at) "
                "VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',TIMESTAMP WITHOUT TIME ZONE %s) "
                "ON CONFLICT ON CONSTRAINT pk_ecs DO NOTHING;",
                data['structure_id'],
                data['corporation_id'],
                data['type_id'],
                data['system_id'],
                data['profile_id'],
                updated_at
            )

    def mark_corporation_structures_updated(self, ids, updated_at=None):
        """

        :param ids: list of corporation structure identities to update
        """

        if updated_at is None:
            self.db.execute(
                "UPDATE esi_corporation_structures"
                " SET ecs_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT' "
                "WHERE ecs_structure_id IN (SELECT * FROM UNNEST(%s));",
                ids
            )
        else:
            self.db.execute(
                "UPDATE esi_corporation_structures"
                " SET ecs_updated_at=TIMESTAMP WITHOUT TIME ZONE %s "
                "WHERE ecs_structure_id IN (SELECT * FROM UNNEST(%s));",
                updated_at,
                ids
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
