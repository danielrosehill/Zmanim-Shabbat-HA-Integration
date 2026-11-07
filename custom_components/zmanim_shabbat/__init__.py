"""Zmanim and Shabbat: a small Home Assistant integration built on hdate."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .calc import Settings
from .const import (
    CONF_CANDLE_LIGHTING_MINUTES,
    CONF_DASHBOARD,
    CONF_DIASPORA,
    CONF_HAVDALAH_MINUTES,
)
from .coordinator import ZmanimConfigEntry, ZmanimCoordinator
from .panel import async_add_dashboard

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ZmanimConfigEntry) -> bool:
    """Set up from a config entry."""
    settings = Settings(
        latitude=hass.config.latitude,
        longitude=hass.config.longitude,
        elevation=hass.config.elevation,
        timezone=dt_util.get_default_time_zone(),
        diaspora=entry.options[CONF_DIASPORA],
        candle_lighting_minutes=int(entry.options[CONF_CANDLE_LIGHTING_MINUTES]),
        havdalah_minutes=int(entry.options[CONF_HAVDALAH_MINUTES]),
    )
    coordinator = ZmanimCoordinator(hass, entry, settings)
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(coordinator.async_stop)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # v1.1 entries don't have this option until Configure is saved.
    if entry.options.get(CONF_DASHBOARD, False):
        entry.async_on_unload(await async_add_dashboard(hass, entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ZmanimConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
