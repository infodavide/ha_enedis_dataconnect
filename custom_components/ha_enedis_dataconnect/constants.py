#!/usr/bin/python3
# -*- coding: utf-8-
"""
The constants of the custom component
"""
import json
import logging
from pathlib import Path
from typing import Any

__VERSION__: str
__GITHUB_URL__: str
__ISSUE_URL__: str
__MANIFEST_TIME__: float
__MANIFEST__: dict[str, Any]
_LOGGER = logging.getLogger(__name__)
DOMAIN: str = 'ha_enedis_dataconnect'
# Base component constants
PLATFORM: str = 'sensor'
PLATFORMS: list = [PLATFORM]
INTEGRATION_PATH: Path = Path(__file__).parent
ENDPOINT_TOKEN_URL = 'https://ext.prod-sandbox.api.enedis.fr/oauth2/v3/'
UPDATE_ENEDIS_EVENT_TYPE: str = 'enedis_update'

CLIENT_ID_KEY: str = 'client_id'
CLIENT_SECRET_KEY: str = 'client_secret'
TOKEN_KEY: str = 'token'
PDL_KEY: str = 'pdl'
PEAK_HOUR_COST_KEY: str = 'peak_hour_cost'
REDIRECT_URI_KEY: str = 'redirect_uri'
SCAN_INTERVAL_KEY: str = 'scan_interval'
COORDINATOR_KEY: str = 'enedis_coordinator'
# noinspection SpellCheckingInspection
UPDATE_UNLISTENER_KEY: str = 'enedis_update_unlistener'
# noinspection SpellCheckingInspection
EVENT_UNLISTENER_KEY: str = 'enedis_event_unlistener'

MIN_SCAN_INTERVAL: int = 15
MAX_SCAN_INTERVAL: int = 600

DEFAULT_PDL: str = ''
DEFAULT_CLIENT_ID: str = ''
DEFAULT_CLIENT_SECRET: str = ''
DEFAULT_PEAK_HOUR_COST: float = 1.0
DEFAULT_REDIRECT_URI: str = 'http://localhost'
DEFAULT_SCAN_INTERVAL: int = 30

path = INTEGRATION_PATH.joinpath('default.json')
if path.exists():
    _LOGGER.debug("Reading default configuration from file: default.json")
    with path.open(mode='r', encoding='utf-8') as f:
        data: dict[str, Any] = json.load(f)
        if PDL_KEY in data:
            DEFAULT_PDL = data[PDL_KEY]
        if CLIENT_ID_KEY in data:
            DEFAULT_CLIENT_ID = data[CLIENT_ID_KEY]
        if CLIENT_SECRET_KEY in data:
            DEFAULT_CLIENT_SECRET = data[CLIENT_SECRET_KEY]
else:
    _LOGGER.debug("Default configuration not found in file: default.json")
_LOGGER.debug("Default configuration: %s, %s, %s, %s, %s, %s", DEFAULT_PDL, DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET, str(DEFAULT_PEAK_HOUR_COST), DEFAULT_REDIRECT_URI, str(DEFAULT_SCAN_INTERVAL))
