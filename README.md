# Zmanim and Shabbat for Home Assistant

A small custom integration that gives you two devices: today's zmanim, and whether Shabbat or Yom Tov is in effect. It is a simpler alternative to the built-in Jewish Calendar integration, and it can run alongside it. The calculations come from the [hdate](https://github.com/py-libhdate/py-libhdate) library, which Jewish Calendar also uses.

Treat the times as a convenience. Check anything halachically important against your own calendar or rabbi.

## What you get

**Zmanim** device: one timestamp sensor for each time you select, such as `sensor.zmanim_shkia`. All 18 of hdate's times are available. Eight are selected by default: Netz HaChama, Sof Zman Shema and Tefilla (GRA), Chatzot, Mincha Gedola, Plag HaMincha, Shkia and Tzeit HaKochavim (Shabbat).

**Shabbat and Yom Tov** device:

| Entity | Meaning |
|---|---|
| `binary_sensor.shabbat_and_yom_tov_in_effect` | On from candle lighting until havdalah, across multi-day stretches |
| `sensor.shabbat_and_yom_tov_next_candle_lighting` | The next candle lighting still to come, including second-night candles |
| `sensor.shabbat_and_yom_tov_next_havdalah` | The next havdalah still to come, at the end of the stretch |

The two "next" sensors never show a time that has passed. Jewish Calendar's `upcoming` sensors keep the past time until midnight on Saturday night.

## Install

Copy `custom_components/zmanim_shabbat` to `/config/custom_components/`, or add this repository to HACS as a custom repository. Restart Home Assistant, then add **Zmanim and Shabbat** under Settings → Devices & services.

## Settings

Set these during setup, and change them later under Configure.

- **Candle lighting:** minutes before sunset. The default is 18. Many in Jerusalem use 40.
- **Havdalah:** minutes after sunset. 0, the default, uses three stars instead.
- **Outside Israel:** two-day Yom Tov. Defaults to on unless Home Assistant's country is Israel.
- **Zmanim to show:** deselecting one removes its sensor.

Location and time zone come from Home Assistant. After changing them, reload the integration.

## Test status

Date: 2026-11-07. `uv sync --python 3.13 && .venv/bin/pytest` passes on Home Assistant 2026.2.3 with hdate 1.2.2.

Not yet run on a live Home Assistant installation.

## License

MIT
