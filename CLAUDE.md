# Zmanim-Shabbat-HA-Integration: notes for agents

Public Home Assistant custom integration, domain `zmanim_shabbat`, in `custom_components/zmanim_shabbat`. Installable through HACS as a custom repository (`hacs.json`); not in the default store (2026-11-07).

Release tier: small (`v1.0`, `v1.1`, ...). `manifest.json` `version` follows it.

## Design decisions (2026-11-07)

- Built from scratch on `hdate`, not forked from core `jewish_calendar`: the owner wanted a much simpler version, and reusing the `jewish_calendar` domain would override the core integration.
- One integration, two devices (Zmanim; Shabbat and Yom Tov), so both share one location and one set of offsets.
- `calc.py` has no Home Assistant imports. Keep date logic there, where it can be tested alone.
- The coordinator has no polling interval. It recalculates at the earliest of midnight, next candle lighting and next havdalah.
- "Next" means strictly after now. Core derives it from today's date, so its `upcoming` sensors show a past time until midnight on Saturday night.
- Location comes from `hass.config`, not the config entry. hdate 1.2.2's zmanim ignore altitude, so there is no elevation setting.
- `hdate` is a range, not a pin, so this can't fight the version core `jewish_calendar` pins (1.2.2 in HA 2026.11.0).
- Only `translations/en.json` exists; a `strings.json` is unused by custom integrations.

## Test

`uv sync --python 3.13 && .venv/bin/pytest`. The status section in README.md says what has not been tested live.
