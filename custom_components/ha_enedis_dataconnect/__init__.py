#!/usr/bin/python3
# -*- coding: utf-8-
"""
The initialisation of the custom component
"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .constants import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up the custom component from a config entry
    :param hass: the home assistant instance
    :param entry: the configuration entry
    :return: true if the entry was successfully configured
    """
    _LOGGER.debug("Setting up the entry...")
    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub.Hub(hass, entry.data["host"])
    hass.states.async_set('hello_world_async.Hello_World', 'Works!')
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
