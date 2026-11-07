"""Show the dashboard in the sidebar.

Home Assistant has no public way to create a dashboard: blueprints cover only
automations, scripts and templates, and lovelace keeps its dashboard collection
private. So this registers a panel the way lovelace does for YAML dashboards, and
serves the config from memory. It is read-only in the UI and nothing is written to
the user's own dashboards. Removing the integration removes it.
"""

from typing import Any

from homeassistant.components import frontend
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.dashboard import LovelaceConfig
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.json import json_bytes, json_fragment

from .const import DASHBOARD_SECTIONS, DOMAIN
from .coordinator import ZmanimConfigEntry
from .dashboard_config import ALERT_ENTITY, DEFAULT_IDS, TITLE, build

URL_PATH = "shabbat-zmanim"
ICON = "mdi:star-david"


class GeneratedDashboard(LovelaceConfig):
    """A read-only dashboard held in memory."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, URL_PATH, None)
        self._generated = config

    @property
    def mode(self) -> str:
        """Report YAML mode, which is what makes the frontend read-only."""
        return "yaml"

    async def async_get_info(self) -> dict[str, Any]:
        """Return basic information."""
        return {"mode": self.mode, "views": len(self._generated["views"])}

    async def async_load(self, force: bool) -> dict[str, Any]:
        """Return the config."""
        return self._generated

    async def async_json(self, force: bool) -> json_fragment:
        """Return the config as JSON."""
        return json_fragment(json_bytes(self._generated).decode())


def _config(hass: HomeAssistant, entry: ZmanimConfigEntry) -> dict[str, Any]:
    """Build the config from this install's real entity IDs."""
    registry = er.async_get(hass)
    ids = {}
    for key, default in DEFAULT_IDS.items():
        domain = default.split(".")[0]
        unique_id = f"{entry.entry_id}-{key}"
        ids[key] = registry.async_get_entity_id(domain, DOMAIN, unique_id) or default
    weather = sorted(
        item.entity_id
        for item in registry.entities.values()
        if item.domain == "weather" and not item.disabled
    )
    return build(
        ids,
        {key for key in DASHBOARD_SECTIONS if entry.options.get(key, False)},
        hass.config.language,
        weather[0] if weather else None,
        ALERT_ENTITY if ALERT_ENTITY in registry.entities else None,
    )


@callback
def async_add_dashboard(
    hass: HomeAssistant, entry: ZmanimConfigEntry
) -> CALLBACK_TYPE:
    """Add the dashboard, and return how to remove it."""
    config = _config(hass, entry)
    hass.data[LOVELACE_DATA].dashboards[URL_PATH] = GeneratedDashboard(hass, config)
    frontend.async_register_built_in_panel(
        hass,
        "lovelace",
        frontend_url_path=URL_PATH,
        sidebar_title=TITLE.get(hass.config.language, TITLE["en"]),
        sidebar_icon=ICON,
        config={"mode": "yaml"},
    )

    @callback
    def remove() -> None:
        frontend.async_remove_panel(hass, URL_PATH)
        hass.data[LOVELACE_DATA].dashboards.pop(URL_PATH, None)

    return remove
