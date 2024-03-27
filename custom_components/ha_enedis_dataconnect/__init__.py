#!/usr/bin/python3
# -*- coding: utf-8-
"""
The initialisation of the custom component
"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, CALLBACK_TYPE

from .constants import CLIENT_ID_KEY, CLIENT_SECRET_KEY, COORDINATOR_KEY, DOMAIN, EVENT_UNLISTENER_KEY, PLATFORMS, REDIRECT_URI_KEY, UPDATE_ENEDIS_EVENT_TYPE, UPDATE_UNLISTENER_KEY, PDL_KEY, DEFAULT_REDIRECT_URI
from .coordinators import EnedisDataUpdateCoordinator
from .enedis_client import EnedisClient, InvalidClientId, InvalidClientSecret, InvalidPdl

_LOGGER = logging.getLogger(__name__)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up the custom component from a config entry
    :param hass: the home assistant instance
    :param entry: the configuration entry
    :return: true if the entry was successfully configured
    """
    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.debug("Setting up the entry...")
        _LOGGER.debug(entry)
        _LOGGER.debug(entry.data)
        _LOGGER.debug(entry.options)
    hass.data.setdefault(DOMAIN, {})
    if CLIENT_ID_KEY in entry.options:
        client_id: str = entry.options[CLIENT_ID_KEY]
    elif CLIENT_ID_KEY in entry.data:
        client_id: str = entry.data[CLIENT_ID_KEY]
    else:
        raise InvalidClientId
    if CLIENT_SECRET_KEY in entry.options:
        client_secret: str = entry.options[CLIENT_SECRET_KEY]
    elif CLIENT_SECRET_KEY in entry.data:
        client_secret: str = entry.data[CLIENT_SECRET_KEY]
    else:
        raise InvalidClientSecret
    if PDL_KEY in entry.options:
        pdl: str = entry.options[PDL_KEY]
    elif PDL_KEY in entry.data:
        pdl: str = entry.data[PDL_KEY]
    else:
        raise InvalidPdl
    if REDIRECT_URI_KEY in entry.options:
        redirect_uri: str = entry.options[REDIRECT_URI_KEY]
    elif REDIRECT_URI_KEY in entry.data:
        redirect_uri: str = entry.data[REDIRECT_URI_KEY]
    else:
        redirect_uri = DEFAULT_REDIRECT_URI
    client: EnedisClient = EnedisClient(hass, pdl, client_id, client_secret, redirect_uri)
    coordinator: EnedisDataUpdateCoordinator = EnedisDataUpdateCoordinator(hass, entry, client)

    async def _async_event_listener(event: Event):
        _LOGGER.info("Event received: %s", event.data)
        if event.event_type == UPDATE_ENEDIS_EVENT_TYPE:
            await coordinator.async_update_enedis_data()

    _LOGGER.debug("Setting up the listeners...")
    # noinspection SpellCheckingInspection
    update_unlistener: CALLBACK_TYPE = entry.add_update_listener(_async_update_listener)
    # noinspection SpellCheckingInspection
    event_unlistener: CALLBACK_TYPE = hass.bus.async_listen(UPDATE_ENEDIS_EVENT_TYPE, _async_event_listener)
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR_KEY: coordinator,
        UPDATE_UNLISTENER_KEY: update_unlistener,
        EVENT_UNLISTENER_KEY: event_unlistener
    }
    _LOGGER.debug("Setting up the devices...")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Unload a config entry
    :param hass: the home assistant instance
    :param entry: the configuration entry
    :return: true if the entry was successfully removed
    """
    _LOGGER.debug("Unloading up the entry...")
    result: bool = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if result:
        hass.data[DOMAIN].pop(entry.entry_id)
    return result
