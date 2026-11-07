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
    SelectSelector,
    SelectSelectorConfig,
)

from .const import (
    ALL_ZMANIM,
    CONF_CANDLE_LIGHTING_MINUTES,
    CONF_DIASPORA,
    CONF_HAVDALAH_MINUTES,
    CONF_ZMANIM,
    DEFAULT_CANDLE_LIGHTING_MINUTES,
    DEFAULT_HAVDALAH_MINUTES,
    DEFAULT_ZMANIM,
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
        CONF_CANDLE_LIGHTING_MINUTES: DEFAULT_CANDLE_LIGHTING_MINUTES,
        CONF_HAVDALAH_MINUTES: DEFAULT_HAVDALAH_MINUTES,
        CONF_ZMANIM: DEFAULT_ZMANIM,
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
            vol.Required(CONF_ZMANIM, default=defaults[CONF_ZMANIM]): SelectSelector(
                SelectSelectorConfig(
                    options=list(ALL_ZMANIM), multiple=True, translation_key="zmanim"
                )
            ),
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
