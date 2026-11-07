"""The Shabbat dashboard as data. No Home Assistant imports, so this can be tested alone.

Core cards only, so it renders on a stock install. dashboards/shabbat.yaml is this
with every section on, for anyone who would rather paste and edit it.
"""

from typing import Any

from .const import ZMANIM

TITLE = {"en": "Shabbat", "he": "שבת"}
HEADINGS = {
    "en": {
        "status": "Status",
        "times": "Shabbat and Yom Tov times",
        "zmanim": "Today's zmanim",
        "fasts": "Fasts and Chol HaMoed",
        "weather": "Weather",
        "alerts": "Red alerts",
    },
    "he": {
        "status": "מצב",
        "times": "זמני שבת וחג",
        "zmanim": "זמני היום",
        "fasts": "צומות וחול המועד",
        "weather": "מזג אוויר",
        "alerts": "צבע אדום",
    },
}

# The entity IDs on an English install, used for the YAML copy and as placeholders.
ALERT_ENTITY = "binary_sensor.oref_alert"
DEFAULT_WEATHER_ENTITY = "weather.home"
DEFAULT_IDS = {
    **{
        key: f"sensor.zmanim_{'chatzot' if key == 'chatzot_hayom' else key}"
        for key in ZMANIM
    },
    "hebrew_date": "sensor.zmanim_hebrew_date",
    "in_effect": "binary_sensor.shabbat_and_yom_tov_in_effect",
    "erev_shabbat_yom_tov": "binary_sensor.shabbat_and_yom_tov_erev_shabbat_or_yom_tov",
    "motzei_shabbat_yom_tov": "binary_sensor.shabbat_and_yom_tov_motzei_shabbat_or_yom_tov",
    "chol_hamoed": "binary_sensor.shabbat_and_yom_tov_chol_hamoed",
    "fast_day": "binary_sensor.shabbat_and_yom_tov_fast_day",
    "parasha": "sensor.shabbat_and_yom_tov_parasha",
    "holiday": "sensor.shabbat_and_yom_tov_holiday",
    "next_shabbat_start": "sensor.shabbat_and_yom_tov_next_shabbat_start",
    "next_shabbat_end": "sensor.shabbat_and_yom_tov_next_shabbat_end",
    "next_candle_lighting": "sensor.shabbat_and_yom_tov_next_candle_lighting",
    "next_havdalah": "sensor.shabbat_and_yom_tov_next_havdalah",
    "next_fast_start": "sensor.shabbat_and_yom_tov_next_fast_start",
    "next_fast_end": "sensor.shabbat_and_yom_tov_next_fast_end",
}


def _section(title: str, icon: str, *cards: dict[str, Any]) -> dict[str, Any]:
    heading = {"type": "heading", "heading": title, "icon": icon}
    return {"type": "grid", "cards": [heading, *cards]}


def _tile(entity: str) -> dict[str, Any]:
    return {"type": "tile", "entity": entity}


def _times(ids: dict[str, str], keys: list[str], display: str) -> dict[str, Any]:
    """List times as clock times. A tile would show "in 3 hours"."""
    return {
        "type": "entities",
        "entities": [{"entity": ids[key], "format": display} for key in keys],
    }


def build(
    ids: dict[str, str],
    sections: set[str],
    language: str = "en",
    weather: str | None = None,
    alert: str | None = None,
) -> dict[str, Any]:
    """Return the dashboard config. sections holds the DASHBOARD_SECTIONS turned on."""
    text = HEADINGS.get(language, HEADINGS["en"])
    status = [
        _tile(ids[key])
        for key in (
            "hebrew_date",
            "in_effect",
            "parasha",
            "holiday",
            "erev_shabbat_yom_tov",
            "motzei_shabbat_yom_tov",
        )
    ]
    if "dashboard_clock" in sections:
        status.insert(0, {"type": "clock", "clock_size": "large"})
    cards = [
        _section(text["status"], "mdi:star-david", *status),
        _section(
            text["times"],
            "mdi:candle",
            _times(
                ids,
                [
                    "next_shabbat_start",
                    "next_shabbat_end",
                    "next_candle_lighting",
                    "next_havdalah",
                ],
                "datetime",
            ),
        ),
    ]
    if "dashboard_zmanim" in sections:
        cards.append(
            _section(
                text["zmanim"], "mdi:weather-sunset", _times(ids, list(ZMANIM), "time")
            )
        )
    if "dashboard_fasts" in sections:
        cards.append(
            _section(
                text["fasts"],
                "mdi:calendar-star",
                _tile(ids["chol_hamoed"]),
                _tile(ids["fast_day"]),
                _times(ids, ["next_fast_start", "next_fast_end"], "datetime"),
            )
        )
    if "dashboard_weather" in sections and weather:
        cards.append(
            _section(
                text["weather"],
                "mdi:weather-partly-cloudy",
                {
                    "type": "weather-forecast",
                    "entity": weather,
                    "forecast_type": "daily",
                },
            )
        )
    if "dashboard_alerts" in sections and alert:
        cards.append(_section(text["alerts"], "mdi:alarm-light", _tile(alert)))
    return {
        "title": TITLE.get(language, TITLE["en"]),
        "views": [{"type": "sections", "max_columns": 3, "sections": cards}],
    }
