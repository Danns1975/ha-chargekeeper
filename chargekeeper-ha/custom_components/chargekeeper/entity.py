"""Entité de base ChargeKeeper."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChargeKeeperCoordinator


class ChargeKeeperEntity(CoordinatorEntity[ChargeKeeperCoordinator]):
    """Entité rattachée à une borne (et éventuellement à un connecteur)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ChargeKeeperCoordinator,
        station_id: str,
        connector_id: int | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._station_id = station_id
        self._connector_id = connector_id

        station = self.station
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station_id)},
            name=station.get("chargerIdAlias") or station_id,
            manufacturer=station.get("chargePointVendor"),
            model=station.get("chargePointModel"),
            serial_number=station.get("chargeBoxSerialNumber"),
            sw_version=station.get("firmwareVersion"),
        )

    @property
    def station(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._station_id, {})

    @property
    def connector(self) -> dict[str, Any]:
        for connector in self.station.get("connectors") or []:
            if connector and connector.get("connectorId") == self._connector_id:
                return connector
        return {}

    @property
    def available(self) -> bool:
        return super().available and self._station_id in self.coordinator.data
