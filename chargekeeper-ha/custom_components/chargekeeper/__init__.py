"""Intégration ChargeKeeper pour Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ChargeKeeperClient
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_TENANT
from .coordinator import ChargeKeeperCoordinator

PLATFORMS = ["sensor", "binary_sensor"]

type ChargeKeeperConfigEntry = ConfigEntry[ChargeKeeperCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ChargeKeeperConfigEntry) -> bool:
    """Initialise l'intégration à partir d'une entrée de configuration."""
    client = ChargeKeeperClient(
        async_get_clientsession(hass),
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_TENANT],
    )
    coordinator = ChargeKeeperCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ChargeKeeperConfigEntry) -> bool:
    """Décharge l'entrée."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: ChargeKeeperConfigEntry) -> None:
    """Recharge l'entrée quand les options changent."""
    await hass.config_entries.async_reload(entry.entry_id)
