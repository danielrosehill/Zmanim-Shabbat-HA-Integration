"""Calculations, checked against the Jerusalem calendar."""

import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from hdate.holidays import HOLIDAYS
from hdate.parasha import Parasha

from custom_components.zmanim_shabbat.calc import (
    Settings,
    default_candle_lighting_minutes,
    format_hebrew_date,
    snapshot,
)

TZ = ZoneInfo("Asia/Jerusalem")
JERUSALEM = Settings(31.778, 35.235, 0, TZ, False, 40, 0)


def at(*args):
    return dt.datetime(*args, tzinfo=TZ)


def test_offset_moves_candle_lighting():
    friday = at(2026, 11, 13, 9)
    forty = snapshot(JERUSALEM, friday).next_candle_lighting
    eighteen = snapshot(
        Settings(31.778, 35.235, 0, TZ, False, 18, 0), friday
    ).next_candle_lighting
    assert eighteen - forty == dt.timedelta(minutes=22)


def test_in_effect_follows_candle_lighting_and_havdalah():
    candles = snapshot(JERUSALEM, at(2026, 11, 13, 9)).next_candle_lighting
    havdalah = snapshot(JERUSALEM, at(2026, 11, 14, 9)).next_havdalah
    minute = dt.timedelta(minutes=1)
    assert not snapshot(JERUSALEM, candles - minute).in_effect
    assert snapshot(JERUSALEM, candles).in_effect
    assert snapshot(JERUSALEM, at(2026, 11, 14, 0, 30)).in_effect
    assert snapshot(JERUSALEM, havdalah - minute).in_effect
    assert not snapshot(JERUSALEM, havdalah).in_effect


def test_next_times_never_point_backwards():
    # Saturday night after havdalah: both must already be next week's.
    late = snapshot(JERUSALEM, at(2026, 11, 14, 22))
    assert late.next_candle_lighting.date() == dt.date(2026, 11, 20)
    assert late.next_havdalah.date() == dt.date(2026, 11, 21)


def test_stretch_of_shabbat_into_yom_tov():
    # Rosh Hashana 5787 is Saturday and Sunday, 12 and 13 September 2026.
    friday = snapshot(JERUSALEM, at(2026, 9, 11, 9))
    assert friday.next_candle_lighting.date() == dt.date(2026, 9, 11)
    assert friday.next_havdalah.date() == dt.date(2026, 9, 13)
    saturday = snapshot(JERUSALEM, at(2026, 9, 12, 9))
    assert saturday.in_effect
    # Second-night candles come from the havdalah calculation, not the offset.
    assert saturday.next_candle_lighting.date() == dt.date(2026, 9, 12)
    assert saturday.next_havdalah.date() == dt.date(2026, 9, 13)
    assert snapshot(JERUSALEM, at(2026, 9, 12, 23)).in_effect


def test_diaspora_second_day():
    # Sukkot 5787 is Saturday 26 September 2026. Sunday is Chol HaMoed in Israel
    # and the second day of Yom Tov outside it.
    sunday = at(2026, 9, 27, 12)
    outside = Settings(31.778, 35.235, 0, TZ, True, 40, 0)
    assert not snapshot(JERUSALEM, sunday).in_effect
    assert snapshot(outside, sunday).in_effect


def test_elevation_is_used_and_not_left_to_hdates_default():
    # 7 November 2026 at sea level, matching core Jewish Calendar on a live install.
    moment = at(2026, 11, 7, 12)
    sea = snapshot(Settings(31.7851118, 35.2141063, 0, TZ, False, 40, 0), moment)
    high = snapshot(Settings(31.7851118, 35.2141063, 754, TZ, False, 40, 0), moment)
    assert sea.zmanim["shkia"] == at(2026, 11, 7, 16, 45)
    assert sea.next_havdalah == at(2026, 11, 7, 17, 23)
    assert high.zmanim["shkia"] == at(2026, 11, 7, 16, 48)


def test_jerusalem_area_defaults_to_40():
    assert default_candle_lighting_minutes(31.785, 35.214) == 40  # City centre
    assert default_candle_lighting_minutes(31.797, 35.103) == 40  # Mevaseret Zion
    assert default_candle_lighting_minutes(32.085, 34.782) == 18  # Tel Aviv
    assert default_candle_lighting_minutes(31.747, 34.988) == 18  # Beit Shemesh
    assert default_candle_lighting_minutes(40.713, -74.006) == 18  # New York


def test_occasion_names_what_is_in_effect():
    assert snapshot(JERUSALEM, at(2026, 11, 7, 12)).occasion == "shabbat"
    assert snapshot(JERUSALEM, at(2026, 11, 9, 12)).occasion == "none"
    # Friday night counts as the Shabbat it starts.
    assert snapshot(JERUSALEM, at(2026, 11, 13, 20)).occasion == "shabbat"
    # Rosh Hashana: Shabbat with Yom Tov, then Yom Tov alone on Sunday.
    assert snapshot(JERUSALEM, at(2026, 9, 12, 12)).occasion == "shabbat_yom_tov"
    assert snapshot(JERUSALEM, at(2026, 9, 13, 12)).occasion == "yom_tov"


def test_every_parasha_has_a_name_in_both_languages():
    root = Path("custom_components/zmanim_shabbat/translations")
    for language in ("en", "he"):
        names = json.loads((root / f"{language}.json").read_text())
        states = names["entity"]["sensor"]["parasha"]["state"]
        assert set(states) == {parasha.name.lower() for parasha in Parasha}


def test_occasion_at_the_moments_announcements_read_it():
    # Candle lighting is before sunset, on a day that is not itself holy.
    # Pesach 5787 is Thursday 22 April 2027, Yom Kippur Monday 21 September 2026.
    for erev in (at(2027, 4, 21, 9), at(2026, 9, 20, 9)):
        candles = snapshot(JERUSALEM, erev).next_candle_lighting
        assert snapshot(JERUSALEM, candles).in_effect
        assert snapshot(JERUSALEM, candles).occasion == "yom_tov"
    friday = snapshot(JERUSALEM, at(2026, 11, 13, 9)).next_candle_lighting
    assert snapshot(JERUSALEM, friday).occasion == "shabbat"
    # Between sunset and havdalah on the last day, with nothing holy tomorrow.
    assert snapshot(JERUSALEM, at(2027, 4, 22, 19, 15)).occasion == "yom_tov"
    assert snapshot(JERUSALEM, at(2026, 11, 14, 16, 50)).occasion == "shabbat"


def test_minor_fast_runs_from_alot_to_fast_tzeit():
    # Tzom Gedaliah 5787 is Monday 14 September 2026.
    noon = snapshot(JERUSALEM, at(2026, 9, 14, 12))
    assert noon.fast_day
    assert noon.next_fast_end.date() == dt.date(2026, 9, 14)
    assert snapshot(JERUSALEM, at(2026, 9, 14, 3)).next_fast_start.date() == dt.date(2026, 9, 14)
    assert not snapshot(JERUSALEM, at(2026, 9, 14, 3)).fast_day
    assert not snapshot(JERUSALEM, at(2026, 9, 14, 21)).fast_day


def test_tisha_bav_starts_the_evening_before():
    # Tisha B'Av 5787 is Thursday 12 August 2027.
    assert not snapshot(JERUSALEM, at(2027, 8, 11, 18)).fast_day
    assert snapshot(JERUSALEM, at(2027, 8, 11, 21)).fast_day
    assert snapshot(JERUSALEM, at(2027, 8, 12, 12)).fast_day


def test_yom_kippur_is_a_fast_ending_at_havdalah():
    # Yom Kippur 5787 is Monday 21 September 2026.
    assert snapshot(JERUSALEM, at(2026, 9, 20, 21)).fast_day
    day = snapshot(JERUSALEM, at(2026, 9, 21, 12))
    assert day.fast_day
    assert day.next_fast_end == day.next_havdalah


def test_fast_lookups_never_run_out_over_a_year():
    for days in range(0, 400, 3):
        when = at(2026, 9, 1, 12) + dt.timedelta(days=days)
        result = snapshot(JERUSALEM, when)
        assert result.next_fast_start > when
        assert result.next_fast_end > when


def test_chol_hamoed():
    # Sukkot 5787: Yom Tov Saturday 26 September, Chol HaMoed to Friday 2 October.
    assert not snapshot(JERUSALEM, at(2026, 9, 26, 12)).chol_hamoed
    assert snapshot(JERUSALEM, at(2026, 9, 27, 12)).chol_hamoed
    # Hoshana Raba counts, though hdate types it as erev Yom Tov.
    assert snapshot(JERUSALEM, at(2026, 10, 2, 12)).chol_hamoed
    assert not snapshot(JERUSALEM, at(2026, 10, 2, 20)).chol_hamoed
    # Shabbat Chol HaMoed counts. Pesach 5787 is Thursday 22 April 2027.
    assert snapshot(JERUSALEM, at(2027, 4, 24, 12)).chol_hamoed
    # The last day counts, though hdate types it as erev Yom Tov, until candles.
    assert snapshot(JERUSALEM, at(2027, 4, 27, 12)).chol_hamoed
    assert not snapshot(JERUSALEM, at(2027, 4, 27, 20)).chol_hamoed


def test_hebrew_date_changes_at_sunset_and_formats_in_both_languages():
    noon = snapshot(JERUSALEM, at(2026, 11, 9, 12)).hebrew_date
    night = snapshot(JERUSALEM, at(2026, 11, 9, 20)).hebrew_date
    assert night.day == noon.day + 1
    assert format_hebrew_date(noon, "en") == "29 Cheshvan 5787"
    assert format_hebrew_date(noon, "he").endswith('בחשוון תשפ"ז')
    assert format_hebrew_date(noon, "fr") == "29 Cheshvan 5787"


def test_next_shabbat_matches_candles_and_havdalah_in_an_ordinary_week():
    week = snapshot(JERUSALEM, at(2026, 11, 10, 12))
    assert week.next_shabbat_start == week.next_candle_lighting
    assert week.next_shabbat_end == week.next_havdalah


def test_next_shabbat_ignores_yom_tov_and_never_points_backwards():
    # Monday of Yom Kippur week: the next candles are for Yom Kippur.
    monday = snapshot(JERUSALEM, at(2026, 9, 14, 12))
    assert monday.next_candle_lighting.date() == dt.date(2026, 9, 18)
    # During Shabbat: this end, and next week's start.
    shabbat = snapshot(JERUSALEM, at(2026, 11, 14, 12))
    assert shabbat.next_shabbat_end.date() == dt.date(2026, 11, 14)
    assert shabbat.next_shabbat_start.date() == dt.date(2026, 11, 20)
    # Rosh Hashana on Shabbat and Sunday: Shabbat still ends on Saturday night.
    assert snapshot(JERUSALEM, at(2026, 9, 12, 12)).next_shabbat_end.date() == dt.date(
        2026, 9, 12
    )
    for days in range(0, 400, 1):
        when = at(2026, 9, 1, 12) + dt.timedelta(days=days)
        result = snapshot(JERUSALEM, when)
        assert when < result.next_shabbat_start <= when + dt.timedelta(days=8)
        assert when < result.next_shabbat_end <= when + dt.timedelta(days=8)


def test_erev_and_motzei():
    candles = snapshot(JERUSALEM, at(2026, 11, 13, 9)).next_candle_lighting
    assert snapshot(JERUSALEM, at(2026, 11, 13, 9)).erev
    assert not snapshot(JERUSALEM, candles).erev
    assert not snapshot(JERUSALEM, at(2026, 11, 14, 12)).motzei
    assert snapshot(JERUSALEM, at(2026, 11, 14, 22)).motzei


def test_holiday_follows_the_evening():
    assert snapshot(JERUSALEM, at(2026, 11, 9, 12)).holiday == "none"
    assert snapshot(JERUSALEM, at(2026, 9, 25, 12)).holiday == "erev_sukkot"
    assert snapshot(JERUSALEM, at(2026, 9, 25, 20)).holiday == "sukkot"
    both = snapshot(JERUSALEM, at(2026, 10, 3, 12))
    assert both.holidays == ["shmini_atzeret", "simchat_torah"]


def test_every_holiday_has_a_name_in_both_languages():
    root = Path("custom_components/zmanim_shabbat/translations")
    for language in ("en", "he"):
        names = json.loads((root / f"{language}.json").read_text())
        states = names["entity"]["sensor"]["holiday"]["state"]
        assert set(states) == {"none"} | {holiday.name for holiday in HOLIDAYS}
