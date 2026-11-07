# Zmanim-Shabbat-HA-Integration: notes for agents

Public Home Assistant custom integration, domain `zmanim_shabbat`, in `custom_components/zmanim_shabbat`. Installable through HACS as a custom repository (`hacs.json`); not in the default store (2026-11-07).

Release tier: small (`v1.0`, `v1.1`, ...). `manifest.json` `version` follows it.

## Design decisions (2026-11-07)

- Built from scratch on `hdate`, not forked from core `jewish_calendar`: the owner wanted a much simpler version, and reusing the `jewish_calendar` domain would override the core integration.
- One integration, two devices (Zmanim; Shabbat and Yom Tov), so both share one location and one set of offsets.
- `calc.py` has no Home Assistant imports. Keep date logic there, where it can be tested alone.
- The coordinator has no polling interval. It recalculates at the earliest of midnight and `Snapshot.next_update`: candle lighting, havdalah, fast start, fast end or sunset. Sunset is there because the Hebrew date and Chol HaMoed roll over then.
- "Next" means strictly after now. Core derives it from today's date, so its `upcoming` sensors show a past time until midnight on Saturday night.
- Location and elevation come from `hass.config`, not the config entry. Elevation must always be passed: hdate 1.2.2 uses it through astral, and `Location` defaults to 754 m (Jerusalem), which moved sunset 3 minutes and havdalah 4 at sea level. First install (v1.0, 2026-11-07) shipped that bug; it showed up only by comparing live values with core `jewish_calendar`, because the tests had no absolute times. Elevation 0 and 754 give different times, so changing it changes candle lighting too.
- Elevation stays at HA's value, which is 0 on the owner's instance. He decided on 2026-11-07 that setting his real elevation is too specific.
- `hdate` is a range, not a pin, so this can't fight the version core `jewish_calendar` pins (1.2.2 in HA 2026.11.0).
- `translations/en.json` and `he.json` are the owner's own names, in modern Israeli pronunciation; core's Ashkenazi forms were the reason for this. No other languages. A `strings.json` is unused by custom integrations.
- One time per zman, no rabbinic alternatives and no selection option (`const.ZMANIM`). The owner asked for this. `sensor.py` deletes registry entries not in `ZMANIM` or `SHABBAT_ENTITIES`, so a new entity key must be added there or it is removed at startup. Live entries still hold an unused `zmanim` option from v1.1.
- Candle lighting defaults to 40 within 15 km of central Jerusalem (`calc.default_candle_lighting_minutes`). It only prefills the form.
- hdate's holiday types don't match these concepts, confirmed against 2026-2027 dates. Yom Kippur is `YOM_TOV`, not `FAST_DAY`. Hoshana Raba and the last day of Pesach Chol HaMoed are `EREV_YOM_TOV`. So `_fast_window` and `_is_chol_hamoed` match by name. hdate has no fast start time, so `_fast_window` derives it.
- Candle lighting is before sunset on a day that isn't itself holy, so `_occasion` must look ahead. Test occasion at the candle lighting instant, not later that evening.
- Announcements use `tts.speak`, not prerecorded eSpeak clips: a blueprint is a single YAML file and can't carry audio, and the owner's Edge TTS sounds better. Per-zman announcements with an offset are deferred to a later release.
- Dashboard: `dashboard_config.py` builds it and has no Home Assistant imports. `panel.py` registers it. Blueprints exist only for automation, script and template (checked in the HA source). `DashboardsCollection` is a local variable in lovelace's `async_setup`, so an integration can't create a storage dashboard. `panel.py` instead subclasses `LovelaceConfig`, puts it in `hass.data[LOVELACE_DATA].dashboards` and registers the panel, which is an internal API: `LovelaceConfig` was identical in 2026.2 and 2026.11.0, but recheck it if the dashboard breaks after an upgrade. Core cards only, so no `card_mod` or Mushroom. Layout comes from the owner's `HA-Shabbat-Dashboard-0125` and his live `dashboard-shabbat`. Times use `entities` cards with `format`, because a tile shows a timestamp as relative. Regenerate `dashboards/shabbat.yaml` when the layout changes; a test compares them.
- `next_shabbat_*` are worked out from sunset, not hdate's `candle_lighting` and `havdalah`, which are empty on some days joining a Yom Tov.
- Tests need `home-assistant-frontend` at the version in HA's frontend manifest, because of the `frontend` dependency. Update it with `pytest-homeassistant-custom-component`.
- Blueprint tests load the real YAML with mocked services. Don't use `freezer` when a blueprint has a `delay`: frozen time hangs it.

## Test

`uv sync --python 3.13 && .venv/bin/pytest`. The status section in README.md says what has not been tested live.
