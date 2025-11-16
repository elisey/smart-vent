# Smart Ventilation Controller - Automation Examples

This document provides ready-to-use automation examples for the Smart Ventilation Controller component.

## Table of Contents

- [Button-Triggered Boost](#button-triggered-boost)
- [Schedule-Based Boost](#schedule-based-boost)
- [Lovelace UI Cards](#lovelace-ui-cards)
- [Notification Automations](#notification-automations)
- [Advanced Automations](#advanced-automations)

---

## Button-Triggered Boost

### Physical Button or Dashboard Button

Activate boost mode with a single button press, perfect for bathroom wall switches or Lovelace dashboard buttons.

```yaml
automation:
  - alias: "Ventilation - Boost on Button Press"
    description: "Activate boost mode when button is pressed"
    trigger:
      - platform: state
        entity_id: binary_sensor.bathroom_button
        to: "on"
    action:
      - service: smart_vent.force_boost
```

**Variation**: With custom duration (e.g., 30 minutes for longer showers)

```yaml
automation:
  - alias: "Ventilation - Extended Boost on Button"
    trigger:
      - platform: state
        entity_id: binary_sensor.bathroom_button
        to: "on"
    action:
      - service: smart_vent.force_boost
```

### Dashboard Button Card

Add this to your Lovelace dashboard:

```yaml
type: button
tap_action:
  action: call-service
  service: smart_vent.force_boost
name: Boost Ventilation
icon: mdi:fan-plus
show_state: false
```

---

## Schedule-Based Boost

### Morning Shower Time

Automatically activate boost before typical morning shower times.

```yaml
automation:
  - alias: "Ventilation - Morning Shower Boost"
    description: "Boost ventilation during morning shower hours"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.shelly_input_0
        state: "on"
      - condition: state
        entity_id: binary_sensor.shelly_input_1
        state: "off"
    action:
      - service: smart_vent.force_boost
```

**Notes**:
- Only activates if switch is in MID mode (input_0=on, input_1=off)
- Respects user preference to keep fan in LOW mode if switched there

### Weekend Extended Boost

Longer boost duration on weekends when family uses bathroom more.

```yaml
automation:
  - alias: "Ventilation - Weekend Extended Boost"
    trigger:
      - platform: time
        at: "08:00:00"
      - platform: time
        at: "19:00:00"
    condition:
      - condition: time
        weekday:
          - sat
          - sun
    action:
      - service: smart_vent.force_boost
```

### After Cooking

Activate boost after detecting cooking activity (requires cooking sensor).

```yaml
automation:
  - alias: "Ventilation - Post-Cooking Boost"
    trigger:
      - platform: state
        entity_id: binary_sensor.stove_activity
        to: "off"
        for:
          minutes: 5
    action:
      - service: smart_vent.force_boost
```

---

## Lovelace UI Cards

### Comprehensive Control Card

A complete control card with all ventilation entities and controls.

```yaml
type: entities
title: Bathroom Ventilation
entities:
  - entity: fan.real_fan
    name: Physical Fan
  - entity: binary_sensor.smart_vent_auto_boost
    name: Auto-Boost Status
  - entity: sensor.temperature_humidity_sensor_9970_humidity
    name: Humidity Level
  - type: divider
  - entity: binary_sensor.shelly_input_0
    name: Switch Input 0
  - entity: binary_sensor.shelly_input_1
    name: Switch Input 1
  - type: section
    label: Controls
  - type: button
    name: Force Boost
    icon: mdi:fan-plus
    tap_action:
      action: call-service
      service: smart_vent.force_boost
```

### Status-Only Card

Minimal card showing current status.

```yaml
type: glance
title: Ventilation Status
entities:
  - entity: fan.real_fan
    name: Fan Speed
  - entity: binary_sensor.smart_vent_auto_boost
    name: Auto-Boost
  - entity: sensor.temperature_humidity_sensor_9970_humidity
    name: Humidity
show_state: true
```

### Mode Selection Card

Quick mode switching with buttons.

```yaml
type: horizontal-stack
cards:
  - type: button
    tap_action:
      action: call-service
      service: smart_vent.set_mode
      service_data:
        mode: low
    name: Low
    icon: mdi:fan-speed-1
  - type: button
    tap_action:
      action: call-service
      service: smart_vent.set_mode
      service_data:
        mode: mid
    name: Mid
    icon: mdi:fan-speed-2
  - type: button
    tap_action:
      action: call-service
      service: smart_vent.set_mode
      service_data:
        mode: boost
    name: Boost
    icon: mdi:fan-speed-3
```

### Auto-Boost Indicator with Time Remaining

Card showing boost status with remaining time.

```yaml
type: markdown
content: >
  {% if is_state('binary_sensor.smart_vent_auto_boost', 'on') %}
    ## 🔥 Auto-Boost Active

    **Time Remaining:** {{ state_attr('binary_sensor.smart_vent_auto_boost', 'time_remaining') }} minutes

    **Boosts Today:** {{ state_attr('binary_sensor.smart_vent_auto_boost', 'count_today') }} / {{ state_attr('binary_sensor.smart_vent_auto_boost', 'max_per_day') }}
  {% else %}
    ## ✅ Normal Operation

    **Boosts Available:** {{ state_attr('binary_sensor.smart_vent_auto_boost', 'max_per_day') | int - state_attr('binary_sensor.smart_vent_auto_boost', 'count_today') | int }}
  {% endif %}
title: Ventilation Boost Status
```

---

## Notification Automations

### Auto-Boost Activation Alert

Get notified when automatic boost activates.

```yaml
automation:
  - alias: "Ventilation - Auto-Boost Notification"
    description: "Send notification when auto-boost activates"
    trigger:
      - platform: state
        entity_id: binary_sensor.smart_vent_auto_boost
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Ventilation Boost Activated"
          message: "High humidity detected ({{ states('sensor.temperature_humidity_sensor_9970_humidity') }}%). Boost mode activated for 20 minutes."
          data:
            notification_icon: mdi:fan-plus
```

### Daily Limit Reached Warning

Alert when auto-boost daily limit is reached (requires template sensor).

First, create a template sensor to detect when limit is reached:

```yaml
template:
  - binary_sensor:
      - name: "Smart Vent Boost Limit Reached"
        unique_id: smart_vent_boost_limit_reached
        state: >
          {{ state_attr('binary_sensor.smart_vent_auto_boost', 'count_today') | int >=
             state_attr('binary_sensor.smart_vent_auto_boost', 'max_per_day') | int }}
```

Then create the automation:

```yaml
automation:
  - alias: "Ventilation - Boost Limit Warning"
    trigger:
      - platform: state
        entity_id: binary_sensor.smart_vent_boost_limit_reached
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Ventilation Boost Limit Reached"
          message: "Daily boost limit (5) reached. Manual boost still available via force_boost service."
```

### Humidity Threshold Warning

Alert when humidity is high but auto-boost can't activate.

```yaml
automation:
  - alias: "Ventilation - High Humidity Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.temperature_humidity_sensor_9970_humidity
        above: 80
        for:
          minutes: 5
    condition:
      - condition: state
        entity_id: binary_sensor.smart_vent_auto_boost
        state: "off"
    action:
      - service: notify.mobile_app
        data:
          title: "High Humidity Detected"
          message: "Humidity is {{ states('sensor.temperature_humidity_sensor_9970_humidity') }}% but auto-boost is not active. Check ventilation settings."
          data:
            actions:
              - action: FORCE_BOOST
                title: "Activate Boost"
```

Handle the notification action:

```yaml
automation:
  - alias: "Ventilation - Handle Boost Notification Action"
    trigger:
      - platform: event
        event_type: mobile_app_notification_action
        event_data:
          action: FORCE_BOOST
    action:
      - service: smart_vent.force_boost
```

---

## Advanced Automations

### Adaptive Boost Duration Based on Humidity

Adjust boost duration based on humidity level (requires manual service calls).

```yaml
automation:
  - alias: "Ventilation - Adaptive Boost Duration"
    trigger:
      - platform: numeric_state
        entity_id: sensor.temperature_humidity_sensor_9970_humidity
        above: 80
    condition:
      - condition: state
        entity_id: binary_sensor.shelly_input_0
        state: "on"
      - condition: state
        entity_id: binary_sensor.shelly_input_1
        state: "off"
      - condition: state
        entity_id: binary_sensor.smart_vent_auto_boost
        state: "off"
    action:
      - service: smart_vent.force_boost
```

**Note**: The component currently uses a fixed boost duration. This example triggers boost but doesn't customize duration.

### Presence-Based Boost

Only allow auto-boost when someone is home.

```yaml
automation:
  - alias: "Ventilation - Disable Auto-Boost When Away"
    trigger:
      - platform: state
        entity_id: binary_sensor.someone_home
        to: "off"
    action:
      - service: smart_vent.set_mode
        data:
          mode: low

  - alias: "Ventilation - Re-enable Auto-Boost When Home"
    trigger:
      - platform: state
        entity_id: binary_sensor.someone_home
        to: "on"
    action:
      - service: smart_vent.set_mode
        data:
          mode: mid
```

### Coordinated Bathroom Fan and Light

Coordinate ventilation with bathroom light usage.

```yaml
automation:
  - alias: "Bathroom - Boost When Light On for Extended Period"
    trigger:
      - platform: state
        entity_id: light.bathroom
        to: "on"
        for:
          minutes: 5
    action:
      - service: smart_vent.force_boost

  - alias: "Bathroom - Return to Mid When Light Off"
    trigger:
      - platform: state
        entity_id: light.bathroom
        to: "off"
        for:
          minutes: 10
    condition:
      - condition: numeric_state
        entity_id: sensor.temperature_humidity_sensor_9970_humidity
        below: 70
    action:
      - service: smart_vent.set_mode
        data:
          mode: mid
```

### Energy-Saving Night Mode

Reduce ventilation at night to save energy.

```yaml
automation:
  - alias: "Ventilation - Night Mode"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.temperature_humidity_sensor_9970_humidity
        below: 70
    action:
      - service: smart_vent.set_mode
        data:
          mode: low

  - alias: "Ventilation - Resume Normal Mode"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: smart_vent.set_mode
        data:
          mode: mid
```

### Monthly Boost Usage Statistics

Track boost usage over time (requires helper entities).

Create a counter helper in `configuration.yaml`:

```yaml
counter:
  ventilation_boost_count:
    name: Total Boost Activations
    icon: mdi:counter
```

Automation to increment:

```yaml
automation:
  - alias: "Ventilation - Count Boost Activations"
    trigger:
      - platform: state
        entity_id: binary_sensor.smart_vent_auto_boost
        to: "on"
    action:
      - service: counter.increment
        target:
          entity_id: counter.ventilation_boost_count
```

Monthly reset:

```yaml
automation:
  - alias: "Ventilation - Monthly Counter Reset"
    trigger:
      - platform: time
        at: "00:00:00"
    condition:
      - condition: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: counter.reset
        target:
          entity_id: counter.ventilation_boost_count
```

---

## Testing Your Automations

### Test Auto-Boost Activation

1. Set switch to MID mode:
   ```yaml
   service: script.set_switch_mid
   ```

2. Simulate high humidity:
   ```yaml
   service: input_number.set_value
   target:
     entity_id: input_number.test_humidity
   data:
     value: 85
   ```

3. Wait for check_interval (5 seconds in your config)

4. Verify:
   - `fan.real_fan` speed is 100%
   - `binary_sensor.smart_vent_auto_boost` is ON

### Test Force Boost Service

```yaml
service: smart_vent.force_boost
```

Verify:
- Fan immediately goes to 100%
- Binary sensor activates
- Returns to previous mode after configured duration

### Test Mode Switching

```yaml
# Switch to each mode and verify fan speed
service: smart_vent.set_mode
data:
  mode: low  # Expect 30%

service: smart_vent.set_mode
data:
  mode: mid  # Expect 52%

service: smart_vent.set_mode
data:
  mode: boost  # Expect 100%
```

---

## Tips and Best Practices

1. **Physical Switch Priority**: Remember that the physical switch position will override service calls on the next state update. For permanent changes, use the physical switch.

2. **Daily Limits**: The `force_boost` service bypasses daily auto-boost limits, use it for genuine emergencies only.

3. **Testing Safely**: Use the development environment's test helpers (`input_number.test_humidity`, `input_boolean.shelly_input_*`) before deploying to production.

4. **Notification Spam**: Add conditions to notifications to prevent excessive alerts (e.g., `for: minutes: 5`).

5. **Energy Efficiency**: Schedule low mode during times when nobody is home or during sleeping hours.

6. **Monitoring**: Track boost usage patterns to optimize your `max_boosts_per_day` and `auto_boost_duration` settings.

---

## Need More Help?

- **[Main Documentation](README.md)** - Component overview and configuration
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[FAQ](FAQ.md)** - Frequently asked questions
- **[GitHub Issues](https://github.com/elisey/smart-vent/issues)** - Report bugs or request features
