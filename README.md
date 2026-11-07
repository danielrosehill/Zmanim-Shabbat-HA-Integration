# Zmanim and Shabbat for Home Assistant

A small custom integration that gives you two devices: today's zmanim, and whether Shabbat or Yom Tov is in effect. It is a simpler alternative to the built-in Jewish Calendar integration, and it can run alongside it. The calculations come from the [hdate](https://github.com/py-libhdate/py-libhdate) library, which Jewish Calendar also uses.

Treat the times as a convenience. Check anything halachically important against your own calendar or rabbi.

## What you get

Names come from this integration's own English and Hebrew lists, in modern Israeli pronunciation. Home Assistant's language picks which one you see.

**Zmanim** device: twelve timestamp sensors with one time each and no alternative opinions, plus the Hebrew date.

| Entity | Meaning |
|---|---|
| `sensor.zmanim_alot_hashachar`, `_talit_and_tefillin`, `_netz_hachama` | Dawn, earliest talit and tefillin, sunrise |
| `sensor.zmanim_sof_zman_shema`, `_sof_zman_tefilla` | Latest Shema and Tefilla, following the GRA |
| `sensor.zmanim_chatzot`, `_mincha_gedola`, `_mincha_ketana`, `_plag_hamincha` | Midday and the afternoon times |
| `sensor.zmanim_shkia`, `_tzeit_hakochavim`, `_chatzot_halayla` | Sunset, three stars (the same as the default havdalah), midnight |
| `sensor.zmanim_hebrew_date` | The Hebrew date, changing at sunset. Attributes: `day`, `month`, `year` |

**Shabbat and Yom Tov** device:

| Entity | Meaning |
|---|---|
| `binary_sensor.shabbat_and_yom_tov_in_effect` | On from candle lighting until havdalah, across multi-day stretches. Attribute `occasion`: `shabbat`, `yom_tov`, `shabbat_yom_tov` or `none` |
| `binary_sensor.shabbat_and_yom_tov_erev_shabbat_or_yom_tov` | On during the day before Shabbat or Yom Tov, until candle lighting |
| `binary_sensor.shabbat_and_yom_tov_motzei_shabbat_or_yom_tov` | On from havdalah until midnight |
| `binary_sensor.shabbat_and_yom_tov_chol_hamoed` | On during Chol HaMoed, including Hoshana Raba and Shabbat Chol HaMoed. Off on Yom Tov |
| `binary_sensor.shabbat_and_yom_tov_fast_day` | On from the start of a fast to its end |
| `sensor.shabbat_and_yom_tov_parasha` | The portion for the coming Shabbat |
| `sensor.shabbat_and_yom_tov_holiday` | Today's holiday, changing at sunset. Attribute `all` lists both when a day has two |
| `sensor.shabbat_and_yom_tov_next_shabbat_start`, `_next_shabbat_end` | The next weekly Shabbat, ignoring any Yom Tov around it |
| `sensor.shabbat_and_yom_tov_next_candle_lighting` | The next candle lighting still to come, including second-night candles |
| `sensor.shabbat_and_yom_tov_next_havdalah` | The next havdalah still to come, at the end of the stretch, so it also gives the end of Yom Tov |
| `sensor.shabbat_and_yom_tov_next_fast_start`, `_next_fast_end` | The next fast start and end still to come |

The "next" sensors never show a time that has passed. Jewish Calendar's `upcoming` sensors keep the past time until midnight on Saturday night.

Fasts follow these times. Taanit Bechorot is not included.

| Fast | Starts | Ends |
|---|---|---|
| Tzom Gedaliah, Asara B'Tevet, Taanit Esther, 17 Tammuz | Alot HaShachar | Tzeit for fasts |
| Tisha B'Av | Sunset the evening before | Tzeit for fasts |
| Yom Kippur | Sunset the evening before | Havdalah |

## Blueprints

Both run when Shabbat or Yom Tov starts and ends. Import them under Settings → Automations & scenes → Blueprints → Import Blueprint, using these URLs:

- **Announcement:** `https://github.com/danielrosehill/Zmanim-Shabbat-HA-Integration/blob/main/blueprints/automation/zmanim_shabbat/announce.yaml`. Choose your speakers, a text to speech engine and English or Hebrew. It names Shabbat or Yom Tov correctly. The engine must be able to speak the language you choose.
- **Light flash:** `https://github.com/danielrosehill/Zmanim-Shabbat-HA-Integration/blob/main/blueprints/automation/zmanim_shabbat/flash_lights.yaml`. Choose your lights. They flash three times, then each goes back to how it was. List individual lights rather than a group, so each one can be restored.

## Dashboard

Turn on **Add a Shabbat dashboard to the sidebar** in the integration's settings, and it appears in the sidebar. It always shows status and Shabbat times. You choose yes or no for each of these:

- A clock
- Today's zmanim
- Fasts and Chol HaMoed
- The weather forecast, from your first weather entity
- Red alerts, if you have the Oref Alert integration

It uses only built-in cards, so there is nothing else to install, and it follows your language. It is read-only because the integration generates it. Removing the integration removes it. To customise your own copy, paste [`dashboards/shabbat.yaml`](dashboards/shabbat.yaml) into a new dashboard's raw configuration editor. A blueprint can't do this, because blueprints only cover automations, scripts and templates.

## Install

Copy `custom_components/zmanim_shabbat` to `/config/custom_components/`, or add this repository to HACS as a custom repository. Restart Home Assistant, then add **Zmanim and Shabbat** under Settings → Devices & services.

## Settings

Set these during setup, and change them later under Configure.

- **Candle lighting:** minutes before sunset. The form starts at 40 if your home is within 15 km of central Jerusalem, otherwise 18. Change it to follow your own custom.
- **Havdalah:** minutes after sunset. 0, the default, uses three stars instead.
- **Outside Israel:** two-day Yom Tov. Defaults to on unless Home Assistant's country is Israel.
- **Dashboard:** whether to add it, and which sections to show.

Location, elevation and time zone come from Home Assistant. Elevation changes sunrise and sunset by a few minutes. After changing any of them, reload the integration.

## Test status

Date: 2026-11-07. `uv sync --python 3.13 && .venv/bin/pytest` passes on Home Assistant 2026.2.3 with hdate 1.2.2.

Installed on a live Home Assistant 2026.11.0 on 2026-11-07. Sunset and havdalah match Jewish Calendar at the same location and elevation. A live candle lighting and havdalah transition has not been watched yet. The blueprints have run only in tests, with mocked services, not on real speakers or lights.

## License

MIT
