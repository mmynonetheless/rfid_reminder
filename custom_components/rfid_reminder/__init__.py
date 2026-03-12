"""Init for RFID Reminder integration."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from . import config_flow
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_NAME,
    EVENT_HOMEASSISTANT_STARTED,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_LAST_CLEARED,
    ATTR_LAST_TRIGGERED,
    ATTR_NEXT_REMINDER,
    ATTR_REGISTERED_TAG,
    ATTR_REMINDER_ACTIVE,
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
    EVENT_RFID_TAG_SCANNED,
    EVENT_REMINDER_CLEARED,
    EVENT_REMINDER_TRIGGERED,
    SERVICE_CLEAR_REMINDER,
    SERVICE_REGISTER_TAG,
    SERVICE_TRIGGER_REMINDER,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_REMINDER_INTERVAL, default=DEFAULT_INTERVAL): vol.Coerce(float),
                vol.Optional(CONF_ALERT_VOLUME, default=DEFAULT_ALERT_VOLUME): cv.small_float,
                vol.Optional(CONF_ALERT_DURATION, default=DEFAULT_ALERT_DURATION): cv.positive_int,
                vol.Optional(CONF_ALERT_SOUND, default=DEFAULT_ALERT_SOUND): cv.string,
                vol.Optional(CONF_MEDIA_PLAYERS, default=[]): vol.All(cv.ensure_list, [cv.entity_id]),
                vol.Optional(CONF_PHONE_NUMBERS, default=[]): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_RFID_TAG, default=""): cv.string,
                vol.Optional(CONF_CUSTOM_MESSAGE, default=DEFAULT_CUSTOM_MESSAGE): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the RFID Reminder component."""
    hass.data.setdefault(DOMAIN, {})
    
    if DOMAIN in config:
        hass.data[DOMAIN]["config"] = config[DOMAIN]
    
    # Register services
    async def trigger_reminder(call: ServiceCall) -> None:
        """Trigger the reminder."""
        entity_id = call.data.get(CONF_ENTITY_ID)
        await async_trigger_reminder(hass, entity_id)
    
    async def clear_reminder(call: ServiceCall) -> None:
        """Clear the reminder."""
        entity_id = call.data.get(CONF_ENTITY_ID)
        await async_clear_reminder(hass, entity_id)
    
    async def register_tag(call: ServiceCall) -> None:
        """Register an RFID tag."""
        entity_id = call.data.get(CONF_ENTITY_ID)
        tag = call.data.get("tag")
        await async_register_tag(hass, entity_id, tag)
    
    hass.services.async_register(DOMAIN, SERVICE_TRIGGER_REMINDER, trigger_reminder)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_REMINDER, clear_reminder)
    hass.services.async_register(DOMAIN, SERVICE_REGISTER_TAG, register_tag)
    
    # Listen for RFID tag scans
    @callback
    async def handle_tag_scanned(event):
        """Handle RFID tag scanned event."""
        tag_id = event.data.get("tag_id")
        _LOGGER.debug("RFID tag scanned: %s", tag_id)
        
        # Find which reminder this tag belongs to
        for entity_id, data in hass.data[DOMAIN].items():
            if isinstance(data, dict) and data.get("registered_tag") == tag_id:
                await async_clear_reminder(hass, entity_id)
                hass.bus.async_fire(
                    EVENT_RFID_TAG_SCANNED,
                    {"tag_id": tag_id, "entity_id": entity_id}
                )
                break
    
    hass.bus.async_listen("tag_scanned", handle_tag_scanned)
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Reminder from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Create reminder entity
    entity = RFIDReminderEntity(hass, entry)
    await entity.async_added_to_hass()
    
    # Add to hass data
    hass.data[DOMAIN][entry.entry_id] = entity
    
    # Forward setup to sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True

async def async_trigger_reminder(hass: HomeAssistant, entity_id: str) -> None:
    """Trigger a reminder."""
    # Find the entity
    for entry_id, entity in hass.data[DOMAIN].items():
        if isinstance(entity, RFIDReminderEntity) and entity.entity_id == entity_id:
            await entity.async_trigger_reminder()
            break

async def async_clear_reminder(hass: HomeAssistant, entity_id: str) -> None:
    """Clear a reminder."""
    for entry_id, entity in hass.data[DOMAIN].items():
        if isinstance(entity, RFIDReminderEntity) and entity.entity_id == entity_id:
            await entity.async_clear_reminder()
            break

async def async_register_tag(hass: HomeAssistant, entity_id: str, tag: str) -> None:
    """Register an RFID tag."""
    for entry_id, entity in hass.data[DOMAIN].items():
        if isinstance(entity, RFIDReminderEntity) and entity.entity_id == entity_id:
            await entity.async_register_tag(tag)
            break

class RFIDReminderEntity(Entity):
    """Representation of a RFID Reminder entity."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the reminder."""
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}"
        self._attr_name = entry.data.get(CONF_NAME, "RFID Reminder")
        
        # State
        self._active = False
        self._last_triggered = None
        self._last_cleared = None
        self._next_reminder = None
        self._registered_tag = entry.data.get(CONF_RFID_TAG, "")
        
        # Configuration
        self._interval = entry.data.get(CONF_REMINDER_INTERVAL, DEFAULT_INTERVAL)
        self._volume = entry.data.get(CONF_ALERT_VOLUME, DEFAULT_ALERT_VOLUME)
        self._duration = entry.data.get(CONF_ALERT_DURATION, DEFAULT_ALERT_DURATION)
        self._sound = entry.data.get(CONF_ALERT_SOUND, DEFAULT_ALERT_SOUND)
        self._media_players = entry.data.get(CONF_MEDIA_PLAYERS, [])
        self._phone_numbers = entry.data.get(CONF_PHONE_NUMBERS, [])
        self._message = entry.data.get(CONF_CUSTOM_MESSAGE, DEFAULT_CUSTOM_MESSAGE)
        
        # Timer
        self._unsub_timer = None
        
    @property
    def state(self):
        """Return the state."""
        return STATE_ON if self._active else "off"
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional attributes."""
        return {
            ATTR_REMINDER_ACTIVE: self._active,
            ATTR_LAST_TRIGGERED: self._last_triggered,
            ATTR_LAST_CLEARED: self._last_cleared,
            ATTR_NEXT_REMINDER: self._next_reminder,
            ATTR_REGISTERED_TAG: self._registered_tag,
            "interval_hours": self._interval,
            "volume": self._volume,
            "duration_seconds": self._duration,
            "alert_sound": self._sound,
            "media_players": self._media_players,
            "phone_numbers": self._phone_numbers,
            "custom_message": self._message,
        }
    
    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Schedule first reminder
        await self._schedule_next_reminder()
        
    async def async_will_remove_from_hass(self):
        """When entity is removed from hass."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
    
    async def _schedule_next_reminder(self):
        """Schedule the next reminder."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        
        now = dt_util.utcnow()
        next_time = now + timedelta(hours=self._interval)
        self._next_reminder = next_time.isoformat()
        
        self._unsub_timer = async_track_point_in_time(
            self.hass, self._reminder_callback, next_time
        )
        
        self.async_write_ha_state()
    
    async def _reminder_callback(self, now):
        """Callback for reminder time."""
        await self.async_trigger_reminder()
        await self._schedule_next_reminder()
    
    async def async_trigger_reminder(self):
        """Trigger the reminder."""
        if self._active:
            return
        
        self._active = True
        self._last_triggered = dt_util.utcnow().isoformat()
        
        # Fire event
        self.hass.bus.async_fire(
            EVENT_REMINDER_TRIGGERED,
            {"entity_id": self.entity_id, "time": self._last_triggered}
        )
        
        # Start alert loop
        self.hass.async_create_task(self._alert_loop())
        
        self.async_write_ha_state()
        _LOGGER.info("Reminder triggered for %s", self.entity_id)
    
    async def _alert_loop(self):
        """Loop alerts while reminder is active."""
        while self._active:
            # Play on media players
            for player in self._media_players:
                await self._play_on_media_player(player)
            
            # Notify phones
            for phone in self._phone_numbers:
                await self._notify_phone(phone)
            
            # Wait before next alert
            await asyncio.sleep(self._duration)
    
    async def _play_on_media_player(self, player_entity):
        """Play alert on a media player."""
        try:
            # Set volume
            await self.hass.services.async_call(
                "media_player",
                "volume_set",
                {"entity_id": player_entity, "volume_level": self._volume}
            )
            
            # Play sound
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": player_entity,
                    "media_content_id": self._sound,
                    "media_content_type": "music"
                }
            )
            _LOGGER.debug("Played alert on %s", player_entity)
        except Exception as e:
            _LOGGER.error("Failed to play on %s: %s", player_entity, str(e))
    
    async def _notify_phone(self, phone_number):
        """Send notification to phone."""
        try:
            await self.hass.services.async_call(
                "notify",
                "notify",
                {
                    "title": "RFID Reminder Alert",
                    "message": f"{self._message}\n\nPlease scan your RFID tag to stop this reminder.",
                    "target": phone_number,
                    "data": {
                        "push": {
                            "sound": "default",
                            "critical": 1,
                            "volume": int(self._volume * 100)
                        }
                    }
                }
            )
            _LOGGER.debug("Notified %s", phone_number)
        except Exception as e:
            _LOGGER.error("Failed to notify %s: %s", phone_number, str(e))
    
    async def async_clear_reminder(self):
        """Clear the reminder."""
        if not self._active:
            return
        
        self._active = False
        self._last_cleared = dt_util.utcnow().isoformat()
        
        # Stop all media players
        for player in self._media_players:
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "media_stop",
                    {"entity_id": player}
                )
            except Exception as e:
                _LOGGER.error("Failed to stop %s: %s", player, str(e))
        
        # Fire event
        self.hass.bus.async_fire(
            EVENT_REMINDER_CLEARED,
            {"entity_id": self.entity_id, "time": self._last_cleared}
        )
        
        self.async_write_ha_state()
        _LOGGER.info("Reminder cleared for %s", self.entity_id)
    
    async def async_register_tag(self, tag: str):
        """Register a new RFID tag."""
        self._registered_tag = tag
        self.async_write_ha_state()
        
        # Update config entry
        new_data = dict(self.entry.data)
        new_data[CONF_RFID_TAG] = tag
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        
        _LOGGER.info("Registered new RFID tag for %s: %s", self.entity_id, tag)
