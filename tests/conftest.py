"""Shared fixtures."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zmanim_shabbat.const import DOMAIN

OPTIONS = {
    "diaspora": False,
    "candle_lighting_minutes": 40,
    "havdalah_minutes": 0,
}


@pytest.fixture(autouse=True)
def auto_enable(enable_custom_integrations):
    yield


@pytest.fixture
async def jerusalem(hass):
    hass.config.latitude = 31.778
    hass.config.longitude = 35.235
    await hass.config.async_set_time_zone("Asia/Jerusalem")


@pytest.fixture
def entry(hass):
    item = MockConfigEntry(domain=DOMAIN, options=OPTIONS, title="Zmanim and Shabbat")
    item.add_to_hass(hass)
    return item
