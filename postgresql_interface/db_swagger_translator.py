# -*- encoding: utf-8 -*-
import typing
import math

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
    # /{all}/updated_at
    # -------------------------------------------------------------------------
    def get_lifetime(self, corporation_ids: typing.List[int]) -> typing.Dict[typing.Tuple[str, int], datetime.datetime]:
        # EXTRACT(EPOCH FROM ())::integer
        rows = self.db.select_all_rows("""
select 'assets' as what, eca_corporation_id, max(eca_updated_at) updated_at
from esi_corporation_assets
where eca_corporation_id in (select * from unnest(%(ids)s))
group by 2
union
select 'blueprints', ecb_corporation_id, max(ecb_updated_at)
from esi_corporation_blueprints
where ecb_corporation_id in (select * from unnest(%(ids)s))
group by 2
union
select 'jobs', ecj_corporation_id, max(ecj_updated_at)
from esi_corporation_industry_jobs
where ecj_corporation_id in (select * from unnest(%(ids)s))
group by 2
union
select 'orders', ecor_corporation_id, max(ecor_updated_at)
from esi_corporation_orders
where ecor_corporation_id in (select * from unnest(%(ids)s))
group by 2
union
select 'current', null, current_timestamp at time zone 'GMT'
;""",
            {'ids': corporation_ids}
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            what: str = row[0]
            corporation_id: int = row[1]
            updated_at: datetime.datetime = row[2]
            data[(what, corporation_id)] = updated_at
        del rows
        return data

    # -------------------------------------------------------------------------
    # /markets/groups/
    # /markets/groups/{market_group_id}/
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
    # /universe/categories/
    # /universe/categories/{category_id}/
    # -------------------------------------------------------------------------

    def get_universe_categories(self) -> typing.Dict[int, QSwaggerCategory]:
        # группа м.б. неизвестна (неопубликована), например у 'Liminal Zirnitra Wreck' группа 'Wreck' не published
        rows = self.db.select_all_rows(
            "SELECT"
            " sdec_category_id,"
            " sdec_category_name,"
            " sdec_published "
            "FROM eve_sde_category_ids;"
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            category_id: int = row[0]
            data[category_id] = QSwaggerCategory(row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # /universe/groups/
    # /universe/groups/{group_id}/
    # -------------------------------------------------------------------------

    def get_universe_groups(
            self,
            categories: typing.Dict[int, QSwaggerCategory]) -> typing.Dict[int, QSwaggerGroup]:
        # группа м.б. неизвестна (неопубликована), например у 'Liminal Zirnitra Wreck' группа 'Wreck' не published
        rows = self.db.select_all_rows(
            "SELECT"
            " sdecg_group_id,"
            " sdecg_category_id,"
            " sdecg_group_name,"
            " sdecg_published "
            "FROM eve_sde_group_ids;"
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            group_id: int = row[0]
            category_id: int = row[1]
            cached_category: typing.Optional[QSwaggerCategory] = categories.get(category_id)
            data[group_id] = QSwaggerGroup(cached_category, row)
        del rows
        return data

    # -------------------------------------------------------------------------
    # /universe/types/
    # /universe/types/{type_id}/
    # -------------------------------------------------------------------------

    def get_type_ids(
            self,
            market_groups: typing.Dict[int, QSwaggerMarketGroup],
            groups: typing.Dict[int, QSwaggerGroup],
            only_published: bool = True) -> typing.Dict[int, QSwaggerTypeId]:
        rows = self.db.select_all_rows(
            "SELECT"
            " sdet_type_id,"
            " sdet_type_name,"
            " sdet_volume,"
            " sdet_capacity,"
            " sdet_base_price,"
            " sdet_published,"
            " sdet_market_group_id,"
            " sdet_meta_group_id,"
            " sdet_tech_level,"
            " sdet_icon_id,"
            " sdet_packaged_volume,"
            " sdet_group_id,"
            " sdet_tech_level "
            "FROM eve_sde_type_ids"
            f"{' WHERE sdet_published' if only_published else ''};"
        )
        if rows is None:
            return {}
        data = {}
        for row in rows:
            type_id: int = row[0]
            market_group_id: typing.Optional[int] = row[6]
            group_id: int = row[11]

            cached_market_group: typing.Optional[QSwaggerMarketGroup] = market_groups.get(market_group_id)
            # группа м.б. неизвестна (неопубликована), например у 'Liminal Zirnitra Wreck' группа 'Wreck' не published
            cached_group: typing.Optional[QSwaggerGroup] = groups.get(group_id)

            data[type_id] = QSwaggerTypeId(
                cached_market_group,
                cached_group,
                row)

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
                # TODO: в то же время есть флаг load_unknown_type_blueprints, который тут надо обработать
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
            " solar_system_name,"
            " station_type_name "
            "FROM esi_known_stations "
            "WHERE name=%(nm)s;",
            {'nm': station_name}
        )
        if row is None:
            return None
        station_type_id: int = row[2]
        station_type: QSwaggerTypeId = type_ids.get(station_type_id)  # маловероятно, что тип неизвестен
        cached_station: QSwaggerStation = QSwaggerStation(row[0], station_name, row[1], row[3], station_type, row[4])
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
        if not ids:
            return {}
        rows = self.db.select_all_rows(
            "SELECT"
            " location_id,"
            " name,"
            " solar_system_id,"
            " station_type_id,"
            " solar_system_name,"
            " station_type_name "
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
            data[station_id] = QSwaggerStation(station_id, row[1], row[2], row[4], station_type, row[5])
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

    def get_corporation_container_places(
            self,
            corporation_id: int,
            assets: typing.Dict[int, QSwaggerCorporationAssetsItem],
            blueprints: typing.Dict[int, QSwaggerCorporationBlueprint]) -> None:
        rows = self.db.select_all_rows(
            """
SELECT
 a.eca_item_id,
 CASE office.eca_location_type
  WHEN 'item' THEN
   CASE office.eca_location_flag
    WHEN 'OfficeFolder' THEN office.eca_location_id
    ELSE (select x.eca_location_id from esi_corporation_assets x where x.eca_item_id=a.eca_location_id)
   END
  WHEN 'station' THEN office.eca_location_id
  ELSE NULL
 END as station_id
FROM
 eve_sde_type_ids t,
 esi_corporation_assets a
  INNER JOIN esi_corporation_assets AS office ON (office.eca_item_id=a.eca_location_id)
WHERE
 a.eca_corporation_id=%(id)s AND
 t.sdet_type_id=a.eca_type_id AND
 a.eca_is_singleton AND
 a.eca_name IS NOT NULL AND
 a.eca_location_flag LIKE 'CorpSAG%%' AND
 t.sdet_group_id in (448,649,12);
""",
            # 12 = Cargo Container
            # 448 = Audit Log Secure Container
            # 649 Freight Container
            # исправь также load_corporation_assets
            {'id': corporation_id}
        )
        # Инициализирует контейнеры указанной корпорации, которые имели название и располагались в корпангаре.
        # После чего перебирает все ассеты корпорации и указывает расположение предметов, которые находились в
        # обнаруженных контейнерах. А после этого повторяет те же действия для чертежей.
        # По правилам работы конвейера нас интересуют лишь только предметы, расположенные в именованных коробках.
        if rows is not None:
            places: typing.Dict[int, int] = {}
            for row in rows:
                container_id: int = row[0]
                station_id: int = row[1]
                places[container_id] = station_id
                if assets and station_id:
                    container: QSwaggerCorporationAssetsItem = assets.get(container_id)
                    if container:
                        container.set_station_id(station_id)
            if assets:
                for a in assets.values():
                    station_id: typing.Optional[int] = places.get(a.location_id, None)
                    if station_id:
                        a.set_station_id(station_id)
            if blueprints:
                for b in blueprints.values():
                    station_id: typing.Optional[int] = places.get(b.location_id, None)
                    if station_id:
                        b.set_station_id(station_id)
            del rows

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

    def get_internal_corporation_industry_jobs(
            self,
            rows: typing.Any,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            blueprints: typing.Dict[int, QSwaggerBlueprint],
            characters: typing.Dict[int, QSwaggerCharacter],
            stations: typing.Dict[int, QSwaggerStation],
            corporation_assets: typing.Dict[int, QSwaggerCorporationAssetsItem],
            corporation_blueprints: typing.Dict[int, QSwaggerCorporationBlueprint],
            load_unknown_type_blueprints: bool = True) -> typing.Dict[int, QSwaggerCorporationIndustryJob]:
        # получаем список пилотов, которые запустили работы, обычно 100 уникальных пилотов на 3000 работах
        unique_installer_ids: typing.List[int] = list(set([r[1] for r in rows]))
        if unique_installer_ids:
            unknown_installer_ids: typing.List[int] = [c_id for c_id in unique_installer_ids if not characters.get(c_id)]
            if unknown_installer_ids:
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
            if unknown_facility_ids:
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
                prev_product_type_id = product_type_id
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
        return data

    def get_corporation_industry_jobs_active(
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
            "WHERE ecj_status='active' AND ecj_corporation_id=%(id)s;",  # ecj_completed_date IS NULL
            {'id': corporation_id}
        )
        if rows is None:
            return {}
        data = self.get_internal_corporation_industry_jobs(
            rows,
            type_ids,
            blueprints,
            characters,
            stations,
            corporation_assets,
            corporation_blueprints,
            load_unknown_type_blueprints=load_unknown_type_blueprints)
        del rows
        return data

    def get_corporation_industry_jobs_completed(
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
            "WHERE"
            " ecj_corporation_id=%(id)s AND"
            " (ecj_status<>'active' OR ecj_completed_date IS NOT NULL) AND"
            " (CURRENT_TIMESTAMP AT TIME ZONE 'GMT' < (ecj_end_date+interval '1440 minute'));",
            {'id': corporation_id}
        )
        if rows is None:
            return {}
        data = self.get_internal_corporation_industry_jobs(
            rows,
            type_ids,
            blueprints,
            characters,
            stations,
            corporation_assets,
            corporation_blueprints,
            load_unknown_type_blueprints=load_unknown_type_blueprints)
        del rows
        return data

    def get_corporation_blueprints_undelivered(
            self,
            corporation_id: int,
            blueprints: typing.Dict[int, QSwaggerBlueprint],
            load_unknown_type_blueprints: bool = False) -> \
            typing.Tuple[typing.Dict[int, QSwaggerCorporationBlueprint], typing.Dict[int, QSwaggerCorporationAssetsItem]]:
        rows = self.db.select_all_rows("""
select
 a.corporation_id, --0
 a.updated_at, --1
 --j.ecj_updated_at,
 --j.ecj_status,
 j.ecj_facility_id, --2
 j.ecj_activity_id, --3
 j.ecj_blueprint_type_id, --4
 j.ecj_blueprint_location_id, --5
 j.ecj_output_location_id, --6
 j.ecj_runs, --7
 j.ecj_licensed_runs, --8
 j.ecj_product_type_id, --9
 j.ecj_end_date, --10
 j.ecj_probability -- 11
from (
 select eca_corporation_id as corporation_id, max(eca_updated_at) as updated_at
 from esi_corporation_assets
 where eca_corporation_id=%(id)s
 group by eca_corporation_id
) a
  left outer join esi_corporation_industry_jobs j on (
   j.ecj_corporation_id=a.corporation_id and
   (j.ecj_updated_at >= a.updated_at
    --or ((j.ecj_end_date >= a.updated_at) and
    --    ((j.ecj_end_date+interval '90 minute') < a.updated_at)
    --   )
   ) and
   j.ecj_activity_id in (5,8)
  )
where
 j.ecj_corporation_id is not null and
 (j.ecj_end_date-a.updated_at) <= '01:05:00';""",
            {'id': corporation_id}
        )
        if rows is None:
            return {}, {}
        undelivered_blueprints = {}
        undelivered_assets = {}
        item_id: int = 0
        for row in rows:
            activity_id: int = row[3]
            if activity_id == 5:
                type_id: int = row[4]
                num_of_copies: int = row[7]
                runs: int = row[8]
            elif activity_id == 8:
                type_id: int = row[9]
                num_of_copies: int = max(1, math.floor(row[7] * row[11]))
                runs: int = 1  # здесь декриптор неизвестен
            else:
                raise Exception(f"Unsupported activity_id={activity_id}")
            cached_blueprint_type: QSwaggerBlueprint = blueprints.get(type_id)
            if cached_blueprint_type is None and not load_unknown_type_blueprints:
                continue
            for i in range(num_of_copies):
                item_id -= 1
                bpc: QSwaggerCorporationBlueprint = QSwaggerCorporationBlueprint(
                    cached_blueprint_type,
                    row=(
                        item_id,  # item_id: 0
                        type_id,  # type_id: 1
                        row[6],  # location_id: 2
                        'Unlocked',  # location_flag: 3 (??? 'Undelivered')
                        -2,  # quantity: 4 (copy)
                        0,  # TODO: time_efficiency: 5
                        0,  # TODO: material_efficiency: 6
                        runs,  # runs: 7
                        row[10],  # updated_at: 8
                        row[2]  # station_id: 9
                    )
                )
                undelivered_blueprints[item_id] = bpc
                undelivered_assets[item_id] = QSwaggerCorporationAssetsItem(
                    cached_blueprint_type.blueprint_type,
                    row=(
                        bpc.item_id,  # item_id: 0
                        bpc.type_id,  # type_id: 1
                        1,  # quantity: 2
                        bpc.location_id,  # location_id: 3
                        'item', # location_type: 4
                        bpc.location_flag,  # location_flag: 5
                        True,  # is_singleton: 6
                        None,  # name: 7
                        row[10],  # updated_at: 8
                        row[2]  # station_id: 9
                    )
                )
        del rows
        return undelivered_blueprints, undelivered_assets

    # -------------------------------------------------------------------------
    # corporations/{corporation_id}/orders/
    # -------------------------------------------------------------------------

    def get_internal_corporation_orders(
            self,
            rows: typing.Any,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            characters: typing.Dict[int, QSwaggerCharacter],
            stations: typing.Dict[int, QSwaggerStation]) -> typing.Dict[int, QSwaggerCorporationOrder]:
        # получаем список пилотов, которые разместили ордера
        unique_issuer_ids: typing.List[int] = list(set([r[8] for r in rows]))
        if unique_issuer_ids:
            unknown_issuer_ids: typing.List[int] = [c_id for c_id in unique_issuer_ids if not characters.get(c_id)]
            if unknown_issuer_ids:
                unknown_order_issuers: typing.Dict[int, QSwaggerCharacter] = self.get_characters(unknown_issuer_ids)
                for (character_id, cached_character) in unknown_order_issuers.items():
                    characters[character_id] = cached_character
                del unknown_order_issuers
            del unknown_issuer_ids
        del unique_issuer_ids
        # получаем список рынков, на которых размещены ордера
        unique_location_ids: typing.List[int] = list(set([r[2] for r in rows]))
        if unique_location_ids:
            unknown_location_ids: typing.List[int] = [c_id for c_id in unique_location_ids if not stations.get(c_id)]
            if unknown_location_ids:
                unknown_order_locations: typing.Dict[int, QSwaggerStation] = self.get_stations(unknown_location_ids, type_ids)
                for (location_id, cached_location) in unknown_order_locations.items():
                    stations[location_id] = cached_location
                del unknown_order_locations
            del unknown_location_ids
        del unique_location_ids
        # обработка данных по корпоративным ордерам и связывание их с другими кешированными объектами
        data = {}
        prev_issued_by: int = -1
        cached_issuer: typing.Optional[QSwaggerCharacter] = None
        prev_type_id: int = -1
        cached_type: typing.Optional[QSwaggerTypeId] = None
        prev_location_id: int = -1
        cached_location: typing.Optional[QSwaggerStation] = None
        for row in rows:
            order_id: int = row[0]
            type_id: int = row[1]
            location_id: int = row[2]
            issued_by: int = row[8]
            # определяем предмет, выставленный в ордере, например Keepstar
            if prev_type_id != type_id:
                prev_type_id = type_id
                cached_type = type_ids.get(type_id)
            # определяем пилота (обычно известен) т.к. добавляется в БД синхронно ордеру (если не удалён вручную)
            if prev_issued_by != issued_by:
                prev_issued_by = issued_by
                cached_issuer = characters[issued_by]
            # определяем рынок (обычно езвестен) т.к. добавляется в БД синхронно ордеру (и не удаляется), но к
            # маркету может пропасть доступ и q_universe_preload.py не сможет получить информацию о нём
            if prev_location_id != location_id:
                prev_location_id = location_id
                cached_location = stations.get(location_id)
            # добавляем новую корпоративную работку
            data[order_id] = QSwaggerCorporationOrder(
                cached_type,  # неизвестен, если в БД нет данных об этом типе предмета (пока не обновится esi)
                cached_issuer,  # обычно известен, т.к. добавляется в БД синхронно работе (если не удалён вручную)
                cached_location,  # меркеты обычно известны, если не пропал доступ (и БД неотсинхронизирована)
                row)
        return data

    def get_corporation_orders_active(
            self,
            corporation_id: int,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            characters: typing.Dict[int, QSwaggerCharacter],
            stations: typing.Dict[int, QSwaggerStation]) -> typing.Dict[int, QSwaggerCorporationOrder]:
        rows = self.db.select_all_rows(  # около 1000 одновременных активных ордеров, или больше...
            "SELECT"
            " ecor_order_id,"
            " ecor_type_id,"
            " ecor_location_id,"
            " ecor_is_buy_order,"
            " ecor_price,"
            " ecor_volume_total,"
            " ecor_volume_remain,"
            " ecor_issued,"
            " ecor_issued_by,"
            " ecor_duration,"
            " ecor_escrow "
            "FROM esi_corporation_orders "
            "WHERE not ecor_history AND ecor_corporation_id=%(id)s;",
            {'id': corporation_id}
        )
        if rows is None:
            return {}
        data = self.get_internal_corporation_orders(
            rows,
            type_ids,
            characters,
            stations)
        del rows
        return data

    # -------------------------------------------------------------------------
    # conveyor
    # -------------------------------------------------------------------------

    def get_conveyor_limits(self,
                            type_ids: typing.Dict[int, QSwaggerTypeId],
                            corporations: typing.Dict[int, QSwaggerCorporation],
                            stations: typing.Dict[int, QSwaggerStation]) -> \
            typing.Dict[int, typing.List[QSwaggerConveyorLimit]]:
        rows = self.db.select_all_rows(  # около 1000 одновременных активных ордеров, или больше...
            "SELECT"
            " cl_type_id,"
            " cl_trade_hub,"
            " cl_trader_corp,"
            " cl_approximate "
            "FROM conveyor_limits "
            "WHERE cl_trader_corp in (select * from unnest(%(ids)s));",
            {'ids': list(corporations.keys())}
        )
        if rows is None:
            return {}
        # получаем список рынков, на которых размещены ордера и настроены лимиты
        unique_trade_hub_ids: typing.List[int] = list(set([r[1] for r in rows]))
        if unique_trade_hub_ids:
            unknown_trade_hub_ids: typing.List[int] = [c_id for c_id in unique_trade_hub_ids if not stations.get(c_id)]
            if unknown_trade_hub_ids:
                unknown_limit_trade_hubs: typing.Dict[int, QSwaggerStation] = self.get_stations(unknown_trade_hub_ids,
                                                                                                type_ids)
                for (trade_hub_id, cached_trade_hub) in unknown_limit_trade_hubs.items():
                    stations[trade_hub_id] = cached_trade_hub
                del unknown_limit_trade_hubs
            del unknown_trade_hub_ids
        del unique_trade_hub_ids
        # обработка данных по лимитам конвейера и связывание их с другими кешированными объектами
        data = {}
        for row in rows:
            # получаем информацию о предмете
            type_id: int = row[0]
            cached_item_type: QSwaggerTypeId = type_ids.get(type_id)
            # получаем информацию о торговом хабе
            trade_hub_id: int = row[1]
            cached_trade_hub: QSwaggerStation = stations.get(trade_hub_id)
            # получаем информацию о торговой корпорации
            corporation_id: int = row[2]
            cached_corporation: QSwaggerCorporation = corporations.get(corporation_id)
            # добавляем лимит
            limit: QSwaggerConveyorLimit = QSwaggerConveyorLimit(
                cached_item_type,
                cached_trade_hub,
                cached_corporation,
                row)
            limits: typing.List[QSwaggerConveyorLimit] = data.get(type_id)
            if not limits:
                data[type_id] = [limit]
            else:
                limits.append(limit)
        return data

    def get_conveyor_requirements(
            self,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            conveyor_limits: typing.Dict[int, typing.List[QSwaggerConveyorLimit]]) -> \
            typing.Dict[int, QSwaggerConveyorRequirement]:
        rows = self.db.select_all_rows("""
select
 l.type_id,
 --t.sdet_type_name as type_name,
 l.limit,
 o.remain,
 --case when o.remain is null then l.limit else l.limit - o.remain end required,
 case when o.remain is null then 0.0
      else o.remain::double precision / l.limit
 end rest
from (
 select cl_type_id as type_id, sum(cl_approximate) as limit
 from conveyor_limits
 group by 1
) as l left outer join (
 select o.ecor_type_id as type_id, sum(o.ecor_volume_remain) as remain
 from (
  select ecor_type_id, ecor_corporation_id, ecor_location_id, ecor_volume_remain 
  from esi_corporation_orders
  where
   not ecor_history and
   not ecor_is_buy_order and
   (ecor_type_id, ecor_location_id, ecor_corporation_id) in (select cl_type_id, cl_trade_hub, cl_trader_corp from conveyor_limits)
 ) o
 group by 1 
) as o on (o.type_id=l.type_id)
 left outer join eve_sde_type_ids as t on (t.sdet_type_id=l.type_id)
where
 l.type_id in (select sdebp_product_id from eve_sde_blueprint_products)
 --and (o.remain is null or (l.limit > o.remain))
--order by rest;
""")
        if rows is None:
            return {}
        # обработка данных по лимитам конвейера и связывание их с другими кешированными объектами
        data: typing.Dict[int, QSwaggerConveyorRequirement] = {}
        for row in rows:
            # получаем информацию о предмете
            type_id: int = row[0]
            cached_item_type: QSwaggerTypeId = type_ids.get(type_id)
            cached_conveyor_limit: typing.Optional[typing.List[QSwaggerConveyorLimit]] = conveyor_limits.get(type_id)
            # добавляем потребность
            requirement: QSwaggerConveyorRequirement = QSwaggerConveyorRequirement(
                cached_item_type,
                cached_conveyor_limit,
                row)
            data[type_id] = requirement
        return data

    def get_conveyor_best_formulas(
            self,
            type_ids: typing.Dict[int, QSwaggerTypeId]) -> \
            typing.Dict[int, QSwaggerConveyorBestFormula]:
        rows = self.db.select_all_rows("""
select
 x.product_type_id,
 x.decryptor_type_id,
 x.profit_w_decryptor,
 c0.profit_wo_decryptor
from (
 select
  f.cf_product_type_id product_type_id,
  --f.cf_blueprint_type_id as blueprint_type_id,
  --f.cf_prior_blueprint_type_id as prior_blueprint_type_id,
  f.cf_decryptor_type_id decryptor_type_id,
  --c.cfc_single_product_profit as abs_profit,
  max(c.cfc_single_product_profit) as profit_w_decryptor
 from
  qi.conveyor_formula_calculus c,
  qi.conveyor_formulas f
 where
  --f.cf_product_type_id in (54782, 54783, 54781, 54785, 54786, 54784) and
  c.cfc_best_choice and
  f.cf_formula=c.cfc_formula and
  c.cfc_trade_hub=60003760
 group by f.cf_product_type_id, f.cf_decryptor_type_id
) x
 left outer join (
  select
   f.cf_product_type_id product_type_id,
   max(c.cfc_single_product_profit) profit_wo_decryptor
  from
   qi.conveyor_formula_calculus c,
   qi.conveyor_formulas f
  where
   f.cf_formula=c.cfc_formula and
   c.cfc_trade_hub=60003760 and
   f.cf_decryptor_type_id is null
  group by f.cf_product_type_id
 ) as c0 on (x.product_type_id=c0.product_type_id);
""")
        if rows is None:
            return {}
        # обработка данных по лимитам конвейера и связывание их с другими кешированными объектами
        data: typing.Dict[int, QSwaggerConveyorBestFormula] = {}
        for row in rows:
            # получаем информацию о предмете
            type_id: int = row[0]
            decryptor_type_id: int = row[1]
            cached_item_type: QSwaggerTypeId = type_ids.get(type_id)
            cached_decryptor_type: QSwaggerTypeId = type_ids.get(decryptor_type_id)
            # добавляем наилучшую формулу
            best_formula: QSwaggerConveyorBestFormula = QSwaggerConveyorBestFormula(
                cached_item_type,
                cached_decryptor_type,
                row)
            data[type_id] = best_formula
        return data

    def get_conveyor_formulas(
            self,
            type_ids: typing.Dict[int, QSwaggerTypeId],
            blueprints: typing.Dict[int, QSwaggerBlueprint],
            stations: typing.Dict[int, QSwaggerStation]) -> \
            typing.Dict[int, typing.List[QSwaggerConveyorFormula]]:
        rows = self.db.select_all_rows("""
select
 f.cf_formula,--0
 f.cf_blueprint_type_id,--1
 f.cf_activity,--2
 f.cf_product_type_id,--3
 f.cf_customized_runs,--4
 f.cf_decryptor_type_id,--5
 f.cf_ancient_relics,--6
 f.cf_prior_blueprint_type_id,--7
 f.cf_material_efficiency,--8
 f.cf_time_efficiency,--9
 c.cfc_products_per_single_run,--10
 c.cfc_products_num,--11
 c.cfc_best_choice,--12
 c.cfc_industry_hub,--13
 c.cfc_trade_hub,--14
 c.cfc_trader_corp,--15
 c.cfc_buying_brokers_fee,--16
 c.cfc_sales_brokers_fee,--17
 c.cfc_sales_tax,--18
 c.cfc_fuel_price_isk,--19
 c.cfc_materials_cost,--20
 c.cfc_materials_cost_with_fee,--21
 c.cfc_purchase_volume,--22
 c.cfc_materials_transfer_cost,--23
 c.cfc_jobs_cost,--24
 c.cfc_ready_volume,--25
 c.cfc_ready_transfer_cost,--26
 c.cfc_products_recommended_price,--27
 c.cfc_products_sell_fee_and_tax,--28
 c.cfc_single_product_price_wo_fee_tax,--29
 c.cfc_total_gross_cost,--30
 c.cfc_single_product_cost,--31
 c.cfc_product_mininum_price,--32
 c.cfc_single_product_profit--33
from qi.conveyor_formulas f, qi.conveyor_formula_calculus c
where f.cf_formula=c.cfc_formula
order by f.cf_blueprint_type_id, f.cf_activity, f.cf_product_type_id, f.cf_prior_blueprint_type_id;
""")
        if rows is None:
            return {}
        # ---
        cached_blueprint: typing.Optional[QSwaggerBlueprint] = None
        cached_activity: typing.Optional[typing.Union[QSwaggerBlueprintManufacturing, QSwaggerBlueprintInvention,
                               QSwaggerBlueprintCopying, QSwaggerBlueprintResearchMaterial,
                               QSwaggerBlueprintResearchTime, QSwaggerBlueprintReaction]] = None  # noqa
        cached_product_type: typing.Optional[QSwaggerTypeId] = None  # noqa
        cached_prior_blueprint: typing.Optional[QSwaggerBlueprint] = None  # noqa
        cached_industry_hub: typing.Optional[QSwaggerStation] = None  # noqa
        cached_trade_hub: typing.Optional[QSwaggerStation] = None  # noqa
        # ---
        prev_blueprint_type_id: int = -1
        prev_activity_id: int = -1
        prev_product_type_id: int = -1
        prev_prior_blueprint_type_id: int = -1
        prev_industry_hub_id: int = -1
        prev_trade_hub_id: int = -1
        # ---
        # обработка данных по лимитам конвейера и связывание их с другими кешированными объектами
        data: typing.Dict[int, typing.List[QSwaggerConveyorFormula]] = {}
        for row in rows:
            # получаем информацию о формуле
            formula_id: int = row[0]
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же чертежей
            blueprint_type_id: int = row[1]
            if blueprint_type_id != prev_blueprint_type_id:
                prev_blueprint_type_id = blueprint_type_id
                # возможна ситуация, когда чертёж неизвестен
                cached_blueprint = blueprints.get(blueprint_type_id)
                prev_activity_id = -1
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же activity
            activity_id: int = row[2]
            if cached_blueprint:
                if activity_id != prev_activity_id:
                    prev_activity_id = activity_id
                    # возможная ситуация, что чертёж есть, а активность выше не добавлена, т.к. продукт non published:
                    # - 2179  Sansha Wrath Cruise Missile Blueprint (Haunter Cruise Missile не published)
                    cached_activity = cached_blueprint.get_activity(activity_id)
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же продуктов
            product_type_id: int = row[3]
            if product_type_id != prev_product_type_id:
                prev_product_type_id = product_type_id
                cached_product_type = type_ids.get(product_type_id)
            # используем факт того, что набор данных отсортирован и прореживаем ненужный поиск одних и тех же чертежей
            prior_blueprint_type_id: int = row[7]
            if prior_blueprint_type_id != prev_prior_blueprint_type_id:
                prev_prior_blueprint_type_id = prior_blueprint_type_id
                # возможна ситуация, когда чертёж неизвестен
                cached_prior_blueprint = blueprints.get(prior_blueprint_type_id)
            # используем факт того, что торговые и производственные хабы сильно разрежены в наборе данных
            industry_hub_id: int = row[13]
            if industry_hub_id != prev_industry_hub_id:
                prev_industry_hub_id = industry_hub_id
                cached_industry_hub = stations.get(industry_hub_id)
            trade_hub_id: int = row[14]
            if trade_hub_id != prev_trade_hub_id:
                prev_trade_hub_id = trade_hub_id
                cached_trade_hub = stations.get(trade_hub_id)
            # информация о декрипторах не может быть последовательно отсортирована
            decryptor_type_id: int = row[5]
            cached_decryptor_type: typing.Optional[QSwaggerTypeId] = type_ids.get(decryptor_type_id)
            # добавляем conveyor-формулу
            conveyor_formula: QSwaggerConveyorFormula = QSwaggerConveyorFormula(
                cached_blueprint,
                cached_activity,
                cached_product_type,
                cached_decryptor_type,
                cached_prior_blueprint,
                cached_trade_hub,
                cached_trade_hub,
                row)
            conveyor_formulas: typing.Optional[typing.List[QSwaggerConveyorFormula]] = data.get(product_type_id)
            if conveyor_formulas:
                conveyor_formulas.append(conveyor_formula)
            else:
                data[product_type_id] = [conveyor_formula]
        return data
