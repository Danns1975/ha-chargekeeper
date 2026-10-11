"""Constantes de l'intégration ChargeKeeper."""

DOMAIN = "chargekeeper"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_TENANT = "tenant"
CONF_STATION_ID = "station_id"

DEFAULT_BASE_URL = "https://rest.service-evse.com/v1"

# Chemin de connexion (relatif à DEFAULT_BASE_URL) : POST /v1/auth/signin
LOGIN_PATHS = ("/auth/signin",)

STATIONS_PATH = "/api/charging-stations"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30  # secondes
MIN_SCAN_INTERVAL = 10

# Statut OCPP renvoyé par l'API -> clé d'état (snake_case, traduisible)
CONNECTOR_STATUS_MAP = {
    "Available": "available",
    "Preparing": "preparing",
    "Charging": "charging",
    "Occupied": "occupied",
    "SuspendedEVSE": "suspended_evse",
    "SuspendedEV": "suspended_ev",
    "Finishing": "finishing",
    "Reserved": "reserved",
    "Unavailable": "unavailable",
    "Faulted": "faulted",
}
CONNECTOR_STATUSES = list(CONNECTOR_STATUS_MAP.values())
