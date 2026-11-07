"""Whether Shabbat or Yom Tov is in effect."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ZmanimConfigEntry
from .entity import DEVICE_SHABBAT, ZmanimShabbatEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZmanimConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensor."""
    async_add_entities([InEffectSensor(entry, DEVICE_SHABBAT, "in_effect")])


class InEffectSensor(ZmanimShabbatEntity, BinarySensorEntity):
    """On from candle lighting to havdalah."""

    @property
    def is_on(self) -> bool:
        """Return whether Shabbat or Yom Tov is in effect."""
        return self.coordinator.data.in_effect
