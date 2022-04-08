# -*- encoding: utf-8 -*-
""" Entry point of qind_postgresql_db, also contains shortcuts for all required objects """

from .db_interface import QIndustrialistDatabase  # noqa
from .db_wij import QWorkflowIndustryJobs  # noqa
from .db_dictionaries import QDictionaries  # noqa
from .db_swagger_interface import QSwaggerInterface  # noqa
from .db_swagger_cache import *  # noqa
from .db_swagger_translator import QSwaggerTranslator  # noqa
from .db_swagger_dictionary import QSwaggerDictionary

__version__ = '0.10.1'
