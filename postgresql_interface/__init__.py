# -*- encoding: utf-8 -*-
""" Entry point of qind_postgresql_db, also contains shortcuts for all required objects """

from .db_interface import QIndustrialistDatabase  # noqa
from .db_wij import QWorkflowIndustryJobs  # noqa
from .db_dictionaries import QDictionaries  # noqa

__version__ = '0.7.6'
