#!/usr/bin/python3
# -*- coding: utf-8-
"""
The constants of the custom component
"""
from typing import Any

__VERSION__: str
__GITHUB_URL__: str
__ISSUE_URL__: str
__MANIFEST_TIME__: float
__MANIFEST__: dict[str, Any]
DOMAIN: str = 'ha_enedis_dataconnect'
# Base component constants
PLATFORM: str = 'sensor'
PLATFORMS: list = [PLATFORM]
CLIENT_ID_KEY: str = "client_id"
CLIENT_SECRET_KEY: str = "client_secret"
TOKEN_KEY: str = 'token'
PDL_KEY: str = 'pdl'
REDIRECT_URI_KEY: str = 'redirect_uri'
DEFAULT_REDIRECT_URI: str = 'http://localhost'
SCAN_INTERVAL_KEY: str = 'scan_interval'
DEFAULT_SCAN_INTERVAL: int = 30
MIN_SCAN_INTERVAL: int = 15
MAX_SCAN_INTERVAL: int = 600
ENDPOINT_TOKEN_URL = "https://ext.prod-sandbox.api.enedis.fr/oauth2/v3/"
