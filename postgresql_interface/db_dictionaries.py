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

    def is_exist(self, id, category):
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

    def clean(self, category):
        """ clean named items in the database by category

        :param category: category of id
        """
        self.db.execute(
            "DELETE FROM eve_sde_names WHERE sden_category=%s;",
            category)

    def insert(self, id, category, name):
        """ inserts named item into database

        :param id: unique id
        :param category: category of id
        :param name: item' name
        """
        self.db.execute(
            "INSERT INTO eve_sde_names(sden_id,sden_category,sden_name) "
            "VALUES (%s,%s,%s);",
            id, category, name)

    def actualize(self, items, category, name_tag):
        if isinstance(items, dict):
            # очиска таблица по указанной категории
            self.clean(category)
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
                        self.insert(id, category, nm)
                else:
                    # предполагаем следущий справочник:
                    # { "0": "Shafrak IX - Moon 1",
                    #   "1": "Vaini - Star",
                    #   "2": "Шафрак"
                    # }
                    nm = items[str(itm_key)]
                    self.insert(id, category, nm)
