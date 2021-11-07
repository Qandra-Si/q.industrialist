# -*- encoding: utf-8 -*-


class QDictionaries:
    def __init__(self, db):
        """ constructor

        :param db: instance of QIndustrialistDatabase
        """
        self.db = db

    def __del__(self):
        """ destructor
        """

    def is_exist_name(self, id, category):
        """

        :param id: unique id
        :param category: category of id
        :return: true - exist, false - absent
        """

        __sdenid = self.db.select_one_row(
            "SELECT 1 FROM eve_sde_names WHERE sden_id=%s AND sden_category=%s;",
            id, category
        )
        if __sdenid is None:
            return False
        return True

    def clean_names(self, category):
        """ clean named items in the database by category

        :param category: category of id
        """
        self.db.execute(
            "DELETE FROM eve_sde_names WHERE sden_category=%s;",
            category)

    def insert_name(self, id, category, name):
        """ inserts named item into database

        :param id: unique id
        :param category: category of id
        :param name: item' name
        """
        self.db.execute(
            "INSERT INTO eve_sde_names(sden_id,sden_category,sden_name) "
            "VALUES (%s,%s,%s);",
            id, category, name)

    def actualize_names(self, items, category, name_tag):
        if isinstance(items, dict):
            # очиска таблицы по указанной категории
            self.clean_names(category)
            # заполнение таблицы по указанной категории
            items_keys = items.keys()
            for itm_key in items_keys:
                id = int(itm_key)
                if not (name_tag is None):
                    # предполагаем следущий справочник:
                    # { "0": { "key1": "val1", "name": { "en": "Shafrak IX - Moon 1" } },
                    #   "1": { "key2": 5, "name": { "en": "Vaini - Star" } },
                    #   "2": { "name": { "ru": "Шафрак" } },
                    #   "3": { "key2": 10 }
                    # }
                    __dict = items[str(itm_key)]
                    if (name_tag in __dict) and ("en" in __dict[name_tag]):
                        nm = __dict[name_tag]["en"]
                        self.insert_name(id, category, nm)
                else:
                    # предполагаем следущий справочник:
                    # { "0": "Shafrak IX - Moon 1",
                    #   "1": "Vaini - Star",
                    #   "2": "Шафрак"
                    # }
                    nm = items[str(itm_key)]
                    self.insert_name(id, category, nm)

    def clean_integers(self, category):
        """ clean numbered items in the database by category

        :param category: category of id
        """
        self.db.execute(
            "DELETE FROM eve_sde_integers WHERE sdei_category=%s;",
            category)

    def insert_integer(self, id, category, number):
        """ inserts numbered item into database

        :param id: unique id
        :param category: category of id
        :param number: item' number
        """
        self.db.execute(
            "INSERT INTO eve_sde_integers(sdei_id,sdei_category,sdei_number) "
            "VALUES (%s,%s,%s);",
            id, category, number)

    def clean_blueprints(self):
        self.db.execute("DELETE FROM eve_sde_blueprints;")

    def insert_blueprint_activity(self, blueprint_id: int, activity_id: int, time: int, materials, products):
        self.db.execute(
            "INSERT INTO eve_sde_blueprints("
            " sdeb_blueprint_type_id,"
            " sdeb_activity,"
            " sdeb_time) "
            "VALUES (%s,%s,%s);",
            int(blueprint_id),
            int(activity_id),
            int(time)
        )
        if products:
            for p in products:
                self.db.execute(
                    "INSERT INTO eve_sde_blueprint_products("
                    " sdebp_blueprint_type_id,"
                    " sdebp_activity,"
                    " sdebp_product_id,"
                    " sdebp_quantity,"
                    " sdebp_probability) "
                    "VALUES (%s,%s,%s,%s,%s);",
                    int(blueprint_id),
                    int(activity_id),
                    int(p["typeID"]),
                    int(p["quantity"]),
                    p.get("probability", None)
                )
        if materials:
            for m in materials:
                self.db.execute(
                    "INSERT INTO eve_sde_blueprint_materials("
                    " sdebm_blueprint_type_id,"
                    " sdebm_activity,"
                    " sdebm_material_id,"
                    " sdebm_quantity) "
                    "VALUES (%s,%s,%s,%s);",
                    int(blueprint_id),
                    int(activity_id),
                    int(m["typeID"]),
                    m["quantity"]
                )

    def actualize_blueprints(self, sde_bp_materials):
        for bp in sde_bp_materials:
            blueprint_id: int = bp
            activities = sde_bp_materials[bp].get("activities")
            if activities:
                copying = activities.get("copying")
                if copying:
                    activity_id = 5
                    materials = copying.get("materials")
                    products = copying.get("products")
                    time = copying["time"]
                    self.insert_blueprint_activity(int(blueprint_id), activity_id, time, materials, products)
                manufacturing = activities.get("manufacturing")
                if manufacturing:
                    activity_id = 1
                    materials = manufacturing.get("materials")
                    products = manufacturing.get("products")
                    time = manufacturing["time"]
                    self.insert_blueprint_activity(int(blueprint_id), activity_id, time, materials, products)
                invention = activities.get("invention")
                if invention:
                    activity_id = 8
                    materials = invention.get("materials")
                    products = invention.get("products")
                    time = invention["time"]
                    self.insert_blueprint_activity(int(blueprint_id), activity_id, time, materials, products)
                research_material = activities.get("research_material")
                if research_material:
                    activity_id = 4
                    materials = research_material.get("materials")
                    products = research_material.get("products")
                    time = research_material["time"]
                    self.insert_blueprint_activity(int(blueprint_id), activity_id, time, materials, products)
                research_time = activities.get("research_time")
                if research_time:
                    activity_id = 3
                    materials = research_time.get("materials")
                    products = research_time.get("products")
                    time = research_time["time"]
                    self.insert_blueprint_activity(int(blueprint_id), activity_id, time, materials, products)
                reaction = activities.get("reaction")
                if reaction:
                    activity_id = 9
                    materials = reaction.get("materials")
                    products = reaction.get("products")
                    time = reaction["time"]
                    self.insert_blueprint_activity(int(blueprint_id), activity_id, time, materials, products)

    def clean_type_ids(self):
        self.db.execute("DELETE FROM eve_sde_type_ids;")

    def insert_type_id(self, type_id: int, type_name: str, type_dict):
        self.db.execute(
            "INSERT INTO eve_sde_type_ids("
            " sdet_type_id,"
            " sdet_type_name,"
            " sdet_volume,"
            " sdet_capacity,"
            " sdet_base_price,"
            " sdet_published,"
            " sdet_market_group_id,"
            " sdet_meta_group_id,"
            " sdet_icon_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);",
            type_id,
            type_name,
            type_dict.get('volume', None),
            type_dict.get('capacity', None),
            type_dict.get('basePrice', None),
            type_dict.get('published', None),
            type_dict.get('marketGroupID', None),
            type_dict.get('metaGroupID', None),
            type_dict.get('iconID', None)
        )

    def actualize_type_ids(self, sde_type_ids):
        # заполнение таблицы typeIDs
        items_keys = sde_type_ids.keys()
        for itm_key in items_keys:
            type_id: int = int(itm_key)
            type_dict = sde_type_ids[str(itm_key)]
            # предполагаем следущий справочник:
            # { "0": { "key1": "val1", "name": { "en": "Shafrak IX - Moon 1" } },
            #   "1": { "key2": 5, "name": { "en": "Vaini - Star" } },
            #   "2": { "name": { "ru": "Шафрак" } },
            #   "3": { "key2": 10 }
            # }
            type_name = None
            if ("name" in type_dict) and ("en" in type_dict["name"]):
                type_name = type_dict["name"]["en"]
            self.insert_type_id(type_id, type_name, type_dict)

    def clean_market_groups(self):
        self.db.execute("DELETE FROM eve_sde_market_groups;")

    def insert_market_group(self, market_group_id: int, market_group_dict):
        self.db.execute(
            "INSERT INTO eve_sde_market_groups("
            " sdeg_group_id,"
            " sdeg_parent_id,"
            " sdeg_semantic_id,"
            " sdeg_group_name,"
            " sdeg_icon_id) "
            "VALUES (%s,%s,%s,%s,%s);",
            market_group_id,
            market_group_dict.get('parentGroupID', None),
            market_group_dict.get('semanticGroupID', None),
            market_group_dict['nameID']['en'],
            market_group_dict.get('iconID', None)
        )

    def actualize_market_groups(self, sde_market_groups):
        # "1031": {
        #   "iconID": 1277,
        #   "nameID": {
        #    "en": "Raw Materials"
        #   },
        #   "parentGroupID": 533,
        #   "semanticGroupID": 533  <--- добавляется индивидуально вызывающим алгоритмом
        #  },
        sde_market_groups_keys = sde_market_groups.keys()
        for group_id in sde_market_groups_keys:
            mg = sde_market_groups[str(group_id)]
            group_id: int = int(group_id)
            self.insert_market_group(group_id, mg)

