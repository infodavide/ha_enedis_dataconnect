#!/usr/bin/python3
# -*- coding: utf-8-
"""
The initialisation of the custom component
"""
import logging
from datetime import timedelta
from enedis_data_connect.enedis_client import EnedisClient, InvalidClientId, InvalidClientSecret, InvalidPrm, DEFAULT_REDIRECT_URI

try:
    from homeassistant.helpers.typing import ConfigType
except ImportError:
    class ConfigType:  # type: ignore[no-redef]
        """
        For testing
        """
        def __init__(self):
            # nothing to do
            pass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event, CALLBACK_TYPE, CoreState
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CLIENT_ID_KEY, CLIENT_SECRET_KEY, COORDINATOR_KEY, DOMAIN, EVENT_UNLISTENER_KEY, PLATFORMS, REDIRECT_URI_KEY, UPDATE_ENEDIS_EVENT_TYPE, UPDATE_UNLISTENER_KEY, CONSUMPTION_PRM_KEY, PRODUCTION_PRM_KEY, DEFAULT_SCAN_INTERVAL, DATA_HASS_CONFIG
from .coordinators import EnedisDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """
    Handle options update
    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """
    Set up the custom component
    """
    hass.data[DATA_HASS_CONFIG] = config
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:  # pylint: disable=too-complex
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
    # noinspection PyTypeChecker
    consumption_prm: str = None
    if CONSUMPTION_PRM_KEY in entry.options:
        consumption_prm = entry.options[CONSUMPTION_PRM_KEY]
    elif CONSUMPTION_PRM_KEY in entry.data:
        consumption_prm = entry.data[CONSUMPTION_PRM_KEY]
    # noinspection PyTypeChecker
    production_prm: str = None
    if PRODUCTION_PRM_KEY in entry.options:
        production_prm = entry.options[PRODUCTION_PRM_KEY]
    elif PRODUCTION_PRM_KEY in entry.data:
        production_prm = entry.data[PRODUCTION_PRM_KEY]
    if consumption_prm is None and production_prm is None:
        raise InvalidPrm
    if REDIRECT_URI_KEY in entry.options:
        redirect_uri: str = entry.options[REDIRECT_URI_KEY]
    elif REDIRECT_URI_KEY in entry.data:
        redirect_uri: str = entry.data[REDIRECT_URI_KEY]
    else:
        redirect_uri = DEFAULT_REDIRECT_URI
    client: EnedisClient = EnedisClient(consumption_prm, production_prm, client_id, client_secret, redirect_uri)
    coordinator: EnedisDataUpdateCoordinator = EnedisDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_setup()

    async def _async_event_listener(event: Event):
        """
        Listen to events
        :param event: the event
        """
        if not event:
            return
        _LOGGER.info("Event received: %s", event.data)
        if event.event_type == UPDATE_ENEDIS_EVENT_TYPE:
            await coordinator.async_update_data()

    async def _async_scheduled_refresh(*_):
        """
        Activate the data update coordinator
        """
        if coordinator:
            coordinator.update_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
            await coordinator.async_refresh()

    if hass.state == CoreState.running:
        await _async_scheduled_refresh()
        if not coordinator.last_update_success:
            raise ConfigEntryNotReady
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _async_scheduled_refresh)

    async def _async_close(event: Event) -> None:
        """
        Listen to events
        :param event: the event
        """
        if not event:
            return
        if client:
            await client.close()

    _LOGGER.debug("Setting up the listeners...")
    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_close))
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
        if COORDINATOR_KEY in hass.data[DOMAIN][entry.entry_id]:
            coordinator: EnedisDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR_KEY]
            if coordinator:
                client: EnedisClient = coordinator.get_client()
                if client:
                    await client.close()
        hass.data[DOMAIN][entry.entry_id][UPDATE_UNLISTENER_KEY]()
        hass.data[DOMAIN][entry.entry_id][EVENT_UNLISTENER_KEY]()
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return result
