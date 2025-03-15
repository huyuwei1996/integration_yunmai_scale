"""Sensor implementation for Yunmai Scale integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from bluetooth_data_tools import short_address
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ICON_BMI,
    ICON_BONE,
    ICON_FAT,
    ICON_LEAN,
    ICON_MUSCLE,
    ICON_SKELETAL,
    ICON_STATUS,
    ICON_VISCERAL,
    ICON_WATER,
    ICON_WEIGHT,
    SENSOR_BMI,
    SENSOR_BODY_FAT,
    SENSOR_BONE_MASS,
    SENSOR_LEAN_BODY_MASS,
    SENSOR_MUSCLE_MASS,
    SENSOR_SKELETAL_MUSCLE,
    SENSOR_STATUS,
    SENSOR_VISCERAL_FAT,
    SENSOR_WATER,
    SENSOR_WEIGHT,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class YunmaiSensorEntityDescription(SensorEntityDescription):
    """Describes Yunmai sensor entity."""

    value_fn: Callable[[dict], StateType] = None


SENSORS: tuple[YunmaiSensorEntityDescription, ...] = (
    YunmaiSensorEntityDescription(
        key=SENSOR_WEIGHT,
        name="Weight",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_WEIGHT,
        value_fn=lambda data: data.get("weight"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_BMI,
        name="BMI",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_BMI,
        value_fn=lambda data: data.get("bmi"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_BODY_FAT,
        name="Body Fat",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_FAT,
        value_fn=lambda data: data.get("body_fat"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_MUSCLE_MASS,
        name="Muscle Mass",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_MUSCLE,
        value_fn=lambda data: data.get("muscle_mass"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_WATER,
        name="Water Percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_WATER,
        value_fn=lambda data: data.get("water_percentage"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_BONE_MASS,
        name="Bone Mass",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_BONE,
        value_fn=lambda data: data.get("bone_mass"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_SKELETAL_MUSCLE,
        name="Skeletal Muscle",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_SKELETAL,
        value_fn=lambda data: data.get("skeletal_muscle"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_LEAN_BODY_MASS,
        name="Lean Body Mass",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_LEAN,
        value_fn=lambda data: data.get("lean_body_mass"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_VISCERAL_FAT,
        name="Visceral Fat",
        state_class=SensorStateClass.MEASUREMENT,
        icon=ICON_VISCERAL,
        value_fn=lambda data: data.get("visceral_fat"),
    ),
    YunmaiSensorEntityDescription(
        key=SENSOR_STATUS,
        name="Scale Status",
        icon=ICON_STATUS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("status", "idle"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yunmai sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [YunmaiSensor(coordinator, description) for description in SENSORS]

    async_add_entities(entities)


class YunmaiSensor(CoordinatorEntity, SensorEntity):
    """Yunmai Scale sensor."""

    entity_description: YunmaiSensorEntityDescription
    _previous_value: StateType = None
    _attr_has_entity_name = True

    def __init__(self, coordinator, description: YunmaiSensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_device_info = coordinator.device_info
        self._attr_unique_id = (
            f"{short_address(coordinator.mac_address)}_{description.key}"
        )
        _LOGGER.info("Created sensor %s %s", description.key, self._attr_unique_id)
        # if ":" not in coordinator.mac_address:
        #     # MacOS Bluetooth addresses are not mac addresses
        #     return
        # self._attr_device_info[ATTR_CONNECTIONS].add(
        #     (dr.CONNECTION_NETWORK_MAC, coordinator.mac_address)
        # )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data and self.entity_description.key != SENSOR_STATUS:
            return self._previous_value

        value = self.entity_description.value_fn(self.coordinator.data)
        if value is not None:
            self._previous_value = value
        elif self._previous_value is not None:
            return self._previous_value

        return value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # For status sensor, always return True
        if self.entity_description.key == SENSOR_STATUS:
            return True

        # For other sensors, check if data is available
        return super().available and self.coordinator.data
