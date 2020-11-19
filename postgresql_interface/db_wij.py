# -*- encoding: utf-8 -*-


class QWorkflowIndustryJobs:
    def __init__(self, db):
        """ constructor

        :param db: instance of QIndustrialistDatabase
        """
        self.db = db

    def __del__(self):
        """ destructor
        """

    def is_exist(self, job_id):
        """

        :param job_id: unique job id
        :return: true - exist, false - absent
        """

        __jid = self.db.select_one_row(
            "SELECT 1 FROM workflow_industry_jobs WHERE wij_job_id=%s;",
            (job_id,)
        )
        if __jid is None:
            return False
        return True

    def insert(self, job, quantity):
        """ inserts job data into database

        :param job: https://esi.evetech.net/ui/#/Industry/get_corporations_corporation_id_industry_jobs
        :param quantity: manufacturing products quantity
        :return:
        """

        # {
        #     "activity_id": 3,
        #     "blueprint_id": 1033874782806,
        #     "blueprint_location_id": 1033970633363,
        #     "blueprint_type_id": 25981,
        #     "cost": 507398.0,
        #     "duration": 1249459,
        #     "end_date": "2020-11-07T19:45:18Z",
        #     "facility_id": 1033917719607,
        #     "installer_id": 2116156168,
        #     "job_id": 440579607,
        #     "licensed_runs": 40,
        #     "location_id": 1033917719607,
        #     "output_location_id": 1033970633363,
        #     "probability": 1.0,
        #     "product_type_id": 25981,
        #     "runs": 10,
        #     "start_date": "2020-10-24T08:40:59Z",
        #     "status": "active"
        # }

        self.db.execute(
            "INSERT INTO workflow_industry_jobs(wij_job_id,wij_activity_id,wij_cost,wij_duration,"
            " wij_runs,wij_product_tid,wij_bp_id,wij_bp_tid,wij_bp_lid,wij_lid,wij_out_lid,"
            " wij_facility_id,wij_installer_id,wij_start_date,wij_end_date,wij_quantity) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TIMESTAMP WITHOUT TIME ZONE %s,"
            " TIMESTAMP WITHOUT TIME ZONE %s,%s) "
            "ON CONFLICT ON CONSTRAINT pk_wij DO NOTHING;",  # тот же самый job_id ?
            job["job_id"],
            job["activity_id"],
            job["cost"] if "cost" in job else None,
            job["duration"],
            job["runs"],
            job["product_type_id"] if "product_type_id" in job else None,
            job["blueprint_id"],
            job["blueprint_type_id"],
            job["blueprint_location_id"],
            job["location_id"],
            job["output_location_id"],
            job["facility_id"],
            job["installer_id"],
            job["start_date"],
            job["end_date"],
            quantity
        )

    def actualize(self, corp_industry_jobs_data, sde_bp_materials):
        # отключаем отладку при работе с БД (слишком много спама)
        db_in_debug_mode = self.db.debug
        if db_in_debug_mode:
            self.db.disable_debug()
        # начинаем ввод данных в БД
        res = 0
        for job in corp_industry_jobs_data:
            if not self.is_exist(job["job_id"]):
                # расчёт кол-ва продуктов, выполняемых текущей работой
                products_quantity = job["runs"]
                blueprint_type_id = job["blueprint_type_id"]
                __bp_dict = sde_bp_materials[str(blueprint_type_id)]["activities"] if str(blueprint_type_id) in sde_bp_materials else None
                if __bp_dict is None:
                    print('ERROR: unknown job blueprint_type_id={}'.format(blueprint_type_id))
                elif job["activity_id"] == 1:
                    if "manufacturing" in __bp_dict:
                        if "products" in __bp_dict["manufacturing"]:
                            products_quantity *= __bp_dict["manufacturing"]["products"][0]["quantity"]
                elif job["activity_id"] == 8:
                    if "invention" in __bp_dict:
                        if "products" in __bp_dict["invention"]:
                            products_quantity *= __bp_dict["invention"]["products"][0]["quantity"]
                elif job["activity_id"] in (9, 11):
                    if "reaction" in __bp_dict:
                        if "products" in __bp_dict["reaction"]:
                            products_quantity *= __bp_dict["reaction"]["products"][0]["quantity"]
                # ввод данных в БД
                self.insert(job, products_quantity)
                res += 1
        # сохраняем данные и подключаем отладку при работе с БД (если отключалась)
        self.db.commit()
        if db_in_debug_mode:
            self.db.enable_debug()
        return res
