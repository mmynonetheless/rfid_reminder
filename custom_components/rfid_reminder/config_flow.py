"""Config flow for RFID Reminder integration."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    CONF_ALERT_DURATION,
    CONF_ALERT_SOUND,
    CONF_ALERT_VOLUME,
    CONF_CUSTOM_MESSAGE,
    CONF_MEDIA_PLAYERS,
    CONF_PHONE_NUMBERS,
    CONF_REMINDER_INTERVAL,
    CONF_RFID_TAG,
    DEFAULT_ALERT_DURATION,
    DEFAULT_ALERT_SOUND,
    DEFAULT_ALERT_VOLUME,
    DEFAULT_CUSTOM_MESSAGE,
    DEFAULT_INTERVAL,
    DOMAIN,
)

class RFIDReminderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RFID Reminder."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("name", "RFID Reminder"),
                data=user_input,
            )
        
        # Build schema
        schema = vol.Schema(
            {
                vol.Required("name", default="RFID Reminder"): str,
                vol.Optional(
                    CONF_REMINDER_INTERVAL, default=DEFAULT_INTERVAL
                ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=24)),
                vol.Optional(
                    CONF_ALERT_VOLUME, default=DEFAULT_ALERT_VOLUME
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
                vol.Optional(
                    CONF_ALERT_DURATION, default=DEFAULT_ALERT_DURATION
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                vol.Optional(CONF_ALERT_SOUND, default=DEFAULT_ALERT_SOUND): str,
                vol.Optional(CONF_MEDIA_PLAYERS, default=[]): EntitySelector(
                    EntitySelectorConfig(
                        domain="media_player",
                        multiple=True,
                    )
                ),
                vol.Optional(CONF_PHONE_NUMBERS, default=""): str,
                vol.Optional(CONF_CUSTOM_MESSAGE, default=DEFAULT_CUSTOM_MESSAGE): str,
                vol.Optional(CONF_RFID_TAG, default=""): str,
            }
        )
        
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        # Get current config
        config = self.config_entry.data
        
        # Build schema with current values
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_REMINDER_INTERVAL,
                    default=config.get(CONF_REMINDER_INTERVAL, DEFAULT_INTERVAL),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=24)),
                vol.Optional(
                    CONF_ALERT_VOLUME,
                    default=config.get(CONF_ALERT_VOLUME, DEFAULT_ALERT_VOLUME),
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
                vol.Optional(
                    CONF_ALERT_DURATION,
                    default=config.get(CONF_ALERT_DURATION, DEFAULT_ALERT_DURATION),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                vol.Optional(
                    CONF_ALERT_SOUND,
                    default=config.get(CONF_ALERT_SOUND, DEFAULT_ALERT_SOUND),
                ): str,
                vol.Optional(
                    CONF_MEDIA_PLAYERS,
                    default=config.get(CONF_MEDIA_PLAYERS, []),
                ): EntitySelector(
                    EntitySelectorConfig(
                        domain="media_player",
                        multiple=True,
                    )
                ),
                vol.Optional(
                    CONF_PHONE_NUMBERS,
                    default=config.get(CONF_PHONE_NUMBERS, ""),
                ): str,
                vol.Optional(
                    CONF_CUSTOM_MESSAGE,
                    default=config.get(CONF_CUSTOM_MESSAGE, DEFAULT_CUSTOM_MESSAGE),
                ): str,
                vol.Optional(
                    CONF_RFID_TAG,
                    default=config.get(CONF_RFID_TAG, ""),
                ): str,
            }
        )
        
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
