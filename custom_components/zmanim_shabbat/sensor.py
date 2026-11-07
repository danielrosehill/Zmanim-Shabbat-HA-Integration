"""Today's zmanim, and the next candle lighting and havdalah."""

import datetime as dt

from hdate.parasha import Parasha

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .calc import format_hebrew_date
from .const import HEBREW_DATE, SHABBAT_ENTITIES, ZMANIM
from .coordinator import ZmanimConfigEntry
from .entity import DEVICE_SHABBAT, DEVICE_ZMANIM, ZmanimShabbatEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZmanimConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors, and drop any left by an older zmanim list."""
    keep = {
        f"{entry.entry_id}-{key}" for key in (*ZMANIM, HEBREW_DATE, *SHABBAT_ENTITIES)
    }
    registry = er.async_get(hass)
    for item in er.async_entries_for_config_entry(registry, entry.entry_id):
        if item.unique_id not in keep:
            registry.async_remove(item.entity_id)

    async_add_entities(
        [
            *(ZmanSensor(entry, DEVICE_ZMANIM, key) for key in ZMANIM),
            HebrewDateSensor(entry, DEVICE_ZMANIM, HEBREW_DATE),
            ParashaSensor(entry, DEVICE_SHABBAT, "parasha"),
            NextFastStartSensor(entry, DEVICE_SHABBAT, "next_fast_start"),
            NextFastEndSensor(entry, DEVICE_SHABBAT, "next_fast_end"),
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


class NextFastStartSensor(TimeSensor):
    """The next fast start still to come."""

    @property
    def native_value(self) -> dt.datetime:
        """Return the time."""
        return self.coordinator.data.next_fast_start


class NextFastEndSensor(TimeSensor):
    """The next fast end still to come."""

    @property
    def native_value(self) -> dt.datetime:
        """Return the time."""
        return self.coordinator.data.next_fast_end


class HebrewDateSensor(ZmanimShabbatEntity, SensorEntity):
    """Today's Hebrew date, which changes at sunset."""

    @property
    def native_value(self) -> str:
        """Return the date in Home Assistant's language."""
        return format_hebrew_date(
            self.coordinator.data.hebrew_date, self.hass.config.language
        )

    @property
    def extra_state_attributes(self) -> dict[str, int | str]:
        """Return the parts, for use in automations."""
        date = self.coordinator.data.hebrew_date
        return {"day": date.day, "month": date.month.name.lower(), "year": date.year}


class ParashaSensor(ZmanimShabbatEntity, SensorEntity):
    """This week's Torah portion, named in translations/."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [parasha.name.lower() for parasha in Parasha]

    @property
    def native_value(self) -> str:
        """Return the portion for the coming Shabbat."""
        return self.coordinator.data.parasha
