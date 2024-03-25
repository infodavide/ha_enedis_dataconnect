#!/usr/bin/python3
# -*- coding: utf-8-
"""
The sensor
"""
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities): # pylint: disable=missing-type-doc
    """
    Configure the devices associated to the component
    :param hass:  the home assistant instance
    :param config_entry:  the configuration entry
    :param async_add_entities: the function used to add devices
    """
    _LOGGER.debug("Setting the entry of the sensor...")
