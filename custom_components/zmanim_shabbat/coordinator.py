"""Recalculate at midnight, candle lighting and havdalah, and at no other time."""

import datetime as dt
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .calc import Settings, Snapshot, snapshot
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type ZmanimConfigEntry = ConfigEntry[ZmanimCoordinator]


class ZmanimCoordinator(DataUpdateCoordinator[Snapshot]):
    """Hold the current snapshot and schedule the next one."""

    def __init__(
        self, hass: HomeAssistant, entry: ZmanimConfigEntry, settings: Settings
    ) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN)
        self.settings = settings
        self._unsub: CALLBACK_TYPE | None = None

    async def _async_update_data(self) -> Snapshot:
        now = dt_util.now()
        data = snapshot(self.settings, now)
        midnight = dt_util.start_of_local_day(now.date() + dt.timedelta(days=1))
        self.async_stop()
        self._unsub = async_track_point_in_time(
            self.hass,
            self._async_tick,
            min(data.next_candle_lighting, data.next_havdalah, midnight),
        )
        return data

    async def _async_tick(self, _now: dt.datetime) -> None:
        self._unsub = None
        await self.async_refresh()

    @callback
    def async_stop(self) -> None:
        """Cancel the pending recalculation."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
