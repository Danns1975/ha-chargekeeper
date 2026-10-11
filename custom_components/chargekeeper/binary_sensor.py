"""Capteurs binaires ChargeKeeper."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ChargeKeeperConfigEntry
from .entity import ChargeKeeperEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChargeKeeperConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée « en ligne » par borne et « en charge » par connecteur."""
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []

    for station_id, station in coordinator.data.items():
        entities.append(ChargeKeeperOnlineBinarySensor(coordinator, station_id))
        for connector in station.get("connectors") or []:
            connector_id = connector.get("connectorId")
            if connector_id is not None:
                entities.append(
                    ChargeKeeperChargingBinarySensor(coordinator, station_id, connector_id)
                )

    async_add_entities(entities)


class ChargeKeeperOnlineBinarySensor(ChargeKeeperEntity, BinarySensorEntity):
    """La borne est-elle connectée à la supervision ?"""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "online"

    def __init__(self, coordinator, station_id: str) -> None:
        super().__init__(coordinator, station_id)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{station_id}_online"

    @property
    def is_on(self) -> bool | None:
        inactive = self.station.get("inactive")
        return None if inactive is None else not inactive


class ChargeKeeperChargingBinarySensor(ChargeKeeperEntity, BinarySensorEntity):
    """Le connecteur est-il en train de charger ?"""

    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _attr_translation_key = "connector_charging"

    def __init__(self, coordinator, station_id: str, connector_id: int) -> None:
        super().__init__(coordinator, station_id, connector_id)
        self._attr_translation_placeholders = {"connector": str(connector_id)}
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{station_id}_{connector_id}_charging"
        )

    @property
    def is_on(self) -> bool | None:
        status = self.connector.get("status")
        return None if status is None else status == "Charging"
