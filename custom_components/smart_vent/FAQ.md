# Smart Ventilation Controller - Frequently Asked Questions

Common questions and answers about the Smart Ventilation Controller component.

## Table of Contents

- [General Questions](#general-questions)
- [Auto-Boost Functionality](#auto-boost-functionality)
- [Configuration](#configuration)
- [Hardware and Compatibility](#hardware-and-compatibility)
- [Usage and Behavior](#usage-and-behavior)
- [Customization](#customization)
- [Advanced Topics](#advanced-topics)

---

## General Questions

### What does this component do?

The Smart Ventilation Controller integrates a physical 3-position switch with humidity-based automation for bathroom/kitchen ventilation. It provides:

- Manual control via physical switch (Low/Mid/Boost modes)
- Automatic boost when humidity exceeds 80% in mid mode
- Configurable daily limits and boost duration
- Priority-based control (manual overrides automatic)

### Do I need programming knowledge to use this?

Basic YAML knowledge is helpful for configuration. If you can edit `configuration.yaml` and create simple automations, you can use this component. See our [examples](EXAMPLES.md) for ready-to-use configurations.

### Is this component cloud-dependent?

No. The component operates entirely locally (`iot_class: local_polling`). No internet connection or external services required.

### What's the difference between this and Home Assistant's built-in fan integration?

Built-in fan integration provides basic on/off or speed control. This component adds:
- Physical switch integration with 3-position logic
- Automatic humidity-based boost triggering
- Daily boost limits and timeouts
- Priority management between manual and automatic control

---

## Auto-Boost Functionality

### How does auto-boost work?

When your physical switch is in **Mid position** and humidity exceeds **80%**:

1. Fan automatically increases to boost speed (100% by default)
2. Runs for configured duration (default 20 minutes)
3. Automatically returns to mid speed
4. Respects daily activation limit (default 5 per day)

**Requirements:**
- Switch must be in Mid mode (input_0=ON, input_1=OFF)
- Humidity must be > 80%
- Daily limit not exceeded
- No active auto-boost already running

### Why isn't auto-boost activating?

Common reasons:

1. **Switch not in Mid mode** - Auto-boost only works in Mid position
2. **Humidity below threshold** - Must be > 80%
3. **Daily limit reached** - Check `binary_sensor.smart_vent_auto_boost` attributes
4. **Sensor unavailable** - Verify humidity sensor is working
5. **Check interval not passed** - Wait for next update cycle

See [Troubleshooting - Auto-Boost Not Activating](TROUBLESHOOTING.md#auto-boost-not-activating) for detailed diagnostics.

### Can I change the humidity threshold?

Currently, the 80% threshold is hardcoded. This may be configurable in future versions.

**Workaround:** Create a custom automation that calls `force_boost` at your desired threshold:

```yaml
automation:
  - alias: "Custom Humidity Boost"
    trigger:
      - platform: numeric_state
        entity_id: sensor.temperature_humidity_sensor_9970_humidity
        above: 70  # Your custom threshold
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

### What's the difference between auto-boost and force_boost?

| Feature | Auto-Boost | Force Boost |
|---------|------------|-------------|
| Trigger | Automatic (humidity > 80%) | Manual (service call) |
| Daily Limit | Respects limit | Bypasses limit |
| Requires | Mid mode | Any mode |
| Cancellation | Switch movement cancels | Switch movement cancels |
| Use Case | Automatic daily operation | Emergency/manual override |

### Can I have unlimited auto-boost activations?

Yes, but not recommended. Set a high limit:

```yaml
smart_vent:
  # ... other config ...
  max_boosts_per_day: 999  # Effectively unlimited
```

**Why limits exist:** Prevents excessive fan wear, energy waste, and over-drying the air.

### Does auto-boost work when I'm away from home?

Yes, unless you create an automation to disable it. See [Examples - Presence-Based Boost](EXAMPLES.md#presence-based-boost) for how to disable when away.

---

## Configuration

### What are the minimum required configuration options?

```yaml
smart_vent:
  fan_entity: fan.your_fan
  humidity_sensor: sensor.your_humidity
  input_0: binary_sensor.switch_input_0
  input_1: binary_sensor.switch_input_1
```

All other parameters have sensible defaults.

### Can I customize the fan speeds for each mode?

Yes:

```yaml
smart_vent:
  # ... required fields ...
  speeds:
    low: 20      # 20% instead of default 30%
    mid: 60      # 60% instead of default 52%
    boost: 100   # Keep at 100% or reduce if needed
```

Speeds must be 0-100 (percentage).

### How often does the component check conditions?

Controlled by `check_interval` (default 20 seconds):

```yaml
smart_vent:
  # ... other config ...
  check_interval: 10  # Check every 10 seconds
```

**Note:** Component also responds immediately to switch and humidity sensor state changes via event listeners, so actual response is faster than the check interval.

### What happens during Home Assistant restart?

1. Component reads current physical switch position
2. Sets fan to corresponding speed
3. Resets all auto-boost states (count_today remains)
4. Resumes normal operation

**Important:** Active auto-boost does NOT persist across restarts. The component starts fresh based on current switch position.

### Can I change the auto-boost duration?

Yes:

```yaml
smart_vent:
  # ... other config ...
  auto_boost_duration: 30  # 30 minutes instead of default 20
```

Valid range: 1-120 minutes.

---

## Hardware and Compatibility

### What fan controllers are compatible?

Any fan entity that supports percentage speed control (0-100%):

**Recommended:**
- **Shelly Dimmer 2** - WiFi, reliable, easy integration
- **ESPHome** custom fan controller
- **Zigbee fan controllers** (various brands)
- **Z-Wave fan controllers** (various brands)

**Not compatible:**
- Simple on/off relays (no speed control)
- Fans with only preset speeds (low/medium/high) without percentage support

**How to verify:** Check if your fan has a `percentage` attribute in Developer Tools → States.

### What humidity sensors work?

Any Home Assistant humidity sensor entity:

**Popular options:**
- **Xiaomi Mijia LYWSD03MMC** (Bluetooth, affordable)
- **Aqara Humidity Sensor** (Zigbee, reliable)
- **Z-Wave humidity sensors** (various brands)
- **DHT22/BME280** via ESPHome
- **Template sensors** combining multiple inputs

**Requirements:**
- Entity provides numeric humidity value
- Unit of measurement is `%`
- Updates at least every 5 minutes

### Can I use this without a 3-position switch?

Not as designed. The component requires two binary inputs to determine mode.

**Alternatives:**

1. **Use separate buttons/switches:**
   - Create automations to call `smart_vent.set_mode` based on button presses
   - Won't have the same physical feedback as a 3-position switch

2. **Use only automation control:**
   - Set both inputs to a fixed state (e.g., both OFF for Low)
   - Control entirely via `set_mode` service calls
   - Physical switch will not reflect actual mode

3. **Use a rotary selector:**
   - Some rotary switches can be wired to provide binary outputs
   - Check switch specifications

### What is a 3-position switch and how do I wire it?

A 3-position switch has three distinct positions with different electrical connections.

**Example wiring for Shelly input:**

```
Position 1 (Low):   Both terminals open
Position 2 (Mid):   Terminal A closes → Input 0 = ON
Position 3 (Boost): Terminal B closes → Input 1 = ON
```

**Where to buy:**
- Search for "3-position toggle switch" or "3-position selector switch"
- Automotive switches often have this configuration
- Industrial selector switches (2-position + center-off or 3-position maintained)

**Wiring diagram:**
```
Switch Terminal A ──→ Shelly Input 0
Switch Terminal B ──→ Shelly Input 1
Common Ground    ──→ Shelly Ground
```

### Can I use multiple fans with one switch?

Not directly. The component controls one fan entity.

**Workaround:**

1. **Create a fan group:**
   ```yaml
   fan:
     - platform: group
       name: "Bathroom Fans"
       entities:
         - fan.bathroom_fan_1
         - fan.bathroom_fan_2
   ```

2. **Use the group in smart_vent config:**
   ```yaml
   smart_vent:
     fan_entity: fan.bathroom_fans
     # ... rest of config ...
   ```

All fans in the group will be controlled together.

---

## Usage and Behavior

### Why does my mode keep reverting to the switch position?

This is **intentional behavior**. The physical switch has priority.

The component is designed for **physical-switch-first control**:
- Physical switch determines the mode
- Service calls (`set_mode`) are temporary overrides
- On next update, mode returns to switch position

See [Troubleshooting - Mode Keeps Reverting](TROUBLESHOOTING.md#mode-keeps-reverting) for details.

### Can I control the fan from Home Assistant UI?

Yes, but with caveats:

- **`smart_vent.set_mode`** - Temporarily sets mode (reverts on next switch change)
- **`smart_vent.force_boost`** - Activates boost for configured duration
- **`fan.real_fan`** - Your physical fan entity still works independently

The virtual `fan.smart_vent` entity is read-only (status indicator).

### What happens if I move the switch during auto-boost?

Auto-boost is immediately canceled and fan switches to new position:

- **Switch to Low** → Auto-boost canceled, fan goes to 30%
- **Switch to Boost** → Auto-boost canceled, manual boost at 100%
- **Switch to Mid** → Auto-boost canceled, returns to 52%

### How do I know if auto-boost is active?

Check `binary_sensor.smart_vent_auto_boost`:

- **State:** `on` = active, `off` = inactive
- **Attributes:**
  - `time_remaining`: Minutes left in current boost
  - `count_today`: Activations used today
  - `max_per_day`: Daily limit

Create a Lovelace card to display this (see [Examples - Lovelace Cards](EXAMPLES.md#lovelace-ui-cards)).

### Can I manually extend an active auto-boost?

Not directly. Auto-boost runs for fixed duration.

**Workaround:**
1. Wait for auto-boost to end
2. Call `force_boost` again

Or:

1. Switch to Boost position (manual control)
2. Keep it there as long as needed
3. Switch back to Mid when done

### What happens at midnight?

The `count_today` counter resets to 0, allowing new auto-boost activations.

---

## Customization

### Can I add CO₂ or other sensors as triggers?

The component currently only monitors humidity.

**Workaround:** Create custom automations:

```yaml
automation:
  - alias: "Boost on High CO2"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bathroom_co2
        above: 1000
    action:
      - service: smart_vent.force_boost
```

### Can I create different speed profiles for different times of day?

Not within the component configuration.

**Workaround:** Use automations to temporarily change modes:

```yaml
# Night mode - reduce all speeds
automation:
  - alias: "Ventilation - Night Speed Reduction"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: smart_vent.set_mode
        data:
          mode: low
```

**Note:** This will be overridden when switch position changes.

### Can I get notifications when boost activates?

Yes! See [Examples - Notification Automations](EXAMPLES.md#notification-automations) for ready-to-use examples.

### Can I log boost activations to a spreadsheet/database?

Yes, using Home Assistant's built-in tools:

**Option 1: History Stats**
```yaml
sensor:
  - platform: history_stats
    name: Boost Activations Today
    entity_id: binary_sensor.smart_vent_auto_boost
    state: "on"
    type: count
    start: "{{ now().replace(hour=0, minute=0, second=0) }}"
    end: "{{ now() }}"
```

**Option 2: InfluxDB/PostgreSQL**
Enable the recorder integration and export to your database of choice.

**Option 3: Google Sheets**
Use AppDaemon or Node-RED to log to Google Sheets when boost activates.

---

## Advanced Topics

### How does the priority system work?

Priority from highest to lowest:

1. **Manual Boost** (physical switch in boost position)
   - Immediately cancels auto-boost
   - Full manual control

2. **Auto-Boost** (humidity trigger in mid mode)
   - Temporary boost with timeout
   - Only activates in mid mode

3. **Manual Mid/Low** (physical switch position)
   - Cancels auto-boost
   - Sets corresponding speed

### What is the DataUpdateCoordinator pattern?

The component uses Home Assistant's `DataUpdateCoordinator` for efficient state management:

- **Event-driven updates:** Instant response to switch/humidity changes
- **Periodic updates:** Regular checks for timeout/limit conditions
- **Debouncing:** Prevents rapid repeated updates
- **Error handling:** Graceful degradation when sensors fail

Users don't need to understand this - it just makes the component efficient and responsive.

### Can I use this component as a template for other projects?

Yes! The component is well-structured and follows Home Assistant best practices:

- Clear separation of concerns (coordinator, entities, services)
- Comprehensive error handling
- Extensive logging
- Configuration validation

Feel free to fork and adapt for your use case (MIT license).

### How do I contribute improvements?

Contributions welcome! See the [GitHub repository](https://github.com/elisey/smart-vent):

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

**Improvement ideas:**
- Configurable humidity threshold
- Multiple sensor support (CO₂, temperature)
- Different speed profiles by time/day
- Machine learning-based auto-boost timing

### What's planned for future versions?

**Under consideration:**

- Configuration Flow (UI-based setup instead of YAML)
- Configurable humidity threshold
- Support for multiple trigger conditions (CO₂, temperature)
- Time-based speed profiles
- Usage statistics and analytics
- HACS default repository inclusion

**Check [GitHub Issues](https://github.com/elisey/smart-vent/issues) for current roadmap.**

### How do I debug custom automations?

1. **Enable debug logging** for both the component and automation:
   ```yaml
   logger:
     logs:
       custom_components.smart_vent: debug
       homeassistant.components.automation: debug
   ```

2. **Use Developer Tools → Events:**
   - Listen to `state_changed` events for your entities
   - Watch for automation triggers

3. **Check automation traces:**
   - Settings → Automations & Scenes → Click automation → "Traces"
   - See exactly why automation fired or didn't fire

4. **Test services manually:**
   - Developer Tools → Services
   - Call services directly to verify they work

### Can I run multiple instances for different rooms?

Not currently supported. The component is designed as a singleton (one instance per Home Assistant).

**Workaround (advanced):**

Create multiple component instances with different domains (requires code modification):

1. Copy `custom_components/smart_vent` to `custom_components/smart_vent_bathroom`
2. Modify `const.py`: `DOMAIN = "smart_vent_bathroom"`
3. Update all references to use new domain
4. Add separate configuration block

**Better approach:** Request multi-instance support in [GitHub Issues](https://github.com/elisey/smart-vent/issues).

---

## Still Have Questions?

- **[Main Documentation](README.md)** - Complete component documentation
- **[Examples](EXAMPLES.md)** - Automation and UI examples
- **[Troubleshooting](TROUBLESHOOTING.md)** - Problem-solving guide
- **[GitHub Discussions](https://github.com/elisey/smart-vent/discussions)** - Ask questions
- **[GitHub Issues](https://github.com/elisey/smart-vent/issues)** - Report bugs or request features
- **[Home Assistant Community](https://community.home-assistant.io/)** - General Home Assistant help

**Can't find your answer?** Open a [GitHub Discussion](https://github.com/elisey/smart-vent/discussions) and we'll help!
