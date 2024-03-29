#!/usr/bin/python3
# -*- coding: utf-8-
"""
The sensor
"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import COORDINATOR_KEY, DOMAIN, SENSOR_TYPES, SensorTypeEnum, EnedisHistoryDetailsTypeEnum, EnedisDetailsPeriodEnum
from .coordinators import EnedisDataUpdateCoordinator, EnedisSensorCoordinatorEntity, EnedisConsumedHistoryCoordinatorEntity, EnedisConsumedDailyCostCoordinatorEntity, EnedisConsumedEnergyCoordinatorEntity, EnedisConsumedEnergyDetailsCoordinatorEntity, EnedisConsumedEnergyCostDetailsCoordinatorEntity

ICON = "mdi:currency-euro"
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):  # pylint: disable=missing-type-doc
    """
    Configure the devices associated to the component
    :param hass: the home assistant instance
    :param entry: the configuration entry
    :param async_add_entities: the function used to add devices
    """
    _LOGGER.debug("Setting the entry of the sensor...")
    coordinator: EnedisDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR_KEY]
    entities = []
    for key, value in SENSOR_TYPES.items():
        if key == SensorTypeEnum.MAIN_SENSOR_TYPE:
            entities.append(EnedisSensorCoordinatorEntity(value, coordinator))
        elif key == SensorTypeEnum.CONSUMED_HISTORY_SENSOR_TYPE:
            entities.append(EnedisConsumedHistoryCoordinatorEntity(value, coordinator, details_type=EnedisHistoryDetailsTypeEnum.ALL))
        elif key == SensorTypeEnum.CONSUMED_HISTORY_PEAK_HOURS_SENSOR_TYPE:
            entities.append(EnedisConsumedHistoryCoordinatorEntity(value, coordinator, details_type=EnedisHistoryDetailsTypeEnum.PEAK_HOURS))
        elif key == SensorTypeEnum.CONSUMED_YESTERDAY_COST_SENSOR_TYPE:
            entities.append(EnedisConsumedDailyCostCoordinatorEntity(value, coordinator, 1))
        elif key == SensorTypeEnum.CONSUMED_ENERGY_SENSOR_TYPE:
            entities.append(EnedisConsumedEnergyCoordinatorEntity(value, coordinator))
        elif key == SensorTypeEnum.CONSUMED_ENERGY_DETAILS_HOURS_SENSOR_TYPE:
            entities.append(EnedisConsumedEnergyDetailsCoordinatorEntity(value, coordinator, details_type=EnedisDetailsPeriodEnum.HOURS))
        elif key == SensorTypeEnum.CONSUMED_ENERGY_DETAILS_HOURS_COST_SENSOR_TYPE:
            entities.append(EnedisConsumedEnergyCostDetailsCoordinatorEntity(value, coordinator, details_type=EnedisDetailsPeriodEnum.HOURS))
    async_add_entities(
        entities,
        False,
    )
