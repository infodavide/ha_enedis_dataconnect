#!/usr/bin/python3
# -*- coding: utf-8-
"""
The constants of the custom component
"""
import json
import logging
from enum import StrEnum
from pathlib import Path
from typing import Any

from homeassistant.const import Platform, UnitOfEnergy, UnitOfPower

LOGGER = logging.getLogger(__name__)
EMPTY_STRING: str = ''
DATE_FORMAT: str = '%Y-%m-%d'
DATE_TIME_FORMAT: str = '%Y-%m-%d %H:%M'

MANIFEST: dict[str, Any] = {}
VERSION: str = '0.0.1'
GITHUB_URL: str = EMPTY_STRING
ISSUE_URL: str = EMPTY_STRING
DOMAIN: str = 'ha_enedis_dataconnect'
DATA_HASS_CONFIG = DOMAIN + "_hass_config"
# Base component constants
PLATFORM: str = Platform.SENSOR
PLATFORMS: list = [PLATFORM]
INTEGRATION_PATH: Path = Path(__file__).parent
ENDPOINT_URL: str = 'https://ext.prod-sandbox.api.enedis.fr'
ENDPOINT_TOKEN_URL: str = ENDPOINT_URL + '/oauth2/v3/'
UPDATE_ENEDIS_EVENT_TYPE: str = 'enedis_update'

VERSION_KEY: str = 'version'
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
ENTITY_NAME_KEY: str = "name"
ENTITY_UNIT_KEY: str = "unit"
ENTITY_DELAY_KEY: str = "delay"

MIN_SCAN_INTERVAL: int = 15
MAX_SCAN_INTERVAL: int = 600

DEFAULT_PDL: str = EMPTY_STRING
DEFAULT_CLIENT_ID: str = EMPTY_STRING
DEFAULT_CLIENT_SECRET: str = EMPTY_STRING
DEFAULT_PEAK_HOUR_COST: float = 1.0
DEFAULT_REDIRECT_URI: str = 'http://localhost'
DEFAULT_SCAN_INTERVAL: int = 60 * 2
DEFAULT_HISTORY_SCAN_INTERVAL: int = 60 * 10
DEFAULT_ENTITY_DELAY: int = 60
EURO: str = 'euro'
SENSOR_TYPES: dict[str, dict[str, Any]] = {}


class EnedisSensorTypeEnum(StrEnum):
    """
    The enumeration representing the type of sensor
    """
    PRODUCTION = 'production'
    CONSUMPTION = 'consumption'


class EnedisHistoryDetailsTypeEnum(StrEnum):
    """
    The enumeration representing the type of details
    """
    ALL = 'all'
    PEAK_HOURS = 'peak_hours'
    OFF_PEAK_HOURS = 'off_peak_hours'


class EnedisDetailsPeriodEnum(StrEnum):
    """
    The enumeration representing the period of details
    """
    HOURS = 'hours'
    DAYS = 'days'
    MONTHS = 'months'


class SensorTypeEnum(StrEnum):
    """
    The enumeration representing the type of sensor
    """
    MAIN_SENSOR_TYPE = 'main'
    CONSUMED_HISTORY_SENSOR_TYPE = 'consumed_history'
    CONSUMED_HISTORY_PEAK_HOURS_SENSOR_TYPE = 'consumed_history_peak_hours'
    CONSUMED_HISTORY_OFF_PEAK_HOURS_SENSOR_TYPE = 'consumed_history_off_peak_hours'
    CONSUMED_YESTERDAY_COST_SENSOR_TYPE = 'consumed_yesterday_cost'
    CONSUMED_ENERGY_SENSOR_TYPE = 'consumed_energy'
    CONSUMED_ENERGY_DETAILS_HOURS_SENSOR_TYPE = 'consumed_energy_detail_hours'
    CONSUMED_ENERGY_DETAILS_HOURS_COST_SENSOR_TYPE = 'consumed_energy_detail_hours_cost'


def _put_sensor_type(d: dict[str, Any]) -> None:
    """
    Add the sensor type to the dictionary using the entity name as the key
    :param d: the data
    """
    SENSOR_TYPES[d[ENTITY_NAME_KEY]] = d


_put_sensor_type({
    ENTITY_NAME_KEY: SensorTypeEnum.MAIN_SENSOR_TYPE,
    ENTITY_DELAY_KEY: DEFAULT_ENTITY_DELAY,
    ENTITY_UNIT_KEY: UnitOfPower.KILO_WATT
})
_put_sensor_type({
    ENTITY_NAME_KEY: SensorTypeEnum.CONSUMED_HISTORY_SENSOR_TYPE,
    ENTITY_DELAY_KEY: DEFAULT_ENTITY_DELAY,
    ENTITY_UNIT_KEY: UnitOfPower.KILO_WATT
})
_put_sensor_type({
    ENTITY_NAME_KEY: SensorTypeEnum.CONSUMED_HISTORY_PEAK_HOURS_SENSOR_TYPE,
    ENTITY_DELAY_KEY: DEFAULT_ENTITY_DELAY,
    ENTITY_UNIT_KEY: UnitOfPower.KILO_WATT
})
_put_sensor_type({
    ENTITY_NAME_KEY: SensorTypeEnum.CONSUMED_YESTERDAY_COST_SENSOR_TYPE,
    ENTITY_DELAY_KEY: DEFAULT_ENTITY_DELAY,
    ENTITY_UNIT_KEY: EURO
})
_put_sensor_type({
    ENTITY_NAME_KEY: SensorTypeEnum.CONSUMED_ENERGY_SENSOR_TYPE,
    ENTITY_DELAY_KEY: DEFAULT_ENTITY_DELAY,
    ENTITY_UNIT_KEY: UnitOfEnergy.KILO_WATT_HOUR
})
_put_sensor_type({
    ENTITY_NAME_KEY: SensorTypeEnum.CONSUMED_ENERGY_DETAILS_HOURS_SENSOR_TYPE,
    ENTITY_DELAY_KEY: DEFAULT_ENTITY_DELAY,
    ENTITY_UNIT_KEY: UnitOfEnergy.KILO_WATT_HOUR
})
_put_sensor_type({
    ENTITY_NAME_KEY: SensorTypeEnum.CONSUMED_ENERGY_DETAILS_HOURS_COST_SENSOR_TYPE,
    ENTITY_DELAY_KEY: DEFAULT_ENTITY_DELAY,
    ENTITY_UNIT_KEY: EURO
})

path = INTEGRATION_PATH.joinpath('manifest.json')
if path.exists():
    LOGGER.debug("Reading manifest from file: manifest.json")
    with path.open(mode='r', encoding='utf-8') as f:
        MANIFEST = json.load(f)
        if VERSION_KEY in MANIFEST:
            VERSION = MANIFEST[VERSION_KEY]
        if 'documentation' in MANIFEST:
            GITHUB_URL = MANIFEST['documentation']
        if 'issue_tracker' in MANIFEST:
            ISSUE_URL = MANIFEST['issue_tracker']
else:
    LOGGER.debug("Manifest not found in file: manifest.json")
path = INTEGRATION_PATH.joinpath('default.json')
if path.exists():
    LOGGER.debug("Reading default configuration from file: default.json")
    with path.open(mode='r', encoding='utf-8') as f:
        data: dict[str, Any] = json.load(f)
        if PDL_KEY in data:
            DEFAULT_PDL = data[PDL_KEY]
        if CLIENT_ID_KEY in data:
            DEFAULT_CLIENT_ID = data[CLIENT_ID_KEY]
        if CLIENT_SECRET_KEY in data:
            DEFAULT_CLIENT_SECRET = data[CLIENT_SECRET_KEY]
else:
    LOGGER.debug("Default configuration not found in file: default.json")
LOGGER.debug("Default configuration: %s, %s, %s, %s, %s, %s", DEFAULT_PDL, DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET, str(DEFAULT_PEAK_HOUR_COST), DEFAULT_REDIRECT_URI, str(DEFAULT_SCAN_INTERVAL))
