# -*- encoding: utf-8 -*-
""" Entry point of eve_esi_interface, also contains shortcuts for all required objects """

from .auth_cache import EveESIAuth  # noqa
from .eve_esi_client import EveESIClient  # noqa
from .eve_esi_interface import EveOnlineInterface  # noqa
from .error import EveOnlineClientError  # noqa

__version__ = '0.8.1'
