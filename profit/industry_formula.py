# -*- encoding: utf-8 -*-
import math
import typing


class QIndustryFormula:
    class Purchase:
        def __init__(self, type_id: int, quantity: float):
            self.type_id: int = type_id
            self.quantity: float = quantity

    class JobCost:
        def __init__(self,
                     usage_chain: float,
                     solar_system_id: int,
                     blueprint_type_id: int,
                     planned_blueprints: int,
                     planned_runs: int,
                     activity_code: int,
                     role_bonus_job_cost: float,
                     rigs_bonus_job_cost: float,
                     scc_surcharge: float,
                     facility_tax: float):
            # доля работы относительно предыдущих уровней вложенности
            self.usage_chain: float = usage_chain
            # солнечная система в которой планируется работа
            self.solar_system_id: int = solar_system_id
            # type_id чертежа
            self.blueprint_type_id: int = blueprint_type_id
            # количество чертежей
            self.planned_blueprints: int = planned_blueprints
            # количество прогонов
            self.planned_runs: int = planned_runs
            # тип производственной работы
            self.activity_code: int = activity_code
            # [reaction] -> reaction; [manufacturing, copying, invention] -> manufacturing
            self.activity_eiv: int = 9 if activity_code == 9 else 1
            # [manufacturing, reaction] -> 1.0; [copying, invention] -> 0.2
            self.job_cost_base_multiplier: float = 1.0 if activity_code in [1, 9] else 0.02
            # ролевой бонус структуры для выбранного activity_code
            self.role_bonus_job_cost: float = role_bonus_job_cost
            # бонусы модификаторов для выбранного activity_code
            self.rigs_bonus_job_cost: float = rigs_bonus_job_cost
            # дополнительный сбор от CCP, фиксирован 0.04
            self.scc_surcharge: float = scc_surcharge
            # налог на структуре (фиксированный налог на NPC структурах 0.0025; на структурах игроков
            # устанавливается владельцем)
            self.facility_tax: float = facility_tax
            """
            Итоговая стоимость:

            estimated_items_value: float =?= function(blueprint_type_id, activity_eiv)
            industry_cost_index: float =?= function(solar_system_id)
            
            job_cost_base: float = estimated_items_value * job_cost_base_multiplier  # ISK
            system_cost: int = int(math.ceil(job_cost_base * industry_cost_index))  # ISK
            structure_role_bonus: int = int(math.ceil(system_cost * role_bonus_job_cost))  # ISK
            structure_rigs_bonus: int = int(math.ceil(system_cost * rigs_bonus_job_cost))  # ISK
            total_job_gross_cost: int = system_cost + structure_role_bonus + structure_rigs_bonus  # ISK
            tax_scc_surcharge: int = int(math.ceil(job_cost_base * scc_surcharge))  # ISK
            tax_facility: int = int(math.ceil(job_cost_base * facility_tax))  # ISK
            total_taxes: int = tax_scc_surcharge + tax_facility  # ISK
            single_run_job_cost: int = total_job_gross_cost + total_taxes  # ISK
            total_job_cost: float = usage_chain * planned_blueprints * planned_runs * single_run_job_cost
            """

    def __init__(self,
                 prior_blueprint_type_id: typing.Optional[int],
                 blueprint_type_id: int,
                 product_type_id: int,
                 decryptor_type_id: typing.Optional[int],
                 customized_runs: int):
        self.prior_blueprint_type_id: typing.Optional[int] = prior_blueprint_type_id  # исходный чертёж, при инвенте
        self.blueprint_type_id: int = blueprint_type_id  # чертёж продукта
        self.product_type_id: int = product_type_id
        self.decryptor_type_id: typing.Optional[int] = decryptor_type_id
        self.customized_runs: int = customized_runs
        self.purchase: typing.List[QIndustryFormula.Purchase] = []
        self.job_costs: typing.List[QIndustryFormula.JobCost] = []

    def append_purchase(self, type_id: int, quantity: float) -> None:
        self.purchase.append(QIndustryFormula.Purchase(type_id, quantity))

    def append_job_cost(
            self,
            usage_chain: float,
            solar_system_id: int,
            blueprint_type_id: int,
            planned_blueprints: int,
            planned_runs: int,
            activity_code: int,
            role_bonus_job_cost: typing.Optional[float],
            rigs_bonus_job_cost: typing.Optional[float],
            scc_surcharge: typing.Optional[float],
            facility_tax: typing.Optional[float]) -> None:
        exist: QIndustryFormula.JobCost = next((
            _ for _ in self.job_costs if _.solar_system_id == solar_system_id and
                                         _.blueprint_type_id == blueprint_type_id and
                                         _.planned_blueprints == planned_blueprints and
                                         _.planned_runs == planned_runs and
                                         _.activity_code == activity_code), None)
        if exist:
            exist.usage_chain += usage_chain
        else:
            self.job_costs.append(QIndustryFormula.JobCost(
                usage_chain,
                solar_system_id,
                blueprint_type_id,
                planned_blueprints,
                planned_runs,
                activity_code,
                role_bonus_job_cost if role_bonus_job_cost is not None else 0.0,
                rigs_bonus_job_cost if rigs_bonus_job_cost is not None else 0.0,
                scc_surcharge if scc_surcharge is not None else 0.04,
                facility_tax if facility_tax is not None else 0.0))

    def calc_materials_cost(self, get_buy_material_price) -> float:
        materials_cost: float = 0.0
        for p in self.purchase:
            materials_cost += get_buy_material_price(p.type_id) * p.quantity
        return materials_cost

    def calc_industry_cost(self, calc_estimated_items_value, get_industry_cost_index) -> float:
        industry_cost: float = 0.0
        for jc in self.job_costs:
            # внешние данные
            estimated_items_value: float = calc_estimated_items_value(jc.blueprint_type_id, jc.activity_eiv)
            industry_cost_index: float = get_industry_cost_index(jc.solar_system_id, jc.activity_code)
            # вычисления
            job_cost_base: float = estimated_items_value * jc.job_cost_base_multiplier  # ISK
            system_cost: int = int(math.ceil(job_cost_base * industry_cost_index))  # ISK
            structure_role_bonus: int = int(math.ceil(system_cost * jc.role_bonus_job_cost))  # ISK
            structure_rigs_bonus: int = int(math.ceil(system_cost * jc.rigs_bonus_job_cost))  # ISK
            total_job_gross_cost: int = system_cost + structure_role_bonus + structure_rigs_bonus  # ISK
            tax_scc_surcharge: int = int(math.ceil(job_cost_base * jc.scc_surcharge))  # ISK
            tax_facility: int = int(math.ceil(job_cost_base * jc.facility_tax))  # ISK
            total_taxes: int = tax_scc_surcharge + tax_facility  # ISK
            single_run_job_cost: int = total_job_gross_cost + total_taxes  # ISK
            total_job_cost: float = jc.usage_chain * jc.planned_blueprints * jc.planned_runs * single_run_job_cost
            """
            # ----------------------------------------------------------------------------------------------------------
            total_job_cost: float = jc.usage_chain * jc.planned_blueprints * jc.planned_runs * \    
                (  # single_run_job_cost
                    (   # total_job_gross_cost
                        # system_cost
                        int(math.ceil(job_cost_base * industry_cost_index)) +
                        # structure_role_bonus
                        int(math.ceil(system_cost * jc.role_bonus_job_cost)) +
                        # structure_rigs_bonus
                        int(math.ceil(system_cost * jc.rigs_bonus_job_cost))
                    ) +
                    (   # total_taxes
                        int(math.ceil(job_cost_base * jc.scc_surcharge)) +  # tax_scc_surcharge
                        int(math.ceil(job_cost_base * jc.facility_tax))  # tax_facility
                    )
                )
            # ----------------------------------------------------------------------------------------------------------
            """
            # аккумулятор цены
            industry_cost += total_job_cost
        return industry_cost
