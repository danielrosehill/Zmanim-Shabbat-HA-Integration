"""Base entity and the two devices."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZmanimConfigEntry, ZmanimCoordinator

DEVICE_ZMANIM = ("zmanim", "Zmanim")
DEVICE_SHABBAT = ("shabbat", "Shabbat and Yom Tov")


class ZmanimShabbatEntity(CoordinatorEntity[ZmanimCoordinator]):
    """An entity on one of the two devices."""

    _attr_has_entity_name = True

    def __init__(
        self, entry: ZmanimConfigEntry, device: tuple[str, str], key: str
    ) -> None:
        super().__init__(entry.runtime_data)
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}-{key}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{entry.entry_id}-{device[0]}")},
            name=device[1],
        )
