﻿# -*- encoding: utf-8 -*-
from .db_swagger_cache import *
from .db_interface import QIndustrialistDatabase


class QSwaggerTranslator:
    def __init__(self, db: QIndustrialistDatabase):
        """ constructor

        :param db: instance of QIndustrialistDatabase
        """
        self.db = db

    def __del__(self):
        """ destructor
        """
        del self.db

    # -------------------------------------------------------------------------
    # /market/groups/
    # /market/groups/{market_group_id}/
    # -------------------------------------------------------------------------

    def get_market_groups(self) -> typing.Dict[int, QSwaggerMarketGroup]:
        rows = self.db.select_all_rows(
            "SELECT"
            " sdeg_group_id,"
            " sdeg_parent_id,"
            " sdeg_semantic_id,"
            " sdeg_group_name,"
            " sdeg_icon_id "
            "FROM eve_sde_market_groups;"
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            group_id: int = row[0]
            data[group_id] = QSwaggerMarketGroup(row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # /universe/types/
    # /universe/types/{type_id}/
    # -------------------------------------------------------------------------

    def get_published_type_ids(self) -> typing.Dict[int, QSwaggerTypeId]:
        rows = self.db.select_all_rows(
            "SELECT"
            " sdet_type_id,"
            " sdet_type_name,"
            " sdet_volume,"
            " sdet_capacity,"
            " sdet_base_price,"
            " sdet_market_group_id,"
            " sdet_meta_group_id,"
            " sdet_tech_level,"
            " sdet_icon_id,"
            " sdet_packaged_volume "
            "FROM eve_sde_type_ids "
            "WHERE sdet_published;"
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            type_id: int = row[0]
            data[type_id] = QSwaggerTypeId(row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # blueprints.yaml from https://developers.eveonline.com/resource/resources
    # -------------------------------------------------------------------------

    def get_blueprints(self, type_ids: typing.Dict[int, QSwaggerTypeId]) -> typing.Dict[int, QSwaggerBlueprint]:
        rows = self.db.select_all_rows(  # 15088 записей
            "SELECT"
            " blueprint_type_id,"
            " activity_id,"
            " time,"
            " product_type_id,"
            " quantity,"
            " probability "
            "FROM eve_sde_workable_blueprints;"
        )
        if rows is None:
            return {}
        data = {}
        # добавление чертежей в справочник, проверка входных данных на исключения... у CCP надо быть "готовым ко всему",
        # так как есть, например published manufacturing-чертежи у которых нет производимого продукта:
        # - 27015 Civilian Data Analyzer Blueprint (Civilian Data Analyzer не published)
        # - 2211  Sansha Juggernaut Torpedo Blueprint (Banshee Torpedo не published)
        # - 2179  Sansha Wrath Cruise Missile Blueprint (Haunter Cruise Missile не published)
        # и published чертёж, с которым можно выполнять invent-ы, и у которого нет продукта:
        # - 36949 Coalesced Element Blueprint (в sde есть invention-активность с time=0)
        #
        # и published чертёж, с которым можно выполнять научку и копирку:
        # - 36949 Coalesced Element Blueprint (в sde есть копирка с научкой c time=0)
        # - 41536 Zeugma Integrated Analyzer Blueprint (в sde есть копирка с научкой c time=0)
        for row in rows:
            type_id: int = row[0]
            # у некоторых чертежей есть несколько activity
            blueprint: QSwaggerBlueprint = data.get(type_id)
            if blueprint is None:
                cached_blueprint_type: QSwaggerTypeId = type_ids.get(type_id)
                if cached_blueprint_type is None:
                    raise Exception("Unable to add unknown blueprint #{}".format(type_id))
                blueprint: QSwaggerBlueprint = QSwaggerBlueprint(cached_blueprint_type)
                data[type_id] = blueprint
            # у invention activity может быть несколько products, остальные продукты связаны отношением 1:1
            activity_id: int = row[1]
            product_id = row[3]
            if activity_id == 1:
                if blueprint.manufacturing is not None:
                    raise Exception("Unable to add manufacturing activity twice: blueprint #{}".format(type_id))
                if product_id is None:
                    continue
                cached_product_type: QSwaggerTypeId = type_ids.get(product_id)
                if cached_product_type is None:
                    raise Exception("Unable to add manufacturing activity with unknown product #{}".format(product_id))
                blueprint.add_activity(cached_product_type, row)
            elif activity_id == 8:
                if blueprint.invention is None:
                    blueprint.add_activity_without_product(activity_id, row[2])
                if product_id is None:
                    continue
                cached_product_type: QSwaggerTypeId = type_ids.get(product_id)
                if cached_product_type is None:
                    raise Exception("Unable to add invention activity with unknown product #{}".format(product_id))
                blueprint.invention.add_product(cached_product_type, row)
            elif activity_id == 5:
                if blueprint.copying is not None:
                    raise Exception("Unable to add copying activity twice: blueprint #{}".format(type_id))
                cached_product_type: QSwaggerTypeId = type_ids.get(product_id)
                if cached_product_type is None:
                    raise Exception("Unable to add copying activity with unknown product #{}".format(product_id))
                blueprint.add_activity(cached_product_type, row)
            elif activity_id == 4:
                if blueprint.research_material is not None:
                    raise Exception("Unable to add research material activity twice: blueprint #{}".format(type_id))
                elif product_id is not None:
                    raise Exception("Unable to add research material, product must be unknown: blueprint #{}".format(type_id))
                blueprint.add_activity_without_product(activity_id, row[2])
            elif activity_id == 3:
                if blueprint.research_time is not None:
                    raise Exception("Unable to add research time activity twice: blueprint #{}".format(type_id))
                elif product_id is not None:
                    raise Exception("Unable to add research time activity, product must be unknown: blueprint #{}".format(type_id))
                blueprint.add_activity_without_product(activity_id, row[2])
            elif activity_id == 9:
                if blueprint.reaction is not None:
                    raise Exception("Unable to add reaction activity twice: blueprint #{}".format(type_id))
                if product_id is None:
                    continue
                cached_product_type: QSwaggerTypeId = type_ids.get(product_id)
                if cached_product_type is None:
                    raise Exception(
                        "Unable to add reaction activity with unknown product #{}".format(product_id))
                blueprint.add_activity(cached_product_type, row)
        del rows
        # ---
        rows = self.db.select_all_rows(
            "SELECT"
            " blueprint_type_id,"
            " activity_id,"
            " material_type_id,"
            " quantity "
            "FROM eve_sde_available_blueprint_materials "
            "ORDER BY 1,2,4 desc;"
        )
        if rows is None:
            return data
        blueprint: QSwaggerBlueprint = None  # noqa
        activity: typing.Union[QSwaggerBlueprintManufacturing, QSwaggerBlueprintInvention,
                               QSwaggerBlueprintCopying, QSwaggerBlueprintResearchMaterial,
                               QSwaggerBlueprintResearchTime, QSwaggerBlueprintReaction] = None  # noqa
        prev_blueprint_type_id: int = -1
        prev_activity_id: int = -1
        for row in rows:
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же чертежей
            blueprint_type_id: int = row[0]
            if blueprint_type_id != prev_blueprint_type_id:
                prev_blueprint_type_id = blueprint_type_id
                blueprint = data.get(blueprint_type_id)
                # возможная ситуация, что такого чертежа нет - тогда это ошибка
                if blueprint is None:
                    raise Exception("Unable to add material into blueprint #{} activity #{}".format(blueprint_type_id, activity_id))
                prev_activity_id = -1
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же activity
            activity_id: int = row[1]
            if activity_id != prev_activity_id:
                prev_activity_id = activity_id
                activity = blueprint.get_activity(activity_id)
            # возможная ситуация, что чертёж есть, а активность выше не добавлена, т.к. продукт non published:
            # - 2179  Sansha Wrath Cruise Missile Blueprint (Haunter Cruise Missile не published)
            if activity is None:
                continue
            # нужная activity найдена, добавляем материалы
            material_id: int = row[2]
            material_type: QSwaggerTypeId = type_ids.get(material_id)
            if material_type is None:
                raise Exception("Unable to add material #{} into blueprint #{} activity #{}".format(material_id, blueprint_type_id, activity_id))
            activity.materials.add_material(material_type, row[3])
        del rows
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/
    # -------------------------------------------------------------------------
    def get_corporation_id(self, corporation_name: str) -> typing.Optional[int]:
        row = self.db.select_one_row(
            "SELECT eco_corporation_id "
            "FROM esi_corporations "
            "WHERE eco_name=%(nm)s;",
            {'nm': corporation_name}
        )
        if row is None:
            return None
        return row[0]

    # -------------------------------------------------------------------------
    # characters/{character_id}/
    # -------------------------------------------------------------------------

    def get_character(self, character_name: str) -> typing.Optional[QSwaggerCharacter]:
        row = self.db.select_one_row(
            "SELECT ech_character_id "
            "FROM esi_characters "
            "WHERE ech_name=%(nm)s;",
            {'nm': character_name}
        )
        if row is None:
            return None
        cached_character: QSwaggerCharacter = QSwaggerCharacter(row[0], character_name)
        del row
        return cached_character

    def get_characters(
            self,
            character_ids: typing.Union[typing.List[int], typing.Set[int]]) -> typing.Dict[int, QSwaggerCharacter]:
        if isinstance(character_ids, list):
            ids: typing.List[int] = character_ids[:]
        elif isinstance(character_ids, set):
            ids: typing.List[int] = list(character_ids)
        else:
            raise Exception("Unable to determine type of character ids")
        rows = self.db.select_all_rows(
            "SELECT"
            " ech_character_id,"
            " ech_name "
            "FROM esi_characters "
            "WHERE ech_character_id IN (SELECT * FROM UNNEST(%(ids)s));",
            {'ids': ids}
        )
        del ids
        if rows is None:
            return {}
        data = {}
        for row in rows:
            character_id: int = row[0]
            data[character_id] = QSwaggerCharacter(character_id, row[1])
        del rows
        return data

    # -------------------------------------------------------------------------
    # universe/stations/{station_id}/
    # universe/structures/{structure_id}/
    # -------------------------------------------------------------------------

    def get_station(
            self,
            station_name: str,
            type_ids: typing.Dict[int, QSwaggerTypeId]) -> typing.Optional[QSwaggerStation]:
        row = self.db.select_one_row(
            "SELECT"
            " location_id,"
            " solar_system_id,"
            " station_type_id,"
            " solar_system_name "
            "FROM esi_known_stations "
            "WHERE name=%(nm)s;",
            {'nm': station_name}
        )
        if row is None:
            return None
        station_type_id: int = row[2]
        station_type: QSwaggerTypeId = type_ids.get(station_type_id)  # маловероятно, что тип неизвестен
        cached_station: QSwaggerStation = QSwaggerStation(row[0], station_name, row[1], row[3], station_type)
        del row
        return cached_station

    def get_stations(
            self,
            station_ids: typing.Union[typing.List[int], typing.Set[int]],
            type_ids: typing.Dict[int, QSwaggerTypeId]) -> typing.Dict[int, QSwaggerStation]:
        if isinstance(station_ids, list):
            ids: typing.List[int] = station_ids[:]
        elif isinstance(station_ids, set):
            ids: typing.List[int] = list(station_ids)
        else:
            raise Exception("Unable to determine type of station ids")
        rows = self.db.select_all_rows(
            "SELECT"
            " location_id,"
            " name,"
            " solar_system_id,"
            " station_type_id,"
            " solar_system_name "
            "FROM esi_known_stations "
            "WHERE location_id IN (SELECT * FROM UNNEST(%(ids)s));",
            {'ids': ids}
        )
        del ids
        if rows is None:
            return {}
        data = {}
        for row in rows:
            station_id: int = row[0]
            station_type_id: int = row[3]
            station_type: QSwaggerTypeId = type_ids.get(station_type_id)  # маловероятно, что тип неизвестен
            data[station_id] = QSwaggerStation(station_id, row[1], row[2], row[4], station_type)
        del rows
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/assets/
    # -------------------------------------------------------------------------

    def get_corporation_assets(
            self,
            corporation_id: int,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            load_unknown_type_assets: bool = False,
            load_asseted_blueprints: bool = False) -> typing.Dict[int, QSwaggerCorporationAssetsItem]:
        # ассеты могут содержать например 26420 предметов, тогда как чертежей в них будет 23289 шт
        filter_blueprints: str = ''
        if not load_asseted_blueprints:
            filter_blueprints = \
                "INNER JOIN eve_sde_type_ids ON (sdet_type_id=eca_type_id) " \
                "INNER JOIN eve_sde_group_ids ON (sdet_group_id=sdecg_group_id AND sdecg_category_id!=9) "
        rows = self.db.select_all_rows(
            "SELECT"
            " eca_item_id,"
            " eca_type_id,"
            " eca_quantity,"
            " eca_location_id,"
            " eca_location_type,"
            " eca_location_flag,"
            " eca_is_singleton,"
            " eca_name,"
            " eca_updated_at "
            "FROM esi_corporation_assets "
            + filter_blueprints +
            "WHERE eca_corporation_id=%(id)s;",
            {'id': corporation_id}
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            item_id: int = row[0]
            type_id: int = row[1]
            cached_item_type: QSwaggerTypeId = type_ids.get(type_id)
            if cached_item_type is None and not load_unknown_type_assets:
                continue
            data[item_id] = QSwaggerCorporationAssetsItem(cached_item_type, row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/blueprints/
    # -------------------------------------------------------------------------

    def get_corporation_blueprints(
            self,
            corporation_id: int,
            blueprints: typing.Dict[int, QSwaggerBlueprint],
            load_unknown_type_blueprints: bool = False) -> typing.Dict[int, QSwaggerCorporationBlueprint]:
        rows = self.db.select_all_rows(
            "SELECT"
            " ecb_item_id,"
            " ecb_type_id,"
            " ecb_location_id,"
            " ecb_location_flag,"
            " ecb_quantity,"
            " ecb_time_efficiency,"
            " ecb_material_efficiency,"
            " ecb_runs,"
            " ecb_updated_at "
            "FROM esi_corporation_blueprints "
            "WHERE ecb_corporation_id=%(id)s;",
            {'id': corporation_id}
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            item_id: int = row[0]
            type_id: int = row[1]
            cached_blueprint_type: QSwaggerBlueprint = blueprints.get(type_id)
            if cached_blueprint_type is None and not load_unknown_type_blueprints:
                continue
            data[item_id] = QSwaggerCorporationBlueprint(cached_blueprint_type, row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/industry/jobs/
    # -------------------------------------------------------------------------

    def get_corporation_industry_jobs(
            self,
            corporation_id: int,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            blueprints: typing.Dict[int, QSwaggerBlueprint],
            characters: typing.Dict[int, QSwaggerCharacter],
            stations: typing.Dict[int, QSwaggerStation],
            corporation_assets: typing.Dict[int, QSwaggerCorporationAssetsItem],
            corporation_blueprints: typing.Dict[int, QSwaggerCorporationBlueprint],
            load_unknown_type_blueprints: bool = True) -> typing.Dict[int, QSwaggerCorporationIndustryJob]:
        rows = self.db.select_all_rows(  # около 3000 одновременных активных корп работ, или больше...
            "SELECT"
            " ecj_job_id,"
            " ecj_installer_id,"
            " ecj_facility_id,"
            " ecj_activity_id,"
            " ecj_blueprint_id,"
            " ecj_blueprint_type_id,"
            " ecj_blueprint_location_id,"
            " ecj_output_location_id,"
            " ecj_runs,"
            " ecj_cost,"
            " ecj_licensed_runs,"
            " ecj_probability,"
            " ecj_product_type_id,"
            " ecj_end_date "
            "FROM esi_corporation_industry_jobs "
            "WHERE ecj_completed_date IS NULL AND ecj_corporation_id=%(id)s;",
            {'id': corporation_id}
        )
        if rows is None:
            return {}
        # получаем список пилотов, которые запустили работы, обычно 100 уникальных пилотов на 3000 работах
        unique_installer_ids: typing.List[int] = list(set([r[1] for r in rows]))
        if unique_installer_ids:
            unknown_installer_ids: typing.List[int] = [c_id for c_id in unique_installer_ids if not characters.get(c_id)]
            unknown_job_installers: typing.Dict[int, QSwaggerCharacter] = self.get_characters(unknown_installer_ids)
            for (character_id, cached_character) in unknown_job_installers.items():
                characters[character_id] = cached_character
            del unknown_job_installers
            del unknown_installer_ids
        del unique_installer_ids
        # получаем список фабрик, на которых запущены работы, обычно единицы уникальных станций/структур
        unique_facility_ids: typing.List[int] = list(set([r[2] for r in rows]))
        if unique_facility_ids:
            unknown_facility_ids: typing.List[int] = [c_id for c_id in unique_facility_ids if not stations.get(c_id)]
            unknown_job_facilities: typing.Dict[int, QSwaggerStation] = self.get_stations(unknown_facility_ids, type_ids)
            for (facility_id, cached_facility) in unknown_job_facilities.items():
                stations[facility_id] = cached_facility
            del unknown_job_facilities
            del unknown_facility_ids
        del unique_facility_ids
        # обработка данных по корпоративным работам и связывание их с другими кешированными объектами
        data = {}
        prev_blueprint_type_id: int = -1
        cached_blueprint_type: typing.Optional[QSwaggerBlueprint] = None
        prev_installer_id: int = -1
        cached_installer: typing.Optional[QSwaggerCharacter] = None
        prev_product_type_id: int = -1
        cached_product_type: typing.Optional[QSwaggerTypeId] = None
        prev_blueprint_location_id: int = -1
        blueprint_location: typing.Optional[QSwaggerCorporationAssetsItem] = None
        prev_output_location_id: int = -1
        output_location: typing.Optional[QSwaggerCorporationAssetsItem] = None
        prev_facility_id: int = -1
        facility: typing.Optional[QSwaggerStation] = None
        for row in rows:
            job_id: int = row[0]
            installer_id: int = row[1]
            facility_id: int = row[2]
            activity_id: int = row[3]
            blueprint_id: int = row[4]
            blueprint_type_id: int = row[5]
            blueprint_location_id: int = row[6]
            output_location_id: int = row[7]
            product_type_id: int = row[12]
            # определяем тип чертежа, например Photon Microprocessor Blueprint
            if prev_blueprint_type_id != blueprint_type_id:
                prev_blueprint_type_id = blueprint_type_id
                cached_blueprint_type = blueprints.get(blueprint_type_id)
                # если задана настройка "не реботать с неизвестными данными", то пропускаем чертёж
                if cached_blueprint_type is None and not load_unknown_type_blueprints:
                    continue
            # определяем продукт производства, например Photon Microprocessor
            if prev_product_type_id != product_type_id:
                product_type_id = product_type_id
                cached_product_type = None
                # стараемся найти тип продукта в наборе данных, ассоциированных с типом чертежа
                if cached_blueprint_type:
                    if activity_id == 1:
                        cached_product_type = cached_blueprint_type.manufacturing.product_type
                    elif activity_id == 9:
                        cached_product_type = cached_blueprint_type.reaction.product_type
                    elif activity_id == 5 or activity_id == 4 or activity_id == 3:  # продукт копирки и научки - чертёж
                        cached_product_type = cached_blueprint_type.blueprint_type
                    elif activity_id == 8:
                        cached_product_type = next((p.product_type for p in cached_blueprint_type.invention.products if p.product_id == product_type_id), None)
                    # если задана настройка "не реботать с неизвестными данными", то пропускаем чертёж
                    if cached_product_type is None and not load_unknown_type_blueprints:
                        continue
                # если продукт найти с помощью типа чертежа не удалось, то ищем в глобальном справочнике type_ids
                if not cached_product_type:
                    cached_product_type = type_ids.get(product_type_id)
                    # если задана настройка "не реботать с неизвестными данными", то пропускаем чертёж
                    if cached_product_type is None and not load_unknown_type_blueprints:
                        continue
            # определяем пилота (обычно известен) т.к. добавляется в БД синхронно работе (если не удалён вручную)
            if prev_installer_id != installer_id:
                prev_installer_id = installer_id
                cached_installer = characters[installer_id]
            # определяем фабрику (обычно известна) т.к. добавляется в БД синхронно работе (и не удаляется), но к
            # фабрике может пропасть доступ и q_universe_preload.py не сможет получить информацию о ней
            if prev_facility_id != facility_id:
                prev_facility_id = facility_id
                facility = stations.get(facility_id)
            # определяем место расположения чертежа (коробка из которой была запущена работа)
            if prev_blueprint_location_id != blueprint_location_id:
                prev_blueprint_location_id = blueprint_location_id
                blueprint_location = corporation_assets.get(blueprint_location_id)
            # определяем место, куда будет отправлен продукт (коробка куда направлен выход запущенной работы)
            if prev_output_location_id != output_location_id:
                prev_output_location_id = output_location_id
                output_location = corporation_assets.get(output_location_id)
            # ищет среди корпоративных чертежей bp с идентичным идентификатором
            # то, что чертёж может быть не найден, - это может быть вполне себе стандартной ситуацией, т.к.
            # сведения от CCP несинхронны
            cached_blueprint: typing.Optional[QSwaggerCorporationBlueprint] = corporation_blueprints.get(blueprint_id)
            # добавляем новую корпоративную работку
            data[job_id] = QSwaggerCorporationIndustryJob(
                cached_blueprint,  # неизвестен, если в корпчертежах нет этого bp, либо сведения о работе несинхронны
                cached_blueprint_type,  # неизвестен, если в БД нет данных об этом типе чертежа (пока не обновится sde)
                cached_product_type,  # неизвестен, если в БД нет данных об этом типе продукта (пока не обновится esi)
                cached_installer,  # обычно известен, т.к. добавляется в БД синхронно работе (если не удалён вручную)
                blueprint_location,  # коробки редко перемещаются, поэтому обычно известны
                output_location,  # коробки редко перемещаются, поэтому обычно известны
                facility,  # фабрики обычно известны, если не пропал доступ (и БД неотсинхронизирована)
                row)
        del rows
        return data
