"""Setup, entities, options and scheduled updates."""

import datetime as dt
from zoneinfo import ZoneInfo

from freezegun.api import FrozenDateTimeFactory
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.zmanim_shabbat.const import DOMAIN

from .conftest import OPTIONS

TZ = ZoneInfo("Asia/Jerusalem")
IN_EFFECT = "binary_sensor.shabbat_and_yom_tov_in_effect"
CANDLES = "sensor.shabbat_and_yom_tov_next_candle_lighting"


async def setup(hass, entry):
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_config_flow(hass, jerusalem):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], OPTIONS)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"] == OPTIONS


async def test_uses_home_assistant_elevation(hass, jerusalem, entry):
    hass.config.elevation = 123
    await setup(hass, entry)
    assert entry.runtime_data.settings.elevation == 123


async def test_two_devices(hass, jerusalem, entry):
    await setup(hass, entry)
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert sorted(device.name for device in devices) == ["Shabbat and Yom Tov", "Zmanim"]
    assert hass.states.get("sensor.zmanim_shkia") is not None
    assert hass.states.get(IN_EFFECT) is not None


async def test_turns_on_at_candle_lighting(
    hass, jerusalem, entry, freezer: FrozenDateTimeFactory
):
    freezer.move_to(dt.datetime(2026, 11, 13, 9, tzinfo=TZ))
    await setup(hass, entry)
    assert hass.states.get(IN_EFFECT).state == "off"

    candles = dt.datetime.fromisoformat(hass.states.get(CANDLES).state)
    freezer.move_to(candles)
    async_fire_time_changed(hass, candles)
    await hass.async_block_till_done()

    assert hass.states.get(IN_EFFECT).state == "on"
    assert dt.datetime.fromisoformat(hass.states.get(CANDLES).state) > candles


async def test_zmanim_roll_over_at_midnight(
    hass, jerusalem, entry, freezer: FrozenDateTimeFactory
):
    freezer.move_to(dt.datetime(2026, 11, 9, 12, tzinfo=TZ))
    await setup(hass, entry)
    before = hass.states.get("sensor.zmanim_shkia").state

    midnight = dt.datetime(2026, 11, 10, 0, 0, 1, tzinfo=TZ)
    freezer.move_to(midnight)
    async_fire_time_changed(hass, midnight)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.zmanim_shkia").state != before


async def test_options_remove_unselected_zman(hass, jerusalem, entry):
    await setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], OPTIONS | {"zmanim": ["shkia"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    assert registry.async_get("sensor.zmanim_shkia") is not None
    assert registry.async_get("sensor.zmanim_plag_hamincha") is None
    assert registry.async_get(IN_EFFECT) is not None


async def test_unload_cancels_schedule(hass, jerusalem, entry):
    await setup(hass, entry)
    coordinator = entry.runtime_data
    assert coordinator._unsub is not None
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert coordinator._unsub is None
