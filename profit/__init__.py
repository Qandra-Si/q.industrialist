# -*- encoding: utf-8 -*-
""" Entry point of qind_profit, also contains shortcuts for all required objects """

from .industry_tree import QBaseMaterial  # noqa
from .industry_tree import QMaterial  # noqa
from .industry_tree import QIndustryAction  # noqa
from .industry_tree import QIndustryTree  # noqa
from .industry_plan import QPlannedMaterial  # noqa
from .industry_plan import QPlannedActivity  # noqa
from .industry_plan import QIndustryObtainingPlan  # noqa
from .industry_plan import QIndustryMaterial  # noqa
from .industry_plan import QIndustryMaterialsRepository  # noqa
from .industry_plan import QIndustryPlanCustomization  # noqa
from .industry_plan import QIndustryPlan  # noqa

__version__ = '0.1.2'
