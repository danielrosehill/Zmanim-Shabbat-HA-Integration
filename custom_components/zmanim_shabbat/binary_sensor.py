"""Whether Shabbat, Yom Tov, Chol HaMoed or a fast is in effect."""

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
    """Add the sensors."""
    async_add_entities(
        [
            InEffectSensor(entry, DEVICE_SHABBAT, "in_effect"),
            CholHamoedSensor(entry, DEVICE_SHABBAT, "chol_hamoed"),
            FastDaySensor(entry, DEVICE_SHABBAT, "fast_day"),
        ]
    )


class InEffectSensor(ZmanimShabbatEntity, BinarySensorEntity):
    """On from candle lighting to havdalah."""

    @property
    def is_on(self) -> bool:
        """Return whether Shabbat or Yom Tov is in effect."""
        return self.coordinator.data.in_effect

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Say which it is, so announcements can name it."""
        return {"occasion": self.coordinator.data.occasion}


class CholHamoedSensor(ZmanimShabbatEntity, BinarySensorEntity):
    """On during Chol HaMoed, including its Shabbat, but not on Yom Tov."""

    @property
    def is_on(self) -> bool:
        """Return whether it is Chol HaMoed."""
        return self.coordinator.data.chol_hamoed


class FastDaySensor(ZmanimShabbatEntity, BinarySensorEntity):
    """On from the start of a fast to its end."""

    @property
    def is_on(self) -> bool:
        """Return whether a fast is on."""
        return self.coordinator.data.fast_day
