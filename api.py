"""Client minimal pour l'API REST ChargeKeeper."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
import uuid

import aiohttp

from .const import DEFAULT_BASE_URL, LOGIN_PATHS, STATIONS_PATH

_LOGGER = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=20)
_PAGE_SIZE = 100


class ChargeKeeperError(Exception):
    """Erreur générique (réseau, réponse inattendue)."""


class ChargeKeeperAuthError(ChargeKeeperError):
    """Identifiants / tenant invalides."""


class ChargeKeeperClient:
    """Client asynchrone ChargeKeeper."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        tenant: str,
        base_url: str = DEFAULT_BASE_URL,
        device_id: str | None = None,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._tenant = tenant
        # Identifiant d'appareil stable (même valeur à chaque démarrage)
        self._device_id = device_id or str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"chargekeeper-ha:{tenant}:{email.lower()}")
        )
        self._base_url = base_url.rstrip("/")
        self._token: str | None = None

    async def async_login(self) -> None:
        """Obtient un jeton d'accès."""
        payload = {
            "email": self._email,
            "password": self._password,
            "tenant": self._tenant,
            "acceptEula": True,
            "deviceid": self._device_id,
        }
        last_error: Exception | None = None

        for path in LOGIN_PATHS:
            url = f"{self._base_url}{path}"
            try:
                async with self._session.post(
                    url, json=payload, timeout=_TIMEOUT
                ) as resp:
                    if resp.status in (404, 405):
                        last_error = ChargeKeeperError(
                            f"Chemin de connexion introuvable: {path}"
                        )
                        continue
                    if resp.status in (400, 401, 403, 422):
                        raise ChargeKeeperAuthError(
                            f"Connexion refusée (HTTP {resp.status})"
                        )
                    if resp.status >= 400:
                        raise ChargeKeeperError(f"HTTP {resp.status} sur {path}")
                    data = await resp.json(content_type=None)
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise ChargeKeeperError(f"Connexion impossible: {err}") from err

            token = None
            if isinstance(data, dict):
                token = data.get("accessToken") or data.get("token")
            if not token:
                raise ChargeKeeperAuthError("Aucun jeton dans la réponse de connexion")
            self._token = token
            return

        raise last_error or ChargeKeeperError("Connexion impossible")

    async def _request(
        self, path: str, params: dict[str, Any] | None = None, retry: bool = True
    ) -> Any:
        if self._token is None:
            await self.async_login()

        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.get(
                url, params=params, headers=headers, timeout=_TIMEOUT
            ) as resp:
                if resp.status == 401 and retry:
                    self._token = None
                    await self.async_login()
                    return await self._request(path, params, retry=False)
                if resp.status in (401, 403):
                    raise ChargeKeeperAuthError(f"Accès refusé (HTTP {resp.status})")
                if resp.status >= 400:
                    raise ChargeKeeperError(f"HTTP {resp.status} sur {path}")
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise ChargeKeeperError(f"Requête impossible: {err}") from err

    async def async_get_stations(
        self, station_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Retourne les bornes du compte (pagination incluse).

        station_id : un ou plusieurs identifiants séparés par des virgules
        (ou « | ») pour ne récupérer que ces bornes ; vide = toutes.
        """
        params: dict[str, Any] = {"Limit": _PAGE_SIZE, "WithSiteArea": "true"}
        if station_id:
            ids = [i.strip() for i in station_id.replace("|", ",").split(",")]
            params["ChargingStationID"] = "|".join(i for i in ids if i)

        stations: list[dict[str, Any]] = []
        skip = 0
        while True:
            data = await self._request(STATIONS_PATH, {**params, "Skip": skip})
            if not isinstance(data, dict):
                raise ChargeKeeperError("Réponse inattendue pour la liste des bornes")
            result = data.get("result") or []
            stations.extend(result)
            skip += _PAGE_SIZE
            if not result or skip >= int(data.get("count", 0)):
                break
        return stations
