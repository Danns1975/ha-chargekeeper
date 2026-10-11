"""Capteurs ChargeKeeper."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import ChargeKeeperConfigEntry
from .const import CONNECTOR_STATUS_MAP, CONNECTOR_STATUSES
from .entity import ChargeKeeperEntity


@dataclass(frozen=True, kw_only=True)
class ChargeKeeperSensorDescription(SensorEntityDescription):
    """Description d'un capteur (connecteur ou borne)."""

    value_fn: Callable[[dict[str, Any]], Any]


CONNECTOR_SENSORS: tuple[ChargeKeeperSensorDescription, ...] = (
    ChargeKeeperSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=CONNECTOR_STATUSES,
        value_fn=lambda c: CONNECTOR_STATUS_MAP.get(c.get("status")),
    ),
    ChargeKeeperSensorDescription(
        key="power",
        translation_key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.get("currentInstantWatts"),
    ),
    ChargeKeeperSensorDescription(
        key="session_energy",
        translation_key="session_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.get("currentTotalConsumptionWh"),
    ),
    ChargeKeeperSensorDescription(
        key="state_of_charge",
        translation_key="state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        # 0 = information non remontée par la voiture
        value_fn=lambda c: c.get("currentStateOfCharge") or None,
    ),
    ChargeKeeperSensorDescription(
        key="inactivity",
        translation_key="inactivity",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.get("currentTotalInactivitySecs"),
    ),
    ChargeKeeperSensorDescription(
        key="error_code",
        translation_key="error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: c.get("errorCode"),
    ),
    ChargeKeeperSensorDescription(
        key="transaction_id",
        translation_key="transaction_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda c: c.get("currentTransactionID") or None,
    ),
)

STATION_SENSORS: tuple[ChargeKeeperSensorDescription, ...] = (
    ChargeKeeperSensorDescription(
        key="last_seen",
        translation_key="last_seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: dt_util.parse_datetime(s["lastSeen"]) if s.get("lastSeen") else None,
    ),
    ChargeKeeperSensorDescription(
        key="firmware",
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.get("firmwareVersion"),
    ),
    ChargeKeeperSensorDescription(
        key="ocpp_version",
        translation_key="ocpp_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.get("ocppVersion"),
    ),
    ChargeKeeperSensorDescription(
        key="maximum_power",
        translation_key="maximum_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.get("maximumPower"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChargeKeeperConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crée les capteurs pour chaque borne et chaque connecteur."""
    coordinator = entry.runtime_data
    entities: list[ChargeKeeperSensor] = []

    for station_id, station in coordinator.data.items():
        for description in STATION_SENSORS:
            entities.append(ChargeKeeperSensor(coordinator, description, station_id))
        for connector in station.get("connectors") or []:
            connector_id = connector.get("connectorId")
            if connector_id is None:
                continue
            for description in CONNECTOR_SENSORS:
                entities.append(
                    ChargeKeeperSensor(coordinator, description, station_id, connector_id)
                )

    async_add_entities(entities)


class ChargeKeeperSensor(ChargeKeeperEntity, SensorEntity):
    """Capteur ChargeKeeper."""

    entity_description: ChargeKeeperSensorDescription

    def __init__(
        self,
        coordinator,
        description: ChargeKeeperSensorDescription,
        station_id: str,
        connector_id: int | None = None,
    ) -> None:
        super().__init__(coordinator, station_id, connector_id)
        self.entity_description = description
        suffix = f"_{connector_id}" if connector_id is not None else ""
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{station_id}{suffix}_{description.key}"
        )
        if connector_id is not None:
            self._attr_translation_placeholders = {"connector": str(connector_id)}
            self._attr_translation_key = f"connector_{description.key}"
        else:
            self._attr_translation_key = description.key

    @property
    def native_value(self) -> Any:
        source = self.connector if self._connector_id is not None else self.station
        return self.entity_description.value_fn(source)
