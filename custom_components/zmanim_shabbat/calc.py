"""Time calculations. No Home Assistant imports, so this can be tested alone."""

from dataclasses import dataclass
import datetime as dt

from hdate import Location, Zmanim

# Shabbat is weekly, so a candle lighting and a havdalah always fall inside this.
# Nine days covers the longest stretch, a two-day Yom Tov running into Shabbat.
LOOKAHEAD_DAYS = 9


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
    next_candle_lighting: dt.datetime
    next_havdalah: dt.datetime


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


def snapshot(settings: Settings, now: dt.datetime) -> Snapshot:
    """Calculate the day's zmanim and the Shabbat and Yom Tov status at now."""
    today = now.astimezone(settings.timezone).date()
    day = _zmanim(settings, today)
    return Snapshot(
        zmanim={key: zman.local for key, zman in day.zmanim.items()},
        in_effect=day.issur_melacha_in_effect(now),
        next_candle_lighting=_next(settings, now, today, "candle_lighting"),
        next_havdalah=_next(settings, now, today, "havdalah"),
    )
