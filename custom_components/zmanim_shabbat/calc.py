"""Time calculations. No Home Assistant imports, so this can be tested alone."""

from dataclasses import dataclass
import datetime as dt
import math

from hdate.gematria import hebrew_number
from hdate import HDateInfo, HebrewDate, HolidayTypes, Location, Zmanim

from .const import (
    DEFAULT_CANDLE_LIGHTING_MINUTES,
    JERUSALEM_CANDLE_LIGHTING_MINUTES,
    MONTHS,
    ZMANIM,
)

# Shabbat is weekly, so a candle lighting and a havdalah always fall inside this.
# Nine days covers the longest stretch, a two-day Yom Tov running into Shabbat.
LOOKAHEAD_DAYS = 9

# The longest gap between fasts is Taanit Esther to 17 Tammuz, about 125 days.
FAST_LOOKAHEAD_DAYS = 150

# The 40-minute custom covers the city and the towns right around it.
JERUSALEM = (31.778, 35.235)
JERUSALEM_RADIUS_KM = 15
EARTH_RADIUS_KM = 6371


def default_candle_lighting_minutes(latitude: float, longitude: float) -> int:
    """Return 40 inside the Jerusalem area and 18 anywhere else."""
    lat1, lon1, lat2, lon2 = map(math.radians, (latitude, longitude, *JERUSALEM))
    half_chord = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    distance = 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(half_chord))
    if distance <= JERUSALEM_RADIUS_KM:
        return JERUSALEM_CANDLE_LIGHTING_MINUTES
    return DEFAULT_CANDLE_LIGHTING_MINUTES


@dataclass(frozen=True)
class Settings:
    """Everything a calculation depends on."""

    latitude: float
    longitude: float
    elevation: float
    timezone: dt.tzinfo
    diaspora: bool
    candle_lighting_minutes: int
    havdalah_minutes: int


@dataclass(frozen=True)
class Snapshot:
    """The state of the day at one moment."""

    zmanim: dict[str, dt.datetime]
    in_effect: bool
    occasion: str
    parasha: str
    hebrew_date: HebrewDate
    chol_hamoed: bool
    fast_day: bool
    next_candle_lighting: dt.datetime
    next_havdalah: dt.datetime
    next_fast_start: dt.datetime
    next_fast_end: dt.datetime
    next_update: dt.datetime


def _zmanim(settings: Settings, date: dt.date) -> Zmanim:
    return Zmanim(
        date=date,
        location=Location(
            name="Home",
            latitude=settings.latitude,
            longitude=settings.longitude,
            # Always set this: hdate's own default is Jerusalem's 754 m.
            altitude=settings.elevation,
            timezone=settings.timezone,
            diaspora=settings.diaspora,
        ),
        candle_lighting_offset=settings.candle_lighting_minutes,
        havdalah_offset=settings.havdalah_minutes,
    )


def _next(settings: Settings, now: dt.datetime, today: dt.date, attr: str) -> dt.datetime:
    """Return the first candle lighting or havdalah strictly after now."""
    for offset in range(LOOKAHEAD_DAYS):
        when = getattr(_zmanim(settings, today + dt.timedelta(days=offset)), attr)
        if when is not None and when > now:
            return when
    raise ValueError(f"No {attr} within {LOOKAHEAD_DAYS} days of {now}")


def _fast_window(
    settings: Settings, date: dt.date
) -> tuple[dt.datetime, dt.datetime] | None:
    """Return when the fast on date starts and ends, if there is one.

    hdate types Yom Kippur as Yom Tov, and gives no fast start time.
    """
    names = {
        holiday.name
        for holiday in HDateInfo(date, diaspora=settings.diaspora).holidays
        if holiday.type is HolidayTypes.FAST_DAY or holiday.name == "yom_kippur"
    }
    if not names:
        return None
    day = _zmanim(settings, date)
    eve = _zmanim(settings, date - dt.timedelta(days=1)).zmanim["shkia"].local
    if "yom_kippur" in names:
        return eve, day.havdalah
    end = day.zmanim["tset_hakohavim_tsom"].local
    if "tisha_bav" in names:
        return eve, end
    return day.zmanim["alot_hashachar"].local, end


def _fasts(
    settings: Settings, now: dt.datetime, today: dt.date
) -> tuple[bool, dt.datetime, dt.datetime]:
    """Return whether a fast is on, and the next start and end after now."""
    active = False
    next_start = next_end = None
    # A fast that began at sunset is dated tomorrow, so start from today.
    for offset in range(FAST_LOOKAHEAD_DAYS):
        window = _fast_window(settings, today + dt.timedelta(days=offset))
        if window is None:
            continue
        start, end = window
        active = active or start <= now < end
        if next_end is None and end > now:
            next_end = end
        if start > now:
            next_start = start
            break
    if next_start is None or next_end is None:
        raise ValueError(f"No fast within {FAST_LOOKAHEAD_DAYS} days of {now}")
    return active, next_start, next_end


def _is_chol_hamoed(info: HDateInfo) -> bool:
    """Match by name: hdate types Hoshana Raba and the last day as erev Yom Tov."""
    return any(
        holiday.name.startswith("hol_hamoed") or holiday.name == "hoshana_raba"
        for holiday in info.holidays
    )


def _occasion(settings: Settings, now: dt.datetime, today: dt.date, day: Zmanim) -> str:
    """Name the holy day in effect at now: none, shabbat, yom_tov or both."""
    if not day.issur_melacha_in_effect(now):
        return "none"
    current = HDateInfo(today, diaspora=settings.diaspora)
    following = HDateInfo(today + dt.timedelta(days=1), diaspora=settings.diaspora)
    # These two count Shabbat as well. After sunset the evening belongs to the
    # next day if it is Shabbat or Yom Tov.
    # Candle lighting comes before sunset, so an ordinary day also looks ahead.
    after_sunset = now >= day.zmanim["shkia"].local
    yom_tov_today = current.is_shabbat or current.is_yom_tov
    yom_tov_tomorrow = following.is_shabbat or following.is_yom_tov
    info = following if not yom_tov_today or (after_sunset and yom_tov_tomorrow) else current
    if info.is_shabbat and info.is_yom_tov:
        return "shabbat_yom_tov"
    return "yom_tov" if info.is_yom_tov else "shabbat"


def snapshot(settings: Settings, now: dt.datetime) -> Snapshot:
    """Calculate the day's zmanim and the Shabbat and Yom Tov status at now."""
    today = now.astimezone(settings.timezone).date()
    day = _zmanim(settings, today)
    sunset = day.zmanim["shkia"].local
    evening = today + dt.timedelta(days=1) if now >= sunset else today
    evening_info = HDateInfo(evening, diaspora=settings.diaspora)
    occasion = _occasion(settings, now, today, day)
    fast_day, next_fast_start, next_fast_end = _fasts(settings, now, today)
    next_candle_lighting = _next(settings, now, today, "candle_lighting")
    next_havdalah = _next(settings, now, today, "havdalah")
    changes = [next_candle_lighting, next_havdalah, next_fast_start, next_fast_end]
    if sunset > now:
        changes.append(sunset)
    return Snapshot(
        zmanim={key: day.zmanim[name].local for key, name in ZMANIM.items()},
        in_effect=day.issur_melacha_in_effect(now),
        occasion=occasion,
        parasha=HDateInfo(
            today, diaspora=settings.diaspora
        ).upcoming_shabbat.parasha_obj.name.lower(),
        hebrew_date=evening_info.hdate,
        # Shabbat Chol HaMoed still counts. Yom Tov does not.
        chol_hamoed=_is_chol_hamoed(evening_info) and "yom_tov" not in occasion,
        fast_day=fast_day,
        next_candle_lighting=next_candle_lighting,
        next_havdalah=next_havdalah,
        next_fast_start=next_fast_start,
        next_fast_end=next_fast_end,
        next_update=min(changes),
    )


def format_hebrew_date(date: HebrewDate, language: str) -> str:
    """Write a Hebrew date in Hebrew, or in English for any other language."""
    english, hebrew = MONTHS[date.month.name]
    if language == "he":
        day = hebrew_number(date.day)
        year = hebrew_number(date.year % 1000)
        return f"{day} ב{hebrew} {year}"
    return f"{date.day} {english} {date.year}"
