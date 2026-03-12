"""Constants for the RFID Reminder integration."""

DOMAIN = "rfid_reminder"
VERSION = "1.0.0"

# Configuration keys
CONF_REMINDER_INTERVAL = "reminder_interval"
CONF_ALERT_VOLUME = "alert_volume"
CONF_ALERT_DURATION = "alert_duration"
CONF_ALERT_SOUND = "alert_sound"
CONF_MEDIA_PLAYERS = "media_players"
CONF_PHONE_NUMBERS = "phone_numbers"
CONF_RFID_TAG = "rfid_tag"
CONF_CUSTOM_MESSAGE = "custom_message"

# Default values
DEFAULT_INTERVAL = 4
DEFAULT_VOLUME = 0.7
DEFAULT_DURATION = 30
DEFAULT_MESSAGE = "Time for your reminder!"
DEFAULT_SOUND = "/media/local/alarm.mp3"

# Event types
EVENT_RFID_TAG_SCANNED = "rfid_reminder_tag_scanned"
EVENT_REMINDER_TRIGGERED = "rfid_reminder_triggered"
EVENT_REMINDER_CLEARED = "rfid_reminder_cleared"

# Services
SERVICE_TRIGGER_REMINDER = "trigger_reminder"
SERVICE_CLEAR_REMINDER = "clear_reminder"
SERVICE_REGISTER_TAG = "register_tag"

# Attributes
ATTR_REMINDER_ACTIVE = "reminder_active"
ATTR_LAST_TRIGGERED = "last_triggered"
ATTR_LAST_CLEARED = "last_cleared"
ATTR_REGISTERED_TAG = "registered_tag"
ATTR_NEXT_REMINDER = "next_reminder"
