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
            # очиска таблица по указанной категории
            self.clean_names(category)
            # заполнение таблица по указанной категории
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
