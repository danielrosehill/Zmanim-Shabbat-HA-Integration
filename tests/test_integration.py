"""Setup, entities, options and scheduled updates."""

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    async_fire_time_changed,
    async_mock_service,
)

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

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


async def test_old_zman_sensor_is_removed(hass, jerusalem, entry):
    registry = er.async_get(hass)
    old = registry.async_get_or_create(
        "sensor", DOMAIN, f"{entry.entry_id}-sof_zman_shema_mga", config_entry=entry
    )
    await setup(hass, entry)
    assert registry.async_get(old.entity_id) is None
    assert hass.states.get("sensor.zmanim_sof_zman_shema") is not None


async def test_config_form_defaults_to_40_in_jerusalem(hass, jerusalem):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["data_schema"]({})["candle_lighting_minutes"] == 40


async def test_parasha_and_occasion(
    hass, jerusalem, entry, freezer: FrozenDateTimeFactory
):
    freezer.move_to(dt.datetime(2026, 11, 7, 12, tzinfo=TZ))
    await setup(hass, entry)
    assert hass.states.get("sensor.shabbat_and_yom_tov_parasha").state == "chayei_sara"
    assert hass.states.get(IN_EFFECT).attributes["occasion"] == "shabbat"


async def test_unload_cancels_schedule(hass, jerusalem, entry):
    await setup(hass, entry)
    coordinator = entry.runtime_data
    assert coordinator._unsub is not None
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert coordinator._unsub is None


async def run_blueprint(hass, name, inputs, sensor_states):
    """Load a blueprint from this repo, then walk the sensor through its states."""
    hass.config.config_dir = str(Path.cwd())
    hass.states.async_set(IN_EFFECT, *sensor_states[0])
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "id": "under_test",
                "use_blueprint": {
                    "path": f"zmanim_shabbat/{name}.yaml",
                    "input": inputs,
                },
            }
        },
    )
    await hass.async_block_till_done()
    assert hass.states.async_all("automation")
    for state in sensor_states[1:]:
        hass.states.async_set(IN_EFFECT, *state)
        await hass.async_block_till_done()


SPEAK = {"speakers": ["media_player.home"], "tts_engine": "tts.test"}


@pytest.mark.parametrize(
    ("language", "states", "expected"),
    [
        ("en", [("off", {}), ("on", {"occasion": "shabbat"})], "Shabbat has started. Shabbat Shalom."),
        ("he", [("off", {}), ("on", {"occasion": "yom_tov"})], "נכנס החג. חג שמח."),
        ("en", [("on", {"occasion": "yom_tov"}), ("off", {"occasion": "none"})], "Yom Tov is over."),
        ("he", [("on", {"occasion": "shabbat"}), ("off", {"occasion": "none"})], "יצאה השבת. שבוע טוב."),
    ],
)
async def test_announce_blueprint_says_the_right_thing(hass, language, states, expected):
    calls = async_mock_service(hass, "tts", "speak")
    await run_blueprint(hass, "announce", SPEAK | {"message_language": language}, states)
    assert [call.data["message"] for call in calls] == [expected]
    assert calls[0].data["media_player_entity_id"] == ["media_player.home"]
    assert "language" not in calls[0].data


async def test_announce_blueprint_can_skip_the_start_and_set_a_language(hass):
    calls = async_mock_service(hass, "tts", "speak")
    await run_blueprint(
        hass,
        "announce",
        SPEAK | {"announce_start": False, "tts_language": "he-IL"},
        [
            ("off", {}),
            ("on", {"occasion": "shabbat"}),
            ("off", {"occasion": "none"}),
        ],
    )
    assert [call.data["message"] for call in calls] == ["Shabbat is over. Shavua Tov."]
    assert calls[0].data["language"] == "he-IL"


async def test_flash_blueprint_flashes_then_restores(hass):
    # No freezer here: frozen time would stop the blueprint's delays elapsing.
    created = async_mock_service(hass, "scene", "create")
    restored = async_mock_service(hass, "scene", "turn_on")
    on = async_mock_service(hass, "light", "turn_on")
    off = async_mock_service(hass, "light", "turn_off")
    await run_blueprint(
        hass,
        "flash_lights",
        {"lights": ["light.a", "light.b"], "seconds": 1, "flashes": 2},
        [("off", {}), ("on", {"occasion": "shabbat"})],
    )

    assert created[0].data["snapshot_entities"] == ["light.a", "light.b"]
    assert len(on) == len(off) == 2
    assert restored[0].data["entity_id"] == [f"scene.{created[0].data['scene_id']}"]


async def test_new_entities_exist(hass, jerusalem, entry, freezer: FrozenDateTimeFactory):
    freezer.move_to(dt.datetime(2026, 11, 7, 12, tzinfo=TZ))
    await setup(hass, entry)
    date = hass.states.get("sensor.zmanim_hebrew_date")
    assert date.state == "27 Cheshvan 5787"
    assert date.attributes["month"] == "marcheshvan"
    assert hass.states.get("binary_sensor.shabbat_and_yom_tov_chol_hamoed").state == "off"
    assert hass.states.get("binary_sensor.shabbat_and_yom_tov_fast_day").state == "off"
    assert hass.states.get("sensor.shabbat_and_yom_tov_next_fast_start") is not None
    assert hass.states.get("sensor.shabbat_and_yom_tov_next_fast_end") is not None


async def test_hebrew_date_rolls_over_at_sunset(
    hass, jerusalem, entry, freezer: FrozenDateTimeFactory
):
    freezer.move_to(dt.datetime(2026, 11, 9, 12, tzinfo=TZ))
    await setup(hass, entry)
    before = hass.states.get("sensor.zmanim_hebrew_date").state

    sunset = dt.datetime.fromisoformat(hass.states.get("sensor.zmanim_shkia").state)
    freezer.move_to(sunset)
    async_fire_time_changed(hass, sunset)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.zmanim_hebrew_date").state != before
