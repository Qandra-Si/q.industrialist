import math
import typing
import profit
import eve_sde_tools
import eve_esi_tools


def get_industry_cost_index(
        product_type_id: int,
        action: str,
        # ������� ��������� ������������ ��� ��������� ������ (������� � ��������� ������ � ���������� ��������)
        industry_cost_indices:  typing.List[profit.QIndustryCostIndices]) \
        -> typing.Tuple[profit.QIndustryCostIndices, float]:
    # �������� ���������� � ���������������� �������� � �������, ��� ��������� ���� �������
    system_indices: profit.QIndustryCostIndices = next((
        _ for _ in industry_cost_indices
        if product_type_id in _.product_ids), None)
    if system_indices is None:
        system_indices = next((
            _ for _ in industry_cost_indices
            if not _.product_ids), None)
    assert system_indices is not None
    # �������� ���������������� ������ � �������
    cost_index: float = next((
        float(_['cost_index']) for _ in system_indices.cost_indices
        if _['activity'] == action), None)
    assert cost_index is not None
    # ���������� tuple
    return system_indices, cost_index


def calc_estimated_items_value(
        blueprint_type_id: int,
        activity: str,
        sde_bp_materials,
        eve_market_prices_data) -> float:
    if activity in ['manufacturing', 'reaction']:
        # EIV ��������� �� ���������� ������������ � ���������������� ����������
        bp0_dict = eve_sde_tools.get_blueprint_any_activity(sde_bp_materials, activity, blueprint_type_id)
    elif activity in ['invention']:
        # EIV ��������� �� ���������� ������������ � ������������ T2 �������� (�� �������� �������)
        bp0_dict = eve_sde_tools.get_blueprint_any_activity(sde_bp_materials, 'manufacturing', blueprint_type_id)
    elif activity in ['copying']:
        # EIV ��������� �� ���������� ������������ � ������������ T1 �������� (�� �����)
        bp0_dict = eve_sde_tools.get_blueprint_any_activity(sde_bp_materials, 'manufacturing', blueprint_type_id)
    else:
        assert 0
    assert bp0_dict is not None and 'materials' in bp0_dict

    estimated_items_value: float = 0.0
    materials = bp0_dict.get('materials')

    # ���������� ������ ����������, ������� ����� �������������� � ������������
    for m in materials:
        material_tid: int = int(m['typeID'])
        material_qty: int = int(m['quantity'])
        material_adjusted_price: float = eve_esi_tools.get_material_adjusted_price(
            material_tid,
            eve_market_prices_data)
        estimated_items_value += material_qty * material_adjusted_price

    # ������� EIV, ������� ����������� ��� ���������� ��������� job cost
    return math.ceil(estimated_items_value)

