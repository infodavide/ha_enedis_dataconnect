#!/usr/bin/python3
# -*- coding: utf-8-
"""
The configuration flow of the custom component
"""
import logging
import re
from typing import Any
from collections import OrderedDict
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import DOMAIN, PDL_KEY, DEFAULT_PDL, CLIENT_ID_KEY, DEFAULT_CLIENT_ID, CLIENT_SECRET_KEY, DEFAULT_CLIENT_SECRET, REDIRECT_URI_KEY, DEFAULT_REDIRECT_URI, PEAK_HOUR_COST_KEY, DEFAULT_PEAK_HOUR_COST, SCAN_INTERVAL_KEY, DEFAULT_SCAN_INTERVAL, MIN_SCAN_INTERVAL, MAX_SCAN_INTERVAL, LOGGER
from .enedis_client import EnedisClient

_LOGGER = logging.getLogger(__name__)


async def async_validate_api_access(hass: HomeAssistant, pdl: str, client_id: str, client_secret: str, redirect_uri: str) -> bool:
    """
    Validate the access to the API
    :param hass: the home assistant instance
    :param pdl: the PDL
    :param client_id: the client identifier
    :param client_secret: the client secret
    :param redirect_uri: the redirect URI
    :return: true if the access is valid
    """
    _LOGGER.debug("Validating the access using the client...")
    # noinspection PyTypeChecker
    client: EnedisClient = None
    # noinspection PyBroadException
    try:
        client = EnedisClient(hass, pdl, client_id, client_secret, redirect_uri)
        await hass.async_add_executor_job(client.connect)
        return True
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Cannot connect to the API")
    finally:
        if client:
            await hass.async_add_executor_job(client.close)
    return False


async def async_validate_input(fields: OrderedDict, user_input: dict[str, Any], errors: dict[str, str]) -> dict[str, Any]:
    """
    Validate the user input
    :param fields: the fields used by the voluptuous schema
    :param user_input: the input data
    :param errors: the errors
    :return: the updated schema and the configuration data
    """
    _LOGGER.debug("Validating the input...")
    result: dict[str, Any] = {}
    if PDL_KEY not in user_input or not re.match("\\d{14}", user_input[PDL_KEY]):
        errors[PDL_KEY] = "invalid_pdl"
    else:
        fields[vol.Required(PDL_KEY, default=user_input[PDL_KEY])] = fields[vol.Required(PDL_KEY)]
        result[PDL_KEY] = user_input[PDL_KEY]
    if CLIENT_ID_KEY not in user_input or len(user_input[CLIENT_ID_KEY]) < 1:
        errors[CLIENT_ID_KEY] = "invalid_client_id"
    else:
        fields[vol.Required(CLIENT_ID_KEY, default=user_input[CLIENT_ID_KEY])] = fields[vol.Required(CLIENT_ID_KEY)]
        result[CLIENT_ID_KEY] = user_input[CLIENT_ID_KEY]
    if CLIENT_SECRET_KEY not in user_input or len(user_input[CLIENT_SECRET_KEY]) < 1:
        errors[CLIENT_SECRET_KEY] = "invalid_client_secret"
    else:
        fields[vol.Required(CLIENT_SECRET_KEY, default=user_input[CLIENT_SECRET_KEY])] = fields[vol.Required(CLIENT_SECRET_KEY)]
        result[CLIENT_SECRET_KEY] = user_input[CLIENT_SECRET_KEY]
    if SCAN_INTERVAL_KEY not in user_input:
        errors[SCAN_INTERVAL_KEY] = "invalid_scan_interval"
    else:
        scan_interval: int = DEFAULT_SCAN_INTERVAL
        interval: int = int(user_input[SCAN_INTERVAL_KEY])
        if 0 < interval <= 600:
            scan_interval = interval
        fields[vol.Optional(SCAN_INTERVAL_KEY, default=scan_interval)] = fields[vol.Optional(SCAN_INTERVAL_KEY)]
        result[SCAN_INTERVAL_KEY] = scan_interval
    if PEAK_HOUR_COST_KEY not in user_input:
        errors[PEAK_HOUR_COST_KEY] = "invalid_peak_hour_cost"
    else:
        peak_hour_cost: float = DEFAULT_PEAK_HOUR_COST
        coast: float = float(user_input[PEAK_HOUR_COST_KEY])
        if coast < 0:
            peak_hour_cost = coast
        fields[vol.Optional(PEAK_HOUR_COST_KEY, default=peak_hour_cost)] = fields[vol.Optional(PEAK_HOUR_COST_KEY)]
        result[PEAK_HOUR_COST_KEY] = peak_hour_cost
    if REDIRECT_URI_KEY not in user_input:
        errors[REDIRECT_URI_KEY] = "invalid_redirect_url"
    else:
        redirect_url: str = DEFAULT_REDIRECT_URI
        url = user_input[REDIRECT_URI_KEY]
        if re.match('^(http|https):.*$', url):  # Note that validators.url does not validate URL with localhost or some special characters
            redirect_url = url
        fields[vol.Optional(REDIRECT_URI_KEY, default=redirect_url)] = fields[vol.Optional(REDIRECT_URI_KEY)]
        result[REDIRECT_URI_KEY] = redirect_url
    return result


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Handle the configuration
    """
    VERSION = 1
    MINOR_VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @staticmethod
    def initialize_fields() -> OrderedDict:
        """
        Initialize the fields
        :return: the fields
        """
        result: OrderedDict = OrderedDict()
        result[vol.Required(PDL_KEY, default=DEFAULT_PDL)] = vol.All(str, vol.Length(min=14, max=14))
        result[vol.Required(CLIENT_ID_KEY, default=DEFAULT_CLIENT_ID)] = vol.All(str, vol.Length(min=5))
        result[vol.Required(CLIENT_SECRET_KEY, default=DEFAULT_CLIENT_SECRET)] = vol.All(str, vol.Length(min=5))
        result[vol.Optional(REDIRECT_URI_KEY, default=DEFAULT_REDIRECT_URI)] = vol.All(str, vol.Length(min=5))
        result[vol.Optional(PEAK_HOUR_COST_KEY, default=DEFAULT_PEAK_HOUR_COST)] = vol.All(vol.Coerce(float), vol.Range(min=0))
        result[vol.Optional(SCAN_INTERVAL_KEY, default=DEFAULT_SCAN_INTERVAL)] = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL))
        return result

    def __init__(self):
        """
        The constructor
        """
        self._logger = logging.getLogger(__class__.__name__)
        for handler in LOGGER.handlers:
            self._logger.addHandler(handler)
            self._logger.setLevel(LOGGER.level)
        self._logger.debug("Building a %s", __class__.__name__)
        self._fields: OrderedDict = ConfigFlow.initialize_fields()

    async def async_step_user(self, user_input=None):
        """
        Handle the initial step
        """
        self._logger.debug("Configuring user step...")
        errors = {}
        if user_input is not None:
            # noinspection PyBroadException
            try:
                info: dict[str, Any] = await async_validate_input(self._fields, user_input, errors)
                if len(errors) == 0:
                    access: bool = await async_validate_api_access(self.hass, info[PDL_KEY], info[CLIENT_ID_KEY], info[CLIENT_SECRET_KEY], info[REDIRECT_URI_KEY])
                    if not access:
                        errors["base"] = "cannot_connect"
                    if len(errors) == 0:
                        await self.async_set_unique_id(DOMAIN + '_' + info[PDL_KEY])
                        return self.async_create_entry(title='Enedis data-connect API', data=info)
            except Exception:  # pylint: disable=broad-except
                self._logger.exception("Unexpected exception")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="user", data_schema=vol.Schema(self._fields), errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):  # pylint: disable=unsupported-binary-operation
        """
        Add reconfigure step to allow to reconfigure a config entry
        """
        self._logger.debug("Reconfiguring user step...")
        errors = {}
        if user_input is not None:
            # noinspection PyBroadException
            try:
                info: dict[str, Any] = await async_validate_input(self._fields, user_input, errors)
                if len(errors) == 0:
                    access: bool = await async_validate_api_access(self.hass, info[PDL_KEY], info[CLIENT_ID_KEY], info[CLIENT_SECRET_KEY], info[REDIRECT_URI_KEY])
                    if not access:
                        errors["base"] = "cannot_connect"
                    if len(errors) == 0:
                        return self.async_create_entry(title='Enedis data-connect API', data=info, options=info)
            except Exception:  # pylint: disable=broad-except
                self._logger.exception("Unexpected exception")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="reconfigure", data_schema=vol.Schema(self._fields), errors=errors)
