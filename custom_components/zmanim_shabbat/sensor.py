"""Today's zmanim, and the next candle lighting and havdalah."""

import datetime as dt

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_ZMANIM
from .coordinator import ZmanimConfigEntry
from .entity import DEVICE_SHABBAT, DEVICE_ZMANIM, ZmanimShabbatEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZmanimConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors, and drop any zman no longer selected."""
    selected = entry.options[CONF_ZMANIM]
    keep = {f"{entry.entry_id}-{key}" for key in selected} | {
        f"{entry.entry_id}-{key}"
        for key in ("in_effect", "next_candle_lighting", "next_havdalah")
    }
    registry = er.async_get(hass)
    for item in er.async_entries_for_config_entry(registry, entry.entry_id):
        if item.unique_id not in keep:
            registry.async_remove(item.entity_id)

    async_add_entities(
        [
            *(ZmanSensor(entry, DEVICE_ZMANIM, key) for key in selected),
            NextCandleLightingSensor(entry, DEVICE_SHABBAT, "next_candle_lighting"),
            NextHavdalahSensor(entry, DEVICE_SHABBAT, "next_havdalah"),
        ]
    )


class TimeSensor(ZmanimShabbatEntity, SensorEntity):
    """A sensor whose value is a moment in time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP


class ZmanSensor(TimeSensor):
    """One of today's zmanim."""

    @property
    def native_value(self) -> dt.datetime:
        """Return today's time."""
        return self.coordinator.data.zmanim[self._attr_translation_key]


class NextCandleLightingSensor(TimeSensor):
    """The next candle lighting still to come."""

    @property
    def native_value(self) -> dt.datetime:
        """Return the time."""
        return self.coordinator.data.next_candle_lighting


class NextHavdalahSensor(TimeSensor):
    """The next havdalah still to come."""

    @property
    def native_value(self) -> dt.datetime:
        """Return the time."""
        return self.coordinator.data.next_havdalah
