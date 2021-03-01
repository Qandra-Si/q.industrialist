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

    # -------------------------------------------------------------------------
    # universe/structures/
    # -------------------------------------------------------------------------

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

    def insert_universe_structure(self, id, data, updated_at=None):
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
        if updated_at is None:
            self.db.execute(
                "INSERT INTO esi_universe_structures(eus_structure_id,eus_name,eus_owner_id,eus_solar_system_id,"
                " eus_type_id,eus_created_at,eus_updated_at) "
                "VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',CURRENT_TIMESTAMP AT TIME ZONE 'GMT') "
                "ON CONFLICT ON CONSTRAINT pk_eus DO NOTHING;",
                id,
                data['name'],
                data['owner_id'],
                data['solar_system_id'],
                data.get('type_id', None)
            )
        else:
            self.db.execute(
                "INSERT INTO esi_universe_structures(eus_structure_id,eus_name,eus_owner_id,eus_solar_system_id,"
                " eus_type_id,eus_created_at,eus_updated_at) "
                "VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'GMT',TIMESTAMP WITHOUT TIME ZONE %s) "
                "ON CONFLICT ON CONSTRAINT pk_eus DO NOTHING;",
                id,
                data['name'],
                data['owner_id'],
                data['solar_system_id'],
                data.get('type_id', None),
                updated_at
            )

    def mark_universe_structures_updated(self, ids):
        """

        :param ids: list of unique structure identities to update
        """

        self.db.execute(
            "UPDATE esi_universe_structures"
            " SET eus_updated_at=CURRENT_TIMESTAMP AT TIME ZONE 'GMT' "
            "WHERE eus_structure_id IN (SELECT * FROM UNNEST(%s));",
            ids
        )

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
