#!/usr/bin/python3
# -*- coding: utf-8-
"""
Defines all the coordinators used by the component
"""
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import timedelta, datetime, date
from typing import Any

from homeassistant.components.sensor import SensorStateClass, ATTR_LAST_RESET, SensorDeviceClass, ATTR_STATE_CLASS
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_DEVICE_CLASS, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.util import Throttle

from custom_components.ha_enedis_dataconnect.const import DEFAULT_SCAN_INTERVAL, SCAN_INTERVAL_KEY, EnedisHistoryDetailsTypeEnum, EnedisDetailsPeriodEnum, ENTITY_DELAY_KEY, DOMAIN, ENTITY_UNIT_KEY, VERSION_KEY, VERSION, EnedisSensorTypeEnum, PDL_KEY, EMPTY_STRING, DATE_TIME_FORMAT, LOGGER
from custom_components.ha_enedis_dataconnect.enedis_client import EnedisClient, EnedisApiHelper

_LOGGER = logging.getLogger(__name__)
PDL_ATTR: str = PDL_KEY
LAST_UPDATE_ATTR: str = 'last_update'
COUNTER_TYPE_ATTR: str = 'counter_type'
LAST_CALL_ATTR: str = 'timeLastCall'
UNAVAILABLE_STATE: str = 'unavailable'
MIN_TIME_ATTR: str = 'min_time'
ACTIVATION_DATE_ATTR: str = 'activation_date'
YESTERDAY_ATTR: str = 'yesterday'
YESTERDAY_CONSUMPTION_MAX_POWER_ATTR: str = 'yesterday_consumption_max_power'


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
        self._logger = logging.getLogger(__class__.__name__)
        for handler in LOGGER.handlers:
            self._logger.addHandler(handler)
            self._logger.setLevel(LOGGER.level)
        self._logger.debug("Building a %s", __class__.__name__)
        self._hass = hass
        self._config_entry = entry
        self._client = client
        scan_interval: int = DEFAULT_SCAN_INTERVAL
        if SCAN_INTERVAL_KEY in entry.options:
            interval: int = int(entry.options[SCAN_INTERVAL_KEY])
            if 0 < interval <= 600:
                scan_interval = interval
        super().__init__(hass, _LOGGER, name=f"Enedis information for {entry.title}", update_method=self.async_update_data, update_interval=timedelta(scan_interval))

    def __del__(self):
        """
        Destructor
        """
        if self._client:
            self._hass.async_add_executor_job(self._client.close)

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

    def update_data(self) -> bool:
        """
        Retrieve the latest data
        """
        _LOGGER.info("Retrieving latest data...")
        self._client.update_data()
        return True

    async def async_update_data(self, *_):
        """
        Update the data
        """
        # noinspection PyBroadException
        try:
            return await self.hass.async_add_executor_job(self.update_data)
        except Exception as e:
            raise Exception(e) from e  # pylint: disable=broad-exception-raised

    def setup(self) -> None:
        """
        Configure the coordinator
        """

    async def async_setup(self, *_):
        """
        Configure the coordinator
        """
        # noinspection PyBroadException
        try:
            return await self.hass.async_add_executor_job(self.setup)
        except Exception as e:
            raise Exception(e) from e  # pylint: disable=broad-exception-raised


class AbstractCoordinatorEntity(CoordinatorEntity, RestoreEntity, ABC):  # pylint: disable=too-many-instance-attributes
    """
    The abstract coordinator
    """

    def __init__(self, definition: dict[str, Any], coordinator: EnedisDataUpdateCoordinator):
        """
        The constructor
        :param definition: the sensor definition
        :param coordinator: the parent coordinator
        """
        super().__init__(coordinator)
        self._logger = logging.getLogger(__class__.__name__)
        for handler in LOGGER.handlers:
            self._logger.addHandler(handler)
            self._logger.setLevel(LOGGER.level)
        self._logger.debug("Building a %s", __class__.__name__)
        self._definition: dict[str, Any] = definition
        self._coordinator: EnedisDataUpdateCoordinator = coordinator
        self._api_helper: EnedisApiHelper = EnedisApiHelper(coordinator.get_client())
        self._update_interval: int = definition[ENTITY_DELAY_KEY]
        self._attributes: dict[str, Any] = {}
        # noinspection PyTypeChecker
        self._state: str = None
        self._unit: str = definition[ENTITY_UNIT_KEY]
        # noinspection PyTypeChecker
        self._last_state: str = None
        self._last_attributes: dict[str, str] = {}
        # noinspection PyTypeChecker
        self._last_update_date: str = None
        # noinspection PyTypeChecker
        self._last_call_date: str = None
        # noinspection PyTypeChecker
        self._last_reset_date: str = None
        # noinspection PyTypeChecker
        self._date: datetime = None
        # noinspection PyTypeChecker
        self._activation_date: str = None
        # noinspection PyTypeChecker
        self._start_date: str = None
        # noinspection PyTypeChecker
        self._end_date: str = None
        self.update = Throttle(timedelta(seconds=self._update_interval))(self._update)
        self._logger.info("Refresh interval: %s in seconds", self._update_interval)
        self._version: str = VERSION
        self._success: bool = True
        self._calls_count: int = 0
        # noinspection PyTypeChecker
        self._data: str = None

        self._value = 0

    def get_definition(self) -> dict[str, Any]:
        """
        Return the definition
        :return: the definition
        """
        return self._definition

    def get_update_interval(self) -> int:
        """
        Return the update interval in seconds
        :return: the seconds
        """
        return self._update_interval

    @property
    def state(self) -> str:
        """
        Return the state of the sensor
        :return: the state
        """
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """
        Return the unit of measurement of this entity, if any
        :return: the unit
        """
        return self._unit

    @property
    def extra_state_attributes(self):
        """
        Return the state attributes
        """
        return self._attributes

    @property
    def icon(self):
        """
        Icon to use in the frontend
        """
        return "mdi:package-variant-closed"

    def get_pdl(self) -> str:
        """
        Return the PDL identifier
        :return: the identifier
        """
        coordinator: EnedisDataUpdateCoordinator = self._coordinator
        if coordinator:
            client: EnedisClient = coordinator.get_client()
            if client:
                return client.get_pdl()
        # noinspection PyTypeChecker
        return None

    def get_version(self) -> str:
        """
        Return the version
        :return: the version
        """
        return self._version

    async def async_added_to_hass(self) -> None:
        """
        Handle entity which will be added
        """
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._state = state.state
        # noinspection PyBroadException
        try:
            if COUNTER_TYPE_ATTR in state.attributes:
                self._attributes = state.attributes
        except Exception:  # pylint: disable=broad-except
            self._logger.exception("Restart encountered")

        @callback
        def update():
            """
            Update the state
            """
            self._update_state()
            self.async_write_ha_state()

        self.async_on_remove(self.coordinator.async_add_listener(update))
        self._update_state()

    async def _async_update(self) -> None:
        """
        Update state asynchronously
        """
        self._update_state()
        self.async_write_ha_state()

    def _update(self) -> None:
        """
        Update the data
        """
        self._attributes = {
            ATTR_ATTRIBUTION: EMPTY_STRING
        }
        self._state = "unavailable"

    @abstractmethod
    def _update_state(self) -> None:
        """
        Update the state
        """


class EnedisSensorCoordinatorEntity(AbstractCoordinatorEntity):
    """
    The main coordinator
    """

    @property
    def unique_id(self):
        """
        Returns the unique identifier
        :return: the unique identifier
        """
        return f"{DOMAIN}.{self.get_pdl()}"

    @property
    def name(self):
        """
        Returns the name
        :return: the name
        """
        return f"{DOMAIN}.{self.get_pdl()}"

    def _update_state(self) -> None:
        """
        Update the sensors state
        """
        self._logger.debug("Updating state of %s", self.get_pdl())
        self._attributes = {
            ATTR_ATTRIBUTION: EMPTY_STRING
        }
        today: date = date.today()
        now: datetime = datetime.now()
        state: str = UNAVAILABLE_STATE
        attributes: dict[str, Any] = defaultdict(int)
        attributes[VERSION_KEY] = self._version
        attributes[COUNTER_TYPE_ATTR] = EnedisSensorTypeEnum.CONSUMPTION
        attributes[PDL_ATTR] = self.get_pdl()
        # yesterday consummate max power

        # TODO
        attributes[ACTIVATION_DATE_ATTR] = self._activation_date
        attributes[LAST_CALL_ATTR] = self._last_call_date
        attributes[LAST_UPDATE_ATTR] = now.strftime(DATE_TIME_FORMAT)
        self._attributes.update(attributes)
        self._state = state
        self._logger.debug("State is now: %s", self._state)
        self._logger.debug("Attributes are now: %s", self._attributes)


class EnedisConsumedHistoryCoordinatorEntity(AbstractCoordinatorEntity):
    """
    The history coordinator
    """

    def __init__(self, definition: dict[str, Any], parent: EnedisDataUpdateCoordinator, details_type: EnedisHistoryDetailsTypeEnum):
        """
        The constructor
        :param definition: the sensor definition
        :param parent: the parent coordinator
        :param details_type: the type of details
        """
        super().__init__(definition, parent)
        self._details_type: EnedisHistoryDetailsTypeEnum = details_type

    @property
    def unique_id(self):
        """
        Returns the unique identifier
        :return: the unique identifier
        """
        return f"{DOMAIN}.{self.get_pdl()}_history_{self._details_type}".lower()

    @property
    def name(self):
        """
        Returns the name
        :return: the name
        """
        return f"{DOMAIN}.{self.get_pdl()}_history_{self._details_type}".lower()

    def _update_state(self) -> None:
        """
        Update the sensors state
        """
        self._logger.debug("Updating state of %s", self.get_pdl())
        # data from yesterday are not always available
        today: date = date.today()
        now: datetime = datetime.now()
        state: str = UNAVAILABLE_STATE
        attributes: dict[str, Any] = defaultdict(int)
        # TODO
        attributes[LAST_UPDATE_ATTR] = now.strftime(DATE_TIME_FORMAT)
        self._attributes = {
            ATTR_ATTRIBUTION: EMPTY_STRING,
            ATTR_DEVICE_CLASS: SensorDeviceClass.ENERGY,
            ATTR_UNIT_OF_MEASUREMENT: self._unit
        }
        self._attributes.update(attributes)
        self._state = state
        self._logger.debug("State is now: %s", self._state)
        self._logger.debug("Attributes are now: %s", self._attributes)


class EnedisConsumedEnergyDetailsCoordinatorEntity(AbstractCoordinatorEntity):
    """
    The consumption details coordinator
    """

    def __init__(self, definition: dict[str, Any], parent: EnedisDataUpdateCoordinator, details_type: EnedisDetailsPeriodEnum):
        """
        The constructor
        :param definition: the sensor definition
        :param parent: the parent coordinator
        :param details_type: the type of details
        """
        super().__init__(definition, parent)
        self._details_type: EnedisDetailsPeriodEnum = details_type

    @property
    def unique_id(self):
        """
        Returns the unique identifier
        :return: the unique identifier
        """
        return f"{DOMAIN}.{self.get_pdl()}_energy_{self._details_type}".lower()

    @property
    def name(self):
        """
        Returns the name
        :return: the name
        """
        return f"{DOMAIN}.{self.get_pdl()}_energy_{self._details_type}".lower()

    def _update_state(self) -> None:
        """
        Update the sensors state
        """
        self._logger.debug("Updating state of %s", self.get_pdl())
        today: date = date.today()
        now: datetime = datetime.now()
        state: str = UNAVAILABLE_STATE
        attributes: dict[str, Any] = defaultdict(int)
        # TODO
        attributes[LAST_UPDATE_ATTR] = now.strftime(DATE_TIME_FORMAT)
        self._attributes = {
            ATTR_ATTRIBUTION: EMPTY_STRING,
            ATTR_DEVICE_CLASS: SensorDeviceClass.ENERGY,
            ATTR_STATE_CLASS: SensorStateClass.TOTAL,
            ATTR_UNIT_OF_MEASUREMENT: self._unit,
            ATTR_LAST_RESET: self._last_reset_date
        }
        self._attributes.update(attributes)
        self._state = state
        self._logger.debug("State is now: %s", self._state)
        self._logger.debug("Attributes are now: %s", self._attributes)


class EnedisConsumedEnergyCostDetailsCoordinatorEntity(AbstractCoordinatorEntity):
    """
    The consumption cost details coordinator
    """

    def __init__(self, definition: dict[str, Any], parent: EnedisDataUpdateCoordinator, details_type: EnedisDetailsPeriodEnum):
        """
        The constructor
        :param definition: the sensor definition
        :param parent: the parent coordinator
        :param details_type: the type of details
        """
        super().__init__(definition, parent)
        self._details_type: EnedisDetailsPeriodEnum = details_type

    @property
    def unique_id(self):
        """
        Returns the unique identifier
        :return: the unique identifier
        """
        return f"{DOMAIN}.{self.get_pdl()}_cost_details_{self._details_type}".lower()

    @property
    def name(self):
        """
        Returns the name
        :return: the name
        """
        return f"{DOMAIN}.{self.get_pdl()}_cost_details_{self._details_type}".lower()

    def _update_state(self) -> None:
        """
        Update the sensors state
        """
        self._logger.debug("Updating state of %s", self.get_pdl())
        today: date = date.today()
        now: datetime = datetime.now()
        state: str = UNAVAILABLE_STATE
        attributes: dict[str, Any] = defaultdict(int)
        # TODO
        attributes[LAST_UPDATE_ATTR] = now.strftime(DATE_TIME_FORMAT)
        self._attributes = {
            ATTR_ATTRIBUTION: EMPTY_STRING,
            ATTR_DEVICE_CLASS: SensorDeviceClass.MONETARY,
            ATTR_STATE_CLASS: SensorStateClass.TOTAL,
            ATTR_UNIT_OF_MEASUREMENT: self._unit,
            ATTR_LAST_RESET: self._last_reset_date
        }
        self._attributes.update(attributes)
        self._state = state


class EnedisConsumedDailyCostCoordinatorEntity(AbstractCoordinatorEntity):
    """
    The daily consumption history coordinator
    """

    def __init__(self, definition: dict[str, Any], parent: EnedisDataUpdateCoordinator, days: int):
        """
        The constructor
        :param definition: the sensor definition
        :param parent: the parent coordinator
        :param days: the days from the current date
        """
        super().__init__(definition, parent)
        self._days: int = days

    @property
    def unique_id(self):
        """
        Returns the unique identifier
        :return: the unique identifier
        """
        return f"{DOMAIN}.{self.get_pdl()}_cost_{self._days}"

    @property
    def name(self):
        """
        Returns the name
        :return: the name
        """
        return f"{DOMAIN}.{self.get_pdl()}_cost_{self._days}"

    def _update_state(self) -> None:
        """
        Update the sensors state
        """
        self._logger.debug("Updating state of %s", self.get_pdl())
        today: date = date.today()
        now: datetime = datetime.now()
        state: str = UNAVAILABLE_STATE
        attributes: dict[str, Any] = defaultdict(int)
        # TODO
        attributes[LAST_UPDATE_ATTR] = now.strftime(DATE_TIME_FORMAT)
        self._attributes = {
            ATTR_ATTRIBUTION: EMPTY_STRING,
            ATTR_DEVICE_CLASS: SensorDeviceClass.MONETARY,
            ATTR_UNIT_OF_MEASUREMENT: self._unit
        }
        self._attributes.update(attributes)
        self._state = state


class EnedisConsumedEnergyCoordinatorEntity(AbstractCoordinatorEntity):
    """
    The energy consumption coordinator
    """

    @property
    def unique_id(self):
        """
        Returns the unique identifier
        :return: the unique identifier
        """
        return f"{DOMAIN}.{self.get_pdl()}_{SensorDeviceClass.ENERGY}"

    @property
    def name(self):
        """
        Returns the name
        :return: the name
        """
        return f"{DOMAIN}.{self.get_pdl()}_{SensorDeviceClass.ENERGY}"

    def _update_state(self) -> None:
        """
        Update the sensors state
        """
        self._logger.debug("Updating state of %s", self.get_pdl())
        today: date = date.today()
        now: datetime = datetime.now()
        state: str = UNAVAILABLE_STATE
        attributes: dict[str, Any] = defaultdict(int)
        # TODO
        attributes[LAST_UPDATE_ATTR] = now.strftime(DATE_TIME_FORMAT)
        self._attributes = {
            ATTR_ATTRIBUTION: EMPTY_STRING,
            ATTR_DEVICE_CLASS: SensorDeviceClass.ENERGY,
            ATTR_STATE_CLASS: SensorStateClass.TOTAL,
            ATTR_UNIT_OF_MEASUREMENT: self._unit,
            ATTR_LAST_RESET: self._last_reset_date
        }
        self._attributes.update(attributes)
        self._state = state
