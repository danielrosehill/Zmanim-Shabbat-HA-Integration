"""Constants for Zmanim and Shabbat."""

DOMAIN = "zmanim_shabbat"

CONF_DIASPORA = "diaspora"
CONF_CANDLE_LIGHTING_MINUTES = "candle_lighting_minutes"
CONF_HAVDALAH_MINUTES = "havdalah_minutes"
CONF_ZMANIM = "zmanim"

DEFAULT_CANDLE_LIGHTING_MINUTES = 18
DEFAULT_HAVDALAH_MINUTES = 0  # 0 means three stars, not sunset.

# Keys are hdate's names, so they map straight onto Zmanim.zmanim.
ALL_ZMANIM = (
    "alot_hashachar",
    "talit_and_tefillin",
    "netz_hachama",
    "sof_zman_shema_mga",
    "sof_zman_shema_gra",
    "sof_zman_tfilla_mga",
    "sof_zman_tfilla_gra",
    "chatzot_hayom",
    "mincha_gedola",
    "mincha_gedola_30min",
    "mincha_ketana",
    "plag_hamincha",
    "shkia",
    "tset_hakohavim_tsom",
    "tset_hakohavim_shabbat",
    "tset_hakohavim",
    "tset_hakohavim_rabeinu_tam",
    "chatzot_halayla",
)

DEFAULT_ZMANIM = [
    "netz_hachama",
    "sof_zman_shema_gra",
    "sof_zman_tfilla_gra",
    "chatzot_hayom",
    "mincha_gedola",
    "plag_hamincha",
    "shkia",
    "tset_hakohavim_shabbat",
]
