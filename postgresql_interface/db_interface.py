# -*- encoding: utf-8 -*-
import sys
import json
import psycopg2


class QIndustrialistDatabase:
    def __init__(self, module_name, settings=None, debug=False):
        """ constructor

        :param module_name: unique name of the Q.Industrialist module
        :param connection settings: dbname, user, password, host, port
        :param debug: flag which says that we are in debug mode
        """
        self.__module_name = str(module_name)
        self.__settings = settings
        self.__debug = debug

        self.__conn = None
        self.__module_id = None
        self.__module_settings = []

    def __del__(self):
        """ destructor
        """
        self.disconnect()

    @property
    def module_name(self):
        """ unique name of Q.Industrialist module
        """
        return self.__module_name

    @property
    def module_id(self):
        """ unique id of Q.Industrialist module
        """
        return self.__module_id

    @property
    def settings(self):
        """ connection settings: dbname, user, password, host, port
        """
        return self.__settings

    @property
    def debug(self):
        """ flag which says that we are in debug mode
        """
        return self.__debug

    def enable_debug(self):
        self.__debug = True

    def disable_debug(self):
        self.__debug = False

    def connect(self, settings=None):
        """ connects to the database with specified settings and discover module id parameter
        """
        if not (settings is None):
            self.__settings = settings

        try:
            self.disconnect()
            self.__conn = psycopg2.connect(
                dbname=self.settings["dbname"],
                user=self.settings["user"],
                password=self.settings["password"],
                host=self.settings["host"],
                port=self.settings["port"]
            )
            self.execute("SET search_path TO qi")
            __mid = self.select_one_row(
                "SELECT ml_id FROM modules_list "
                "WHERE ml_name=%s;",
                (self.module_name,)
            )
            if __mid is None:
                __mid = self.select_one_row(
                    "INSERT INTO modules_list(ml_name) "
                    "VALUES(%s) RETURNING ml_id;",
                    (self.module_name,)
                )
            self.__module_id = __mid[0]
        except psycopg2.DatabaseError as e:
            print(f"Error {e}")
            print(sys.exc_info())
            raise e

    def disconnect(self):
        if self.__conn is None:
            return
        with self.__conn as conn:
            if not conn.cursor().closed:
                conn.cursor().close()
            if self.debug and (conn.closed != 0):
                print('Error on closing database connection: code={}'.format(conn.closed))
            conn.cancel()
        self.__conn = None

    def commit(self):
        self.__conn.commit()

    def rollback(self):
        self.__conn.rollback()

    def select_one_row(self, query, *args):
        with self.__conn.cursor() as cur:
            cur.execute(query, args)
            if self.debug:
                print(cur.query)
            records = cur.fetchone()
            cur.close()
            return records

    def select_many_rows(self, fetch_size, query, *args):
        with self.__conn.cursor() as cur:
            cur.execute(query, args)
            if self.debug:
                print(cur.query)
            records = cur.fetchmany(fetch_size)
            cur.close()
            return records

    def select_all_rows(self, query, *args):
        with self.__conn.cursor() as cur:
            cur.execute(query, args)
            if self.debug:
                print(cur.query)
            records = cur.fetchall()
            cur.close()
            return records

    def execute(self, query, *args):
        with self.__conn.cursor() as cur:
            cur.execute(query, args)
            if self.debug:
                print(cur.query)
            cur.close()
            # if self.debug:
            #     print(f"{cur.rowcount} rows affected.")

    def load_module_settings(self, default_settings):
        settings = self.select_all_rows(
            "SELECT ms_key,ms_val "
            "FROM modules_settings WHERE ms_module=%s;",
            (self.module_id,)
        )
        # конвертируем набор данных settings из list в dict по парам key:value
        if settings is None:
            settings = {}
        else:
            __s = {}
            for kv in settings:
                __s.update({kv[0]: kv[1]})
            settings = __s
        # недостающие (новые) значения из default_settings добавляем в БД и в settings
        keys = settings.keys()
        some_missing = False
        for kv in default_settings.items():
            __key = kv[0]
            __default_val = kv[1]
            if not (__key in keys):
                self.execute(
                    "INSERT INTO modules_settings(ms_module,ms_key,ms_val) "
                    "VALUES(%s,%s,%s);",
                    self.module_id, __key, str(__default_val)
                )
                settings.update({__key: __default_val})
                some_missing = True
            else:
                # конвертируем считанные строки из БД в тип, соответствующий default value
                # если в default_settings настройки нет, а из БД она считалась, то
                # храниться в settings она будет как строка
                if isinstance(__default_val, str):
                    pass
                elif isinstance(__default_val, int):
                    settings[__key] = int(settings[__key])
                elif isinstance(__default_val, (list, dict)):
                    settings[__key] = (json.loads(settings[__key]))
        # если набор данных в БД менялся, то подтверждаем транзацию
        if some_missing:
            self.commit()
        return settings
