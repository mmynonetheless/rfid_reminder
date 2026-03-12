"""Sensor platform for RFID Reminder."""
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_LAST_TRIGGERED, ATTR_LAST_CLEARED, ATTR_NEXT_REMINDER

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RFIDReminderSensor(coordinator, entry)])

class RFIDReminderSensor(CoordinatorEntity, Entity):
    """Representation of a RFID Reminder sensor."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_sensor"
        self._attr_name = f"{entry.data.get('name', 'RFID Reminder')} Status"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._coordinator.state

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {
            "last_triggered": self._coordinator._last_triggered,
            "last_cleared": self._coordinator._last_cleared,
            "next_reminder": self._coordinator._next_reminder,
            "registered_tag": self._coordinator._registered_tag,
        }
