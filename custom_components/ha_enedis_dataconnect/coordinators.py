#!/usr/bin/python3
# -*- coding: utf-8-
"""
Defines all the coordinators used by the component
"""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.ha_enedis_dataconnect.constants import DEFAULT_SCAN_INTERVAL, SCAN_INTERVAL_KEY
from custom_components.ha_enedis_dataconnect.enedis_client import EnedisClient

_LOGGER = logging.getLogger(__name__)


class EnedisDataUpdateCoordinator(DataUpdateCoordinator):
    """
    The data update coordinator
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: EnedisClient):
        """
        Constructor
        :param hass: the Home Assistant instance
        :param entry: the configuration entry
        :param client: the client
        """
        _LOGGER.debug("Building a %s", __class__.__name__)
        self._hass = hass
        self._config_entry = entry
        self._client = client
        scan_interval: int = DEFAULT_SCAN_INTERVAL
        if SCAN_INTERVAL_KEY in entry.options:
            interval: int = int(entry.options[SCAN_INTERVAL_KEY])
            if 0 < interval <= 600:
                scan_interval = interval
        super().__init__(hass, _LOGGER, name=f"Enedis information for {entry.title}", update_method=self.async_update_enedis_data, update_interval=timedelta(scan_interval))

    def __del__(self):
        """
        Destructor
        """
        if self._client:
            self._client.close()

    def get_client(self) -> EnedisClient:
        """
        Returns the client
        :return: the client
        """
        return self._client

    def get_config_entry(self) -> ConfigEntry:
        """
        Returns the configuration entry
        :return: the entry
        """
        return self._config_entry

    def get_hass(self) -> HomeAssistant:
        """
        Returns the Home Assistant instance
        :return: the instance
        """
        return self._hass

    def update_enedis_data(self) -> bool:
        """
        Retrieve the latest data
        """
        _LOGGER.info("Retrieving latest data...")
        self._client.update_data()
        return True

    async def async_update_enedis_data(self, *_):
        """
        Update the data
        """
        # noinspection PyBroadException
        try:
            return await self.hass.async_add_executor_job(self.update_enedis_data)
        except Exception as e:
            raise Exception(e) from e  # pylint: disable=broad-exception-raised
