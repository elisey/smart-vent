# Smart Ventilation Controller - Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Smart Ventilation Controller component.

## Table of Contents

- [Enable Debug Logging](#enable-debug-logging)
- [Check Sensor States](#check-sensor-states)
- [Common Issues](#common-issues)
  - [Component Not Loading](#component-not-loading)
  - [Invalid Switch State](#invalid-switch-state)
  - [Humidity Sensor Unavailable](#humidity-sensor-unavailable)
  - [Boost Limit Exceeded](#boost-limit-exceeded)
  - [Fan Not Responding](#fan-not-responding)
  - [Auto-Boost Not Activating](#auto-boost-not-activating)
  - [Mode Keeps Reverting](#mode-keeps-reverting)
  - [Entities Not Appearing](#entities-not-appearing)
- [Advanced Diagnostics](#advanced-diagnostics)

---

## Enable Debug Logging

Debug logging provides detailed information about the component's operation. This should be your first step when troubleshooting.

### Method 1: Via configuration.yaml (Permanent)

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_vent: debug
```

Restart Home Assistant after making this change.

### Method 2: Via UI (Temporary - until next restart)

1. Go to **Settings** → **System** → **Logs**
2. Click **Set log level** (bottom right)
3. Find `custom_components.smart_vent`
4. Set to **Debug**
5. Click **Set level**

### View Logs

**Via UI:**
- Settings → System → Logs
- Look for entries starting with `custom_components.smart_vent`

**Via Command Line (if using Docker):**
```bash
docker logs homeassistant | grep smart_vent
```

**Via Log File:**
```bash
# In Home Assistant config directory
tail -f home-assistant.log | grep smart_vent
```

---

## Check Sensor States

Use Developer Tools to verify entity states and attributes.

### Steps

1. Go to **Developer Tools** → **States**
2. Search for your entities:
   - `fan.real_fan` (your physical fan)
   - `sensor.temperature_humidity_sensor_9970_humidity` (humidity sensor)
   - `binary_sensor.shelly_input_0` (switch input 0)
   - `binary_sensor.shelly_input_1` (switch input 1)
   - `binary_sensor.smart_vent_auto_boost` (auto-boost indicator)

### What to Check

**For binary sensors (switch inputs):**
- State should be `on` or `off`, not `unavailable` or `unknown`
- Check `last_changed` to see if they're updating

**For humidity sensor:**
- State should be a number (e.g., `65.5`)
- Check `unit_of_measurement` is `%`
- State should not be `unavailable`, `unknown`, or `None`

**For fan:**
- State should be `on` or `off`
- Check `percentage` attribute for current speed
- Verify fan is reachable and responding

---

## Common Issues

### Component Not Loading

**Symptoms:**
- No `fan.smart_vent` or `binary_sensor.smart_vent_auto_boost` entities
- Error in logs: "Setup failed for smart_vent"

**Possible Causes & Solutions:**

#### 1. Configuration Error

Check your configuration:

```yaml
smart_vent:
  fan_entity: fan.real_fan
  humidity_sensor: sensor.temperature_humidity_sensor_9970_humidity
  input_0: binary_sensor.shelly_input_0
  input_1: binary_sensor.shelly_input_1
```

**Verify:**
- All required fields are present
- Entity IDs match exactly (case-sensitive)
- No typos in YAML syntax
- Proper indentation (2 spaces, no tabs)

**Validate configuration:**
1. Developer Tools → YAML
2. Click "Check Configuration"
3. Look for errors related to `smart_vent`

#### 2. Missing Files

Verify all component files exist in `custom_components/smart_vent/`:

```
custom_components/smart_vent/
├── __init__.py
├── coordinator.py
├── fan.py
├── binary_sensor.py
├── const.py
├── manifest.json
└── services.yaml
```

#### 3. Invalid manifest.json

The `manifest.json` must be valid JSON. Check with:

```bash
cat custom_components/smart_vent/manifest.json | python3 -m json.tool
```

If this command fails, your JSON is malformed.

#### 4. Entity IDs Don't Exist

Verify all referenced entities exist:
- Go to Developer Tools → States
- Search for each entity ID from your config
- If any are missing, check your hardware integrations

**Solution:** Fix the entity IDs in your configuration to match actual entities.

---

### Invalid Switch State

**Symptoms:**
- Fan stuck at low speed (30%)
- Error in logs: "Invalid switch state detected: both inputs are ON"
- Unexpected behavior when changing switch position

**Explanation:**

The 3-position switch should never have both inputs ON simultaneously:

| Position | input_0 | input_1 | Mode | Valid? |
|----------|---------|---------|------|--------|
| 1 | OFF | OFF | Low | ✅ |
| 2 | ON | OFF | Mid | ✅ |
| 3 | OFF | ON | Boost | ✅ |
| Invalid | ON | ON | Low (safe mode) | ❌ |

**Common Causes:**

1. **Wiring Issue**: Both switch terminals connected simultaneously
2. **Switch Bounce**: Mechanical switch bouncing during transition
3. **Faulty Switch**: Defective 3-position switch

**Solutions:**

#### Check Physical Wiring

1. Turn off power to the switch
2. Verify wiring diagram:
   - Position 1: Both terminals open
   - Position 2: Terminal 0 closes, terminal 1 open
   - Position 3: Terminal 0 open, terminal 1 closes
3. Test with multimeter in each position

#### Verify in Home Assistant

1. Developer Tools → States
2. Manually move switch through all positions
3. Watch `binary_sensor.shelly_input_0` and `binary_sensor.shelly_input_1`
4. Verify only one (or neither) is `on` at any time

#### Temporary Workaround

If you can't fix the wiring immediately, the component defaults to LOW mode (safe mode) when detecting invalid state.

---

### Humidity Sensor Unavailable

**Symptoms:**
- Auto-boost never activates
- Warning in logs: "Humidity sensor unavailable or invalid"
- `sensor.temperature_humidity_sensor_9970_humidity` shows `unavailable`

**Possible Causes & Solutions:**

#### 1. Sensor Offline

**Check:**
- Is the sensor powered?
- Is it in range of the Bluetooth/Zigbee/Z-Wave controller?
- Battery level (if battery-powered)?

**Solution:**
- Replace batteries
- Move sensor closer to controller
- Restart the sensor integration

#### 2. Integration Issue

**For Bluetooth sensors:**
```yaml
# Verify bluetooth is enabled in configuration.yaml
bluetooth:
```

**For Xiaomi BLE:**
- Settings → Devices & Services → Bluetooth
- Verify sensor is discovered and configured

#### 3. Entity Name Changed

Sometimes integrations change entity IDs after updates.

**Solution:**
1. Developer Tools → States
2. Search for "humidity"
3. Find your actual sensor entity ID
4. Update `smart_vent` configuration with correct entity ID
5. Restart Home Assistant

#### 4. Sensor Value Invalid

The component expects a numeric humidity value.

**Check logs for:**
```
WARNING: Humidity value is not numeric: None
WARNING: Humidity value is not numeric: unavailable
```

**Verify sensor:**
- Developer Tools → States → sensor.temperature_humidity_sensor_9970_humidity
- State should be a number, not "unknown" or "unavailable"

---

### Boost Limit Exceeded

**Symptoms:**
- Auto-boost not activating despite high humidity
- Warning in logs: "Auto-boost limit reached for today (5/5)"
- `binary_sensor.smart_vent_auto_boost` stays OFF

**Explanation:**

The component limits automatic boost activations to prevent excessive wear. Default is 5 per day.

**Check Current Usage:**

1. Developer Tools → States → `binary_sensor.smart_vent_auto_boost`
2. Check attributes:
   - `count_today`: Current count
   - `max_per_day`: Configured limit

**Solutions:**

#### Wait for Daily Reset

Counter automatically resets at midnight (00:00).

#### Increase Daily Limit

Edit `configuration.yaml`:

```yaml
smart_vent:
  # ... other config ...
  max_boosts_per_day: 10  # Increase from default 5
```

Restart Home Assistant.

#### Use Manual Boost

The `force_boost` service bypasses the daily limit:

```yaml
service: smart_vent.force_boost
```

**Note:** Use sparingly as this bypasses safety limits.

#### Adjust Auto-Boost Duration

If boosts are too short and retriggering often:

```yaml
smart_vent:
  # ... other config ...
  auto_boost_duration: 30  # Increase from default 20 minutes
```

---

### Fan Not Responding

**Symptoms:**
- Mode changes but fan speed doesn't change
- Fan stuck at one speed
- Error in logs: "Failed to set fan speed"

**Possible Causes & Solutions:**

#### 1. Fan Entity Unavailable

**Check:**
1. Developer Tools → States → `fan.real_fan`
2. State should be `on` or `off`, not `unavailable`

**Solution:**
- Check fan hardware (power, connectivity)
- Restart fan integration
- Verify fan entity ID in configuration

#### 2. Fan Doesn't Support Percentage Control

The component requires fans with percentage speed control.

**Verify:**
1. Developer Tools → States → `fan.real_fan`
2. Check `supported_features` attribute
3. Should include `SET_SPEED` or percentage control

**Solution:**
- Use a compatible fan controller (ESPHome, Shelly Dimmer, etc.)
- Configure fan integration for percentage mode

#### 3. Permission/Communication Issue

**Check logs for:**
```
ERROR: Error calling service fan.set_percentage
ERROR: Failed to communicate with fan
```

**Solution:**
- Restart fan hardware
- Check network connectivity (WiFi, Zigbee, etc.)
- Verify Home Assistant can control fan manually via UI

#### 4. Service Call Syntax Error

Very rare, but check logs for service call errors.

**Manual Test:**

Try controlling fan directly:

```yaml
# Developer Tools → Services
service: fan.set_percentage
target:
  entity_id: fan.real_fan
data:
  percentage: 50
```

If this works, the issue is in the component. If not, issue is with the fan.

---

### Auto-Boost Not Activating

**Symptoms:**
- Humidity > 80%
- Switch in MID position
- `binary_sensor.smart_vent_auto_boost` stays OFF
- No boost activation in logs

**Diagnostic Checklist:**

#### 1. Verify Switch Position

Auto-boost only works in MID mode.

**Check:**
- `binary_sensor.shelly_input_0` = ON
- `binary_sensor.shelly_input_1` = OFF

#### 2. Verify Humidity Threshold

Default threshold is 80%.

**Check:**
- Developer Tools → States → `sensor.temperature_humidity_sensor_9970_humidity`
- Value must be > 80

#### 3. Check Daily Limit

See [Boost Limit Exceeded](#boost-limit-exceeded) above.

#### 4. Check Update Interval

Auto-boost checks every `check_interval` seconds (default 20).

**Your configuration has:**
```yaml
check_interval: 5  # Checks every 5 seconds
```

Wait at least 5 seconds after conditions are met.

#### 5. Verify in Logs

With debug logging enabled, you should see:

```
DEBUG: Checking auto-boost conditions
DEBUG: Switch mode: mid, Humidity: 82.5%, Auto-boost active: False, Count: 2/5
INFO: Activating automatic boost mode
```

If you don't see these, check why conditions aren't met.

#### 6. Manual Boost Override

If auto-boost was manually canceled, it won't retrigger until conditions reset.

**Solution:** Move switch to LOW, then back to MID to reset.

---

### Mode Keeps Reverting

**Symptoms:**
- Set mode via `smart_vent.set_mode` service
- Mode changes back to switch position
- Can't maintain mode set via service

**Explanation:**

This is **expected behavior**. The physical switch has priority.

**How It Works:**

1. Physical switch position determines the mode
2. Service calls (`set_mode`) temporarily override
3. On next state update (switch change, humidity change, periodic check), mode reverts to switch position

**Solutions:**

#### For Permanent Changes: Use Physical Switch

The component is designed for physical switch control as primary interface.

#### For Automations: Keep Switch in Desired Mode

If running automation-based mode changes, ensure switch is in compatible position:

```yaml
# Example: Only set MID mode if switch isn't in LOW
automation:
  - alias: "Set Mid Mode"
    action:
      - condition: state
        entity_id: binary_sensor.shelly_input_0
        state: "on"  # Verify switch isn't in LOW
      - service: smart_vent.set_mode
        data:
          mode: mid
```

#### For Manual Override: Use force_boost

The `force_boost` service is designed for temporary overrides:

```yaml
service: smart_vent.force_boost
```

This activates boost for configured duration, then returns to switch mode.

---

### Entities Not Appearing

**Symptoms:**
- `fan.smart_vent` doesn't exist
- `binary_sensor.smart_vent_auto_boost` doesn't exist
- Component loads but entities missing

**Solutions:**

#### 1. Wait for Discovery

Entities may take 30-60 seconds to appear after restart.

#### 2. Check Entity Registry

1. Settings → Devices & Services → Entities
2. Search for "smart_vent"
3. Check if entities are disabled

**If disabled:**
- Click on entity
- Click "Enable"
- Click "Update"

#### 3. Check Coordinator Initialization

Enable debug logging and check for:

```
INFO: Smart Ventilation Controller component loaded
DEBUG: Coordinator initialized
DEBUG: Fan platform loaded
DEBUG: Binary sensor platform loaded
```

If you see errors after these, coordinator failed to initialize.

#### 4. Configuration Issues

Verify your configuration is valid (see [Component Not Loading](#component-not-loading)).

---

## Advanced Diagnostics

### Check Coordinator State

The coordinator manages all component logic.

**Enable debug logging** and search for:

```
DEBUG: Update cycle starting
DEBUG: Switch state: input_0=on, input_1=off
DEBUG: Switch mode determined: mid
DEBUG: Current humidity: 65.2%
DEBUG: Auto-boost conditions: mode=mid, humidity=65.2, active=False, limit=2/5
DEBUG: Update cycle complete
```

This shows the coordinator's decision-making process.

### Test Mode Transitions

Systematically test all modes:

```yaml
# Test LOW
service: script.set_switch_low
# Wait 10 seconds, verify fan = 30%

# Test MID
service: script.set_switch_mid
# Wait 10 seconds, verify fan = 52%

# Test BOOST
service: script.set_switch_boost
# Wait 10 seconds, verify fan = 100%
```

Document which transitions work and which don't.

### Verify Service Registration

Check services are registered:

1. Developer Tools → Services
2. Search for "smart_vent"
3. Should see:
   - `smart_vent.set_mode`
   - `smart_vent.force_boost`

If missing, component didn't load properly.

### Check Home Assistant Logs for Errors

Look for Python exceptions:

```bash
# Search for tracebacks
grep -A 20 "Traceback" home-assistant.log | grep -A 20 "smart_vent"
```

Common errors:
- `ModuleNotFoundError`: Missing dependency
- `AttributeError`: Code bug
- `ValueError`: Invalid configuration value

### Network/Hardware Diagnostics

If sensors work in Home Assistant but not in smart_vent:

1. **Test sensor directly:**
   ```yaml
   service: homeassistant.update_entity
   target:
     entity_id: sensor.temperature_humidity_sensor_9970_humidity
   ```

2. **Check latency:**
   - Developer Tools → States
   - Click on sensor
   - Check `last_changed` and `last_updated`
   - Should update regularly (< 5 minutes for most sensors)

3. **Verify integrations are loaded:**
   - Settings → Devices & Services
   - Verify Shelly/Bluetooth/etc. integrations are active

---

## Still Having Issues?

If you've tried everything above and still experiencing problems:

### 1. Gather Information

Collect:
- Your `configuration.yaml` smart_vent section
- Debug logs showing the issue
- Screenshots of entity states
- Home Assistant version (`Settings → About`)
- Component version (from `manifest.json`)

### 2. Check Known Issues

Visit the [GitHub Issues](https://github.com/elisey/smart-vent/issues) page to see if your issue is already reported.

### 3. Report a Bug

Create a new issue with:
- **Title:** Brief description of the problem
- **Description:** Detailed explanation
- **Configuration:** Your smart_vent config (remove sensitive info)
- **Logs:** Relevant debug logs
- **Environment:** HA version, installation method, hardware
- **Steps to Reproduce:** How to trigger the issue

### 4. Community Support

Ask for help:
- [Home Assistant Community Forums](https://community.home-assistant.io/)
- Tag your post with `custom-component` and `smart-vent`

---

## Useful Commands Reference

### Docker (Development Environment)

```bash
# View logs
docker-compose logs -f | grep smart_vent

# Restart Home Assistant
docker-compose restart

# Check configuration
docker exec ha-smart-vent-dev hass --script check_config -c /config
```

### Home Assistant CLI

```bash
# Check configuration
hass --script check_config

# View logs
tail -f home-assistant.log | grep smart_vent
```

### Test Services

```yaml
# Test set_mode
service: smart_vent.set_mode
data:
  mode: boost

# Test force_boost
service: smart_vent.force_boost

# Test fan control directly
service: fan.set_percentage
target:
  entity_id: fan.real_fan
data:
  percentage: 75
```

---

**Need More Help?**

- **[Main Documentation](README.md)** - Component overview
- **[Examples](EXAMPLES.md)** - Automation examples
- **[FAQ](FAQ.md)** - Frequently asked questions
- **[GitHub Issues](https://github.com/elisey/smart-vent/issues)** - Report bugs
