"""Interface de configuration : email, mot de passe, tenant."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ChargeKeeperAuthError, ChargeKeeperClient, ChargeKeeperError
from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_STATION_ID,
    CONF_TENANT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)


def _user_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_EMAIL, default=defaults.get(CONF_EMAIL, "")): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
            ),
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
            vol.Required(CONF_TENANT, default=defaults.get(CONF_TENANT, "")): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_STATION_ID, default=defaults.get(CONF_STATION_ID, "")
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        }
    )


class ChargeKeeperConfigFlow(ConfigFlow, domain=DOMAIN):
    """Assistant de configuration."""

    VERSION = 1

    async def _async_validate(self, data: Mapping[str, Any]) -> str | None:
        """Teste la connexion. Retourne un code d'erreur ou None."""
        client = ChargeKeeperClient(
            async_get_clientsession(self.hass),
            data[CONF_EMAIL],
            data[CONF_PASSWORD],
            data[CONF_TENANT],
        )
        station_id = data.get(CONF_STATION_ID) or None
        try:
            await client.async_login()
            stations = await client.async_get_stations(station_id)
        except ChargeKeeperAuthError:
            return "invalid_auth"
        except ChargeKeeperError:
            return "cannot_connect"
        except Exception:  # noqa: BLE001
            return "unknown"
        if station_id and not stations:
            return "station_not_found"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_EMAIL] = user_input[CONF_EMAIL].strip()
            user_input[CONF_TENANT] = user_input[CONF_TENANT].strip()
            user_input[CONF_STATION_ID] = user_input.get(CONF_STATION_ID, "").strip()
            await self.async_set_unique_id(
                f"{user_input[CONF_TENANT]}_{user_input[CONF_EMAIL]}_"
                f"{user_input[CONF_STATION_ID]}".lower()
            )
            self._abort_if_unique_id_configured()

            error = await self._async_validate(user_input)
            if error is None:
                label = user_input[CONF_STATION_ID] or user_input[CONF_TENANT]
                return self.async_create_entry(
                    title=f"ChargeKeeper ({label})", data=user_input
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            error = await self._async_validate(data)
            if error is None:
                return self.async_update_reload_and_abort(entry, data=data)
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ChargeKeeperOptionsFlow()


class ChargeKeeperOptionsFlow(OptionsFlow):
    """Options : fréquence d'interrogation et borne(s) suivie(s)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self.config_entry
        if user_input is not None:
            user_input[CONF_STATION_ID] = user_input.get(CONF_STATION_ID, "").strip()
            return self.async_create_entry(data=user_input)

        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        station_id = entry.options.get(CONF_STATION_ID, entry.data.get(CONF_STATION_ID, ""))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=interval): vol.All(
                        vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=3600)
                    ),
                    vol.Optional(CONF_STATION_ID, default=station_id): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEXT)
                    ),
                }
            ),
        )
