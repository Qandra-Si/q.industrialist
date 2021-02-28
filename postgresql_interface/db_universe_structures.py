# -*- encoding: utf-8 -*-


class QUniverseStructures:
    def __init__(self, db):
        """ constructor

        :param db: instance of QIndustrialistDatabase
        """
        self.db = db

    def __del__(self):
        """ destructor
        """

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

    def get_absent_structure_ids(self, ids):
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

    def insert_universe_structure(self, id, data):
        """ inserts universe structure data into database

        :param id: unique structure id
        :param data: universe structure data
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
            "INSERT INTO esi_universe_structures(eus_structure_id,eus_name,eus_owner_id,eus_solar_system_id,"
            " eus_type_id,eus_created_at) "
            "VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT') "
            "ON CONFLICT ON CONSTRAINT pk_eus DO NOTHING;",
            # "INSERT INTO esi_universe_structures(eus_structure_id,eus_name,eus_owner_id,eus_solar_system_id,"
            # " eus_type_id,eus_x,eus_y,eus_z,eus_created_at,eus_updated_at) "
            # "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',"
            # " CURRENT_TIMESTAMP AT TIME ZONE 'GMT') "
            # "ON CONFLICT ON CONSTRAINT pk_us DO NOTHING;",
            id,
            data['name'],
            data['owner_id'],
            data['solar_system_id'],
            data.get('type_id', None)
            # ,data['position']['x'],
            # data['position']['y'],
            # data['position']['z']
        )

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

    def insert_corporation_structure(self, data):
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
            "INSERT INTO esi_corporation_structures(ecs_structure_id,ecs_corporation_id,ecs_type_id,"
            " ecs_system_id,ecs_profile_id,ecs_created_at) "
            "VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT') "
            "ON CONFLICT ON CONSTRAINT pk_ecs DO NOTHING;",
            data['structure_id'],
            data['corporation_id'],
            data['type_id'],
            data['system_id'],
            data['profile_id']
        )
