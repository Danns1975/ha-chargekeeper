"""Coordinateur de mise à jour ChargeKeeper."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChargeKeeperAuthError, ChargeKeeperClient, ChargeKeeperError
from .const import CONF_SCAN_INTERVAL, CONF_STATION_ID, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ChargeKeeperCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Récupère périodiquement l'état des bornes (clé = identifiant de borne)."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: ChargeKeeperClient
    ) -> None:
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client
        self._station_id = (
            entry.options.get(CONF_STATION_ID, entry.data.get(CONF_STATION_ID)) or None
        )

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            stations = await self.client.async_get_stations(self._station_id)
        except ChargeKeeperAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ChargeKeeperError as err:
            raise UpdateFailed(str(err)) from err
        return {s["id"]: s for s in stations if s.get("id")}
