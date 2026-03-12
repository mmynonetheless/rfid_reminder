# RFID Reminder System for Home Assistant

[![HACS Custom][hacs-shield]][hacs]
[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

A customizable reminder system that triggers audible alerts on media players and phone notifications every X hours, only stopping when a registered RFID tag is scanned.

## Features

- ⏰ **Customizable Interval**: Set reminder frequency from 30 minutes to 24 hours
- 🔊 **Multiple Alert Types**: Plays on all your media players
- 📱 **Phone Notifications**: Critical alerts sent to designated phones
- 🏷️ **RFID Integration**: Works with your existing RFID scanner
- 🎨 **Fully Configurable**: Volume, duration, custom messages
- 🔔 **Event System**: Fires events you can use in automations
- 🖥️ **Beautiful Dashboard**: Ready-to-use Lovelace cards

## Installation

### HACS Installation (Recommended)
1. Make sure [HACS](https://hacs.xyz/) is installed
2. Go to HACS → Integrations
3. Click the three dots in the top right → "Custom repositories"
4. Add this repository URL with category "Integration"
5. Click "Explore & Download Repositories"
6. Search for "RFID Reminder" and download
7. Restart Home Assistant

### Manual Installation
1. Download the `rfid_reminder` folder
2. Copy it to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### UI Configuration (Recommended)
1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "RFID Reminder"
4. Fill in the configuration form:
   - **Name**: A friendly name for this reminder
   - **Reminder Interval**: Hours between reminders
   - **Alert Volume**: Volume level (0.1-1.0)
   - **Alert Duration**: How long to loop alerts (seconds)
   - **Alert Sound**: Path to audio file
   - **Media Players**: Select which speakers to use
   - **Phone Numbers**: Comma-separated phone numbers
   - **Custom Message**: Your reminder message
   - **Registered RFID Tag**: Initial tag (can be set later)

### YAML Configuration (Advanced)
```yaml
# configuration.yaml
rfid_reminder:
  reminder_interval: 4
  alert_volume: 0.7
  alert_duration: 30
  alert_sound: "/media/local/alarm.mp3"
  media_players:
    - media_player.living_room
    - media_player.bedroom
  phone_numbers:
    - "+1234567890"
  custom_message: "Time for your medication!"
  rfid_tag: "1234567890"
