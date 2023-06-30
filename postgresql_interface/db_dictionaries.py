# -*- encoding: utf-8 -*-
import typing


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
            del items_keys

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

    def insert_blueprint_activity(
            self,
            blueprint_id: int,
            activity_id: int,
            time: int,
            materials,
            products,
            max_production_limit: typing.Optional[int] = None):
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
                    " sdebp_probability,"
                    " sdebp_max_production_limit) "
                    "VALUES (%s,%s,%s,%s,%s,%s);",
                    int(blueprint_id),
                    int(activity_id),
                    int(p["typeID"]),
                    int(p["quantity"]),
                    p.get("probability", None),
                    max_production_limit if max_production_limit else None
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
                    max_production_limit: typing.Optional[int] = sde_bp_materials[bp].get("maxProductionLimit", None)
                    # в копирке продуктом всегда является сам чертёж с тем же идентификатором продукта, что и оригинал
                    # за исключением всего одного чертежа Taipan Blueprint 33082, который копируется в 33081 Taipan
                    self.insert_blueprint_activity(
                        int(blueprint_id),
                        activity_id,
                        time,
                        materials,
                        products if products else [{"typeID": int(blueprint_id), "quantity": 1}],
                        max_production_limit=max_production_limit
                    )
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

    def clean_categories(self):
        self.db.execute("DELETE FROM eve_sde_category_ids;")

    def insert_category_id(self, category_id: int, category_dict):
        self.db.execute(
            "INSERT INTO eve_sde_category_ids("
            " sdec_category_id,"
            " sdec_category_name,"
            " sdec_published,"
            " sdec_icon_id) "
            "VALUES ("
            " %(c)s,"
            " %(n)s,"
            " %(p)s,"
            " %(i)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdec DO UPDATE SET"
            " sdec_category_name=%(n)s,"
            " sdec_published=%(p)s,"
            " sdec_icon_id=%(i)s;",
            {'c': category_id,
             'n': category_dict['name']['en'],
             'p': category_dict['published'],
             'i': category_dict.get('iconID', None),
             }
        )

    def actualize_categories(self, sde_categories):
        # "9": {
        #  "iconID": 21,
        #  "name": {
        #   "en": "Blueprint"
        #  },
        #  "published": true
        # }
        sde_categories_keys = sde_categories.keys()
        for category_id in sde_categories_keys:
            c = sde_categories[str(category_id)]
            self.insert_category_id(int(category_id), c)
        del sde_categories_keys

    def clean_groups(self):
        self.db.execute("DELETE FROM eve_sde_group_ids;")

    def insert_group_id(self, group_id: int, group_dict):
        self.db.execute(
            "INSERT INTO eve_sde_group_ids("
            " sdecg_group_id,"
            " sdecg_category_id,"
            " sdecg_group_name,"
            " sdecg_published,"
            " sdecg_icon_id,"
            " sdecg_use_base_price) "
            "VALUES ("
            " %(g)s,"
            " %(c)s,"
            " %(n)s,"
            " %(p)s,"
            " %(i)s,"
            " %(u)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdecg DO UPDATE SET"
            " sdecg_category_id=%(c)s,"
            " sdecg_group_name=%(n)s,"
            " sdecg_published=%(p)s,"
            " sdecg_icon_id=%(i)s,"
            " sdecg_use_base_price=%(u)s;",
            {'g': group_id,
             'c': group_dict['categoryID'],
             'n': group_dict.get('name', {'en': ''}).get('en', ''),  # у группы 1969 нет названия, но она и не published
             'p': group_dict['published'],
             'i': group_dict.get('iconID', None),
             'u': group_dict.get('useBasePrice', None),
             }
        )

    def actualize_groups(self, sde_groups):
        # "18": {
        #  "categoryID": 4,
        #  "iconID": 22,
        #  "name": {
        #   "en": "Mineral"
        #  },
        #  "published": true,
        #  "useBasePrice": true
        # },
        # "1764": {
        #  "categoryID": 11,
        #  "name": {
        #   "en": "\u2666 Mining Frigate" -> ♦ Mining Frigate
        #  },
        #  "published": false,
        #  "useBasePrice": false
        # },
        # "1969": {
        #  "categoryID": 7,
        #  "name": {},
        #  "published": false,
        #  "useBasePrice": false
        # }
        sde_groups_keys = sde_groups.keys()
        for group_id in sde_groups_keys:
            g = sde_groups[str(group_id)]
            self.insert_group_id(int(group_id), g)
        del sde_groups_keys

    def insert_type_id(self, type_id: int, type_name: str, type_dict):
        self.db.execute(
            "INSERT INTO eve_sde_type_ids("
            " sdet_type_id,"
            " sdet_type_name,"
            " sdet_group_id,"
            " sdet_volume,"
            " sdet_capacity,"
            " sdet_base_price,"
            " sdet_published,"
            " sdet_market_group_id,"
            " sdet_meta_group_id,"  # этот параметр получаем из sde (esi его не выдаёт)
            " sdet_tech_level,"  # этот параметр получаем только по esi (из sde его надо читать из атрибутов)
            " sdet_icon_id) "
            "VALUES ("
            " %(t)s,"
            " %(n)s,"
            " %(g)s,"
            " %(v)s,"
            " %(c)s,"
            " %(bp)s,"
            " %(p)s,"
            " %(mg)s,"
            " %(meg)s,"
            " null,"
            " %(i)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdet DO UPDATE SET"
            " sdet_type_name=%(n)s,"
            " sdet_group_id=%(g)s,"
            " sdet_volume=%(v)s,"
            " sdet_capacity=%(c)s,"
            " sdet_base_price=%(bp)s,"
            " sdet_published=%(p)s,"
            " sdet_market_group_id=%(mg)s,"
            " sdet_meta_group_id=%(meg)s,"  # этот параметр получаем из sde (esi его не выдаёт)
            " sdet_icon_id=%(i)s;",
            {'t': type_id,
             'n': type_name,
             'g': type_dict['groupID'],
             'v': type_dict.get('volume', None),
             'c': type_dict.get('capacity', None),
             'bp': type_dict.get('basePrice', None),
             'p': type_dict.get('published', None),
             'mg': type_dict.get('marketGroupID', None),
             'meg': type_dict.get('metaGroupID', None),
             'i': type_dict.get('iconID', None),
             }
        )

    def hide_obsolete_type_ids(self, sde_type_ids):
        # получение с сервера всех типов предметов (для поиска тех, что исчезли из sde)
        stored_type_ids = self.db.select_all_rows(
            "SELECT sdet_type_id FROM eve_sde_type_ids WHERE sdet_published and sdet_type_id<>-1;",
        )
        # поиск тех типов предметов, которые есть в БД, но отсутствуют в sde справочнике
        stored_type_ids = set([int(r[0]) for r in stored_type_ids])
        sde_type_ids = set([int(tid) for tid in sde_type_ids])
        removed_type_ids = stored_type_ids - sde_type_ids
        del stored_type_ids
        del sde_type_ids
        # помечаем в БД удалённые предметы как not published, т.к. в БД есть справочники
        # (например исторические), в которых сохраняется type_id
        if removed_type_ids:
            print("{} Universe' items obsolete in database (market as not published):".format(len(removed_type_ids)))
            for type_id in removed_type_ids:
                print(" * ", type_id)
                self.db.execute(
                    "UPDATE eve_sde_type_ids SET sdet_published=false WHERE sdet_type_id=%s;",
                    type_id)
        del removed_type_ids

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
            # тип предмета либо добавится, либо обновится в содержимом полей из sde-справочника
            self.insert_type_id(type_id, type_name, type_dict)
        # помечаем в БД удалённые предметы как not published, т.к. в БД есть справочники
        # (например исторические), в которых сохраняется type_id
        self.hide_obsolete_type_ids(items_keys)
        del items_keys
        # добавляем в БД маркер-индикатор того, что надо перечитать из esi данные по
        # packaged_volume и обновить их в БД (в sde этих данных нет)
        self.insert_type_id(-1, 'Waiting automatic data update from ESI', {'published': False, 'groupID': 0})

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
            "VALUES (%(g)s,%(p)s,%(s)s,%(n)s,%(i)s) "
            "ON CONFLICT ON CONSTRAINT pk_sdeg DO UPDATE SET"
            " sdeg_parent_id=%(p)s,"
            " sdeg_semantic_id=%(s)s,"
            " sdeg_group_name=%(n)s,"
            " sdeg_icon_id=%(i)s;",
            {'g': market_group_id,
             'p': market_group_dict.get('parentGroupID', None),
             's': market_group_dict.get('semanticGroupID', None),
             'n': market_group_dict['nameID']['en'],
             'i': market_group_dict.get('iconID', None),
             }
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
        del sde_market_groups_keys

