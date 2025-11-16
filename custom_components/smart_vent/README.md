# Smart Ventilation Controller

A Home Assistant custom component that provides intelligent ventilation control with automatic boost functionality based on humidity levels.

## Features

- **Three Operating Modes**: Low, Mid, and Boost ventilation speeds controlled by a 3-position physical switch
- **Automatic Boost**: Automatically activates boost mode when humidity exceeds 80% (configurable duration and daily limit)
- **Manual Override**: Full manual control via physical switch or Home Assistant services
- **Priority Management**: Handles competing control signals intelligently (manual always overrides automatic)
- **Daily Limits**: Prevents excessive boost activations with configurable daily maximum
- **State Persistence**: Restores to current switch position after Home Assistant restart
- **Real-time Updates**: Instant response to switch position changes and humidity fluctuations

## Requirements

### Home Assistant
- **Minimum Version**: Home Assistant 2023.1.0 or later
- **Integration Type**: Local Polling (no cloud dependencies)

### Hardware
- **Fan**: Any Home Assistant-compatible fan entity with percentage speed control
- **Humidity Sensor**: Any humidity sensor entity (Zigbee, Z-Wave, Bluetooth, etc.)
- **3-Position Switch**: Two binary sensors representing switch positions (e.g., Shelly device with two inputs)

### Recommended Hardware Setup
- **Shelly Plus i4** or similar device with 2+ binary inputs for the 3-position switch
- **Xiaomi Bluetooth Humidity Sensor** or equivalent for humidity monitoring
- **Fan controller** with ESPHome, Shelly, or other Home Assistant integration

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/elisey/smart-vent`
6. Category: Integration
7. Click "Add"
8. Search for "Smart Ventilation Controller"
9. Click "Download"
10. Restart Home Assistant

### Option 2: Manual Installation

1. Copy the `custom_components/smart_vent` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

Add the following to your `configuration.yaml`:

```yaml
smart_vent:
  fan_entity: fan.real_fan
  humidity_sensor: sensor.temperature_humidity_sensor_9970_humidity
  input_0: binary_sensor.shelly_input_0
  input_1: binary_sensor.shelly_input_1
  speeds:
    low: 30
    mid: 52
    boost: 100
  check_interval: 5
  auto_boost_duration: 20
  max_boosts_per_day: 5
```

### Configuration Options

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `fan_entity` | Yes | - | Entity ID of the fan to control |
| `humidity_sensor` | Yes | - | Entity ID of the humidity sensor |
| `input_0` | Yes | - | Entity ID of the first binary input (switch position 0) |
| `input_1` | Yes | - | Entity ID of the second binary input (switch position 1) |
| `speeds` | No | See below | Speed percentages for each mode |
| `speeds.low` | No | 30 | Speed percentage (0-100) for low mode |
| `speeds.mid` | No | 52 | Speed percentage (0-100) for mid mode |
| `speeds.boost` | No | 100 | Speed percentage (0-100) for boost mode |
| `check_interval` | No | 20 | How often to check conditions (seconds) |
| `auto_boost_duration` | No | 20 | Auto-boost duration (minutes) |
| `max_boosts_per_day` | No | 5 | Maximum auto-boost activations per day |

### 3-Position Switch Wiring

The component reads two binary inputs to determine the switch position:

| Switch Position | input_0 | input_1 | Mode |
|-----------------|---------|---------|------|
| Position 1 | OFF | OFF | Low |
| Position 2 | ON | OFF | Mid |
| Position 3 | OFF | ON | Boost |
| Invalid | ON | ON | Low (safe mode) |

Connect your 3-position switch so that:
- **Position 1**: Both inputs open (OFF)
- **Position 2**: Close input_0, open input_1
- **Position 3**: Open input_0, close input_1

## Operating Modes

### Low Mode
- Minimum ventilation speed (default 30%)
- Used for continuous background ventilation
- Lowest power consumption

### Mid Mode
- Medium ventilation speed (default 52%)
- Normal operating mode for everyday use
- Enables automatic boost when humidity > 80%

### Boost Mode
- Maximum ventilation speed (default 100%)
- Manual activation via switch or service
- Automatic activation when mid mode + high humidity

## Automatic Boost Logic

When the physical switch is in **Mid position**:

1. **Activation Trigger**: Humidity exceeds 80%
2. **Action**: Fan speed increases to boost level
3. **Duration**: Runs for configured duration (default 20 minutes)
4. **Daily Limit**: Respects `max_boosts_per_day` setting
5. **Return**: Automatically returns to mid speed after timeout
6. **Override**: Manual switch movement immediately cancels auto-boost

**Daily Counter Reset**: Resets at midnight (00:00) each day

## Entities Created

### Fan Entity: `fan.smart_vent`
Virtual fan entity representing the ventilation system state.

**Attributes**:
- `percentage`: Current fan speed (0-100)
- `preset_mode`: Current mode (low/mid/boost)
- `auto_boost_active`: Whether auto-boost is currently active
- `auto_boost_end_time`: When current auto-boost will end
- `auto_boost_count_today`: Number of auto-boosts used today

**Note**: This entity reflects the state but doesn't directly control the fan. It's a status indicator.

### Binary Sensor: `binary_sensor.smart_vent_auto_boost`
Indicates whether automatic boost is currently active.

**Attributes**:
- `time_remaining`: Minutes remaining in current auto-boost
- `count_today`: Auto-boosts used today
- `max_per_day`: Daily limit

**States**:
- `on`: Auto-boost is active
- `off`: Auto-boost is not active

## Services

### `smart_vent.set_mode`
Manually set the ventilation mode (overrides physical switch).

**Parameters**:
- `mode` (required): One of `low`, `mid`, or `boost`

**Example**:
```yaml
service: smart_vent.set_mode
data:
  mode: boost
```

**Note**: This service overrides the physical switch temporarily. The mode will revert to the switch position on the next state change.

### `smart_vent.force_boost`
Manually trigger boost mode for the configured duration, bypassing the daily limit.

**Parameters**: None

**Example**:
```yaml
service: smart_vent.force_boost
```

**Use Cases**:
- Emergency ventilation needed
- Before/after cooking, showering
- Override daily limit when necessary

## Architecture

### DataUpdateCoordinator Pattern
The component uses Home Assistant's `DataUpdateCoordinator` for efficient state management:

- **State Listeners**: Instant updates when switch or humidity changes
- **Periodic Updates**: Regular checks for auto-boost timeout
- **Debounce Protection**: Prevents rapid repeated updates
- **Error Handling**: Graceful degradation when sensors unavailable

### State Management

```
Physical Switch → Coordinator → Fan Entity
                ↓
Humidity Sensor → Auto-Boost Logic → Binary Sensor
```

1. **Input Monitoring**: Coordinator monitors switch inputs and humidity
2. **Mode Determination**: Calculates desired mode based on inputs and conditions
3. **Priority Resolution**: Applies priority rules (manual > automatic)
4. **Fan Control**: Sends speed commands to physical fan
5. **State Broadcast**: Updates virtual entities for UI display

### Priority System

1. **Manual Boost** (physical switch in boost): Highest priority, cancels auto-boost
2. **Auto-Boost** (humidity trigger in mid mode): Medium priority, temporary
3. **Manual Low** (physical switch in low): Cancels auto-boost, returns to low
4. **Normal Mid** (physical switch in mid): Default state, enables auto-boost

## Logging

To enable debug logging, add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smart_vent: debug
```

**Log Levels**:
- `INFO`: Mode changes, boost activations/deactivations
- `WARNING`: Limit exceeded, sensor unavailable
- `ERROR`: Invalid switch states, configuration errors
- `DEBUG`: State changes, periodic updates, decision logic

## Example Automations

See [EXAMPLES.md](EXAMPLES.md) for complete automation examples including:
- Button-triggered boost
- Schedule-based activation
- Lovelace UI cards
- Notification automations

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## FAQ

See [FAQ.md](FAQ.md) for frequently asked questions.

## License

MIT License - see LICENSE file for details

## Support

For bug reports and feature requests, please open an issue on [GitHub](https://github.com/elisey/smart-vent/issues).

## Credits

Developed for Home Assistant smart home automation.
