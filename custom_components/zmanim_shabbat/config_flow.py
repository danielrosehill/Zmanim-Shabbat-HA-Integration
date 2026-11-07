"""Config flow. Setup and Configure show the same form."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .calc import default_candle_lighting_minutes
from .const import (
    CONF_CANDLE_LIGHTING_MINUTES,
    CONF_DASHBOARD,
    CONF_DIASPORA,
    DASHBOARD_SECTIONS,
    CONF_HAVDALAH_MINUTES,
    DEFAULT_HAVDALAH_MINUTES,
    DOMAIN,
)


def _minutes(maximum: int) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=0,
            max=maximum,
            step=1,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement="min",
        )
    )


def _schema(hass: HomeAssistant, current: dict[str, Any]) -> vol.Schema:
    defaults = {
        CONF_DIASPORA: hass.config.country != "IL",
        CONF_CANDLE_LIGHTING_MINUTES: default_candle_lighting_minutes(
            hass.config.latitude, hass.config.longitude
        ),
        CONF_HAVDALAH_MINUTES: DEFAULT_HAVDALAH_MINUTES,
        CONF_DASHBOARD: True,
        **dict.fromkeys(DASHBOARD_SECTIONS, True),
    } | current
    return vol.Schema(
        {
            vol.Required(
                CONF_CANDLE_LIGHTING_MINUTES,
                default=defaults[CONF_CANDLE_LIGHTING_MINUTES],
            ): _minutes(60),
            vol.Required(
                CONF_HAVDALAH_MINUTES, default=defaults[CONF_HAVDALAH_MINUTES]
            ): _minutes(120),
            vol.Required(CONF_DIASPORA, default=defaults[CONF_DIASPORA]): BooleanSelector(),
            **{
                vol.Required(key, default=defaults[key]): BooleanSelector()
                for key in (CONF_DASHBOARD, *DASHBOARD_SECTIONS)
            },
        }
    )


class ZmanimShabbatConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the settings form."""
        if user_input is not None:
            return self.async_create_entry(
                title="Zmanim and Shabbat", data={}, options=user_input
            )
        return self.async_show_form(step_id="user", data_schema=_schema(self.hass, {}))

    @staticmethod
    @callback
    def async_get_options_flow(_entry: ConfigEntry) -> "ZmanimShabbatOptionsFlow":
        """Return the options flow."""
        return ZmanimShabbatOptionsFlow()


class ZmanimShabbatOptionsFlow(OptionsFlowWithReload):
    """Handle Configure."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the settings form."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self.hass, dict(self.config_entry.options)),
        )
