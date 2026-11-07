"""Calculations, checked against the Jerusalem calendar."""

import datetime as dt
from zoneinfo import ZoneInfo

from custom_components.zmanim_shabbat.calc import Settings, snapshot

TZ = ZoneInfo("Asia/Jerusalem")
JERUSALEM = Settings(31.778, 35.235, TZ, False, 40, 0)


def at(*args):
    return dt.datetime(*args, tzinfo=TZ)


def test_offset_moves_candle_lighting():
    friday = at(2026, 11, 13, 9)
    forty = snapshot(JERUSALEM, friday).next_candle_lighting
    eighteen = snapshot(
        Settings(31.778, 35.235, TZ, False, 18, 0), friday
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
    outside = Settings(31.778, 35.235, TZ, True, 40, 0)
    assert not snapshot(JERUSALEM, sunday).in_effect
    assert snapshot(outside, sunday).in_effect
