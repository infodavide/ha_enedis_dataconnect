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
import validators
import voluptuous as vol
from .constants import DOMAIN, PDL_KEY, CLIENT_ID_KEY, CLIENT_SECRET_KEY, REDIRECT_URI_KEY, DEFAULT_REDIRECT_URI, SCAN_INTERVAL_KEY, DEFAULT_SCAN_INTERVAL, MIN_SCAN_INTERVAL, MAX_SCAN_INTERVAL
from .enedis_client import InvalidPdl, InvalidClientId, InvalidClientSecret, InvalidScanInterval, EnedisClient, InvalidAccess

_LOGGER = logging.getLogger(__name__)
fields: OrderedDict = OrderedDict()
fields[vol.Required(CLIENT_ID_KEY)] = vol.All(str, vol.Length(min=5))
fields[vol.Required(CLIENT_SECRET_KEY)] = vol.All(str, vol.Length(min=5))
fields[vol.Required(PDL_KEY)] = vol.All(str, vol.Length(min=14, max=14))
fields[vol.Optional(REDIRECT_URI_KEY, default=DEFAULT_REDIRECT_URI)] = vol.All(str, vol.Length(min=5))
fields[vol.Optional(SCAN_INTERVAL_KEY, default=DEFAULT_SCAN_INTERVAL)] = vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL))
DATA_SCHEMA = vol.Schema(fields)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """
    :param hass: the home assistant instance
    :param data: the input data
    :return: the configuration data
    """
    _LOGGER.debug("Validating the input...")
    if PDL_KEY not in data or not re.match("\\d{14}", data[PDL_KEY]):
        raise InvalidPdl
    if CLIENT_ID_KEY not in data or len(data[CLIENT_ID_KEY]) < 1:
        raise InvalidClientId
    if CLIENT_SECRET_KEY not in data or len(data[CLIENT_SECRET_KEY]) < 1:
        raise InvalidClientSecret
    if SCAN_INTERVAL_KEY not in data or not re.match("\\d*", data[SCAN_INTERVAL_KEY]):
        raise InvalidScanInterval
    scan_interval: int = DEFAULT_SCAN_INTERVAL
    if SCAN_INTERVAL_KEY in data:
        interval: int = int(data[SCAN_INTERVAL_KEY])
        if 0 < interval <= 600:
            scan_interval = interval
    redirect_url: str = DEFAULT_REDIRECT_URI
    if REDIRECT_URI_KEY in data:
        url = data[REDIRECT_URI_KEY]
        if validators.url(url):
            redirect_url = url

    async def validate_access(pdl: str, client_id: str, client_secret: str, redirect_uri: str):
        _LOGGER.debug("Validating the access...")
        client: EnedisClient = EnedisClient(pdl, client_id, client_secret, redirect_uri)
        client.connect()
        client.close()

    await hass.async_add_executor_job(validate_access, data[PDL_KEY], data[CLIENT_ID_KEY], data[CLIENT_SECRET_KEY], redirect_url)
    return {PDL_KEY: data[PDL_KEY], CLIENT_ID_KEY: data[CLIENT_ID_KEY], CLIENT_SECRET_KEY: data[CLIENT_SECRET_KEY], REDIRECT_URI_KEY: redirect_url, SCAN_INTERVAL_KEY: scan_interval}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Handle the configuration
    """

    VERSION = 1
    MINOR_VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """
        Handle the initial step
        """
        _LOGGER.debug("Configuring user step...")
        errors = {}
        if user_input is not None:
            # noinspection PyBroadException
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title='Enedis sensor', data=info)
            except InvalidAccess:
                errors["base"] = "cannot_connect"
            except InvalidPdl:
                errors[PDL_KEY] = "invalid_pdl"
            except InvalidClientId:
                errors[CLIENT_ID_KEY] = "invalid_client_id"
            except InvalidClientSecret:
                errors[CLIENT_SECRET_KEY] = "invalid_client_secret"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
