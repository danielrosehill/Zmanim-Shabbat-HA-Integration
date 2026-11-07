"""Constants for Zmanim and Shabbat."""

DOMAIN = "zmanim_shabbat"

CONF_DIASPORA = "diaspora"
CONF_CANDLE_LIGHTING_MINUTES = "candle_lighting_minutes"
CONF_HAVDALAH_MINUTES = "havdalah_minutes"
CONF_DASHBOARD = "dashboard"
# Sections of the dashboard that can be switched off.
DASHBOARD_SECTIONS = (
    "dashboard_clock",
    "dashboard_zmanim",
    "dashboard_fasts",
    "dashboard_weather",
    "dashboard_alerts",
)

DEFAULT_CANDLE_LIGHTING_MINUTES = 18
JERUSALEM_CANDLE_LIGHTING_MINUTES = 40
DEFAULT_HAVDALAH_MINUTES = 0  # 0 means three stars, not sunset.

# One time per slot, no rabbinic alternatives. Our key -> hdate's name.
# Shema and Tefilla follow the GRA. Tzeit is the Shabbat three stars, so it
# agrees with the default havdalah.
ZMANIM = {
    "alot_hashachar": "alot_hashachar",
    "talit_and_tefillin": "talit_and_tefillin",
    "netz_hachama": "netz_hachama",
    "sof_zman_shema": "sof_zman_shema_gra",
    "sof_zman_tefilla": "sof_zman_tfilla_gra",
    "chatzot_hayom": "chatzot_hayom",
    "mincha_gedola": "mincha_gedola",
    "mincha_ketana": "mincha_ketana",
    "plag_hamincha": "plag_hamincha",
    "shkia": "shkia",
    "tzeit_hakochavim": "tset_hakohavim_shabbat",
    "chatzot_halayla": "chatzot_halayla",
}

# hdate month name -> (English, Hebrew).
MONTHS = {
    "TISHREI": ("Tishrei", "תשרי"),
    "MARCHESHVAN": ("Cheshvan", "חשוון"),
    "KISLEV": ("Kislev", "כסלו"),
    "TEVET": ("Tevet", "טבת"),
    "SHVAT": ("Shvat", "שבט"),
    "ADAR": ("Adar", "אדר"),
    "ADAR_I": ("Adar I", "אדר א'"),
    "ADAR_II": ("Adar II", "אדר ב'"),
    "NISAN": ("Nisan", "ניסן"),
    "IYYAR": ("Iyar", "אייר"),
    "SIVAN": ("Sivan", "סיוון"),
    "TAMMUZ": ("Tammuz", "תמוז"),
    "AV": ("Av", "אב"),
    "ELUL": ("Elul", "אלול"),
}

# Every entity besides the zmanim. sensor.py removes anything not listed here.
SHABBAT_ENTITIES = (
    "in_effect",
    "erev_shabbat_yom_tov",
    "motzei_shabbat_yom_tov",
    "chol_hamoed",
    "fast_day",
    "parasha",
    "holiday",
    "next_shabbat_start",
    "next_shabbat_end",
    "next_candle_lighting",
    "next_havdalah",
    "next_fast_start",
    "next_fast_end",
)
HEBREW_DATE = "hebrew_date"
