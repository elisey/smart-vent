# Smart Ventilation Controller for Home Assistant

A Home Assistant custom component that provides intelligent ventilation control with automatic boost functionality based on humidity levels.

## Features

- **Three Operating Modes**: Low, Mid, and Boost controlled by a 3-position physical switch
- **Automatic Boost**: Activates when humidity exceeds 80% in mid mode
- **Manual Override**: Full control via physical switch or Home Assistant services
- **Daily Limits**: Configurable maximum boost activations per day
- **Real-time Updates**: Instant response to switch and humidity changes

## Documentation

For complete installation and configuration instructions, see the [Component Documentation](custom_components/smart_vent/README.md).

### Quick Links

- **[Installation Guide](custom_components/smart_vent/README.md#installation)** - HACS and manual installation
- **[Configuration](custom_components/smart_vent/README.md#configuration)** - Setup in configuration.yaml
- **[Automation Examples](custom_components/smart_vent/EXAMPLES.md)** - Ready-to-use automations
- **[Troubleshooting](custom_components/smart_vent/TROUBLESHOOTING.md)** - Common issues and solutions
- **[FAQ](custom_components/smart_vent/FAQ.md)** - Frequently asked questions

## Quick Start

1. Install via HACS or manually copy to `custom_components/smart_vent`
2. Add configuration to `configuration.yaml`:

```yaml
smart_vent:
  # Use either a fan entity or a light entity (for Shelly Dimmers)
  fan_entity: fan.your_fan  # or light.your_shelly_dimmer
  humidity_sensor: sensor.your_humidity
  input_0: binary_sensor.switch_input_0
  input_1: binary_sensor.switch_input_1
```

3. Restart Home Assistant
4. Configure your 3-position switch hardware

**Note**: The component supports both `fan.*` entities and `light.*` entities. Light entities are commonly used with Shelly Dimmers controlling fans via 0-10V or brightness control.

See the [full documentation](custom_components/smart_vent/README.md) for detailed setup instructions.

---

## Development Environment

This repository includes a complete Docker-based development environment for testing the Smart Ventilation Controller component.

### What's Included

- **Home Assistant in Docker** - Isolated development environment
- **Emulated Devices** - Humidity sensor, Shelly inputs, fan
- **Test Scripts** - Quick mode switching
- **Automations** - Various scenario simulations
- **Detailed Logging** - Component debugging

### Quick Start for Developers

```bash
# Start Home Assistant
docker-compose up -d

# View logs
docker-compose logs -f

# Access UI
open http://localhost:8123
```

### Test Devices Available

After initial setup, you'll have access to:

- `sensor.temperature_humidity_sensor_9970_humidity` - Humidity sensor
- `binary_sensor.shelly_input_0` - Switch input 0
- `binary_sensor.shelly_input_1` - Switch input 1
- `fan.real_fan` - Emulated fan entity (for backward compatibility testing)
- `light.shelly_dimmer_fan` - Emulated light entity (for Shelly Dimmer testing)
- `input_number.test_humidity` - Manual humidity control
- `input_number.fan_speed` - Fan entity speed state
- `input_number.light_fan_speed` - Light entity speed state
- `input_boolean.shelly_input_0/1` - Manual switch control

### Development Workflow

1. **Edit component code** in `custom_components/smart_vent/`
2. **Restart Home Assistant**: `docker-compose restart`
3. **Check logs**: `docker-compose logs -f | grep smart_vent`
4. **Test scenarios** using provided scripts and automations

### Test Scenarios

#### Manual Switch Control
```yaml
# Set to LOW mode
service: script.set_switch_low

# Set to MID mode
service: script.set_switch_mid

# Set to BOOST mode
service: script.set_switch_boost
```

#### Automatic Boost Test
```yaml
# 1. Set switch to MID
service: script.set_switch_mid

# 2. Trigger high humidity
service: input_boolean.turn_on
target:
  entity_id: input_boolean.quick_high_humidity
```

Wait 5 seconds (configured check_interval) and verify:
- Fan speed increases to 100%
- `binary_sensor.smart_vent_auto_boost` turns on

#### Simulate Gradual Humidity Rise
```yaml
service: input_boolean.turn_on
target:
  entity_id: input_boolean.simulate_high_humidity
```

Watch humidity increase every 2 seconds until auto-boost triggers at >80%.

### Monitoring and Debugging

```bash
# Real-time component logs
docker-compose logs -f | grep -i "smart_vent"

# Last 100 log lines
docker-compose logs --tail=100 | grep smart_vent

# Check configuration validity
docker exec ha-smart-vent-dev hass --script check_config -c /config
```

### Docker Commands

```bash
# Stop Home Assistant
docker-compose down

# Restart
docker-compose restart

# Full reset (removes all data)
docker-compose down -v
rm -rf config/*

# Rebuild and start
docker-compose up -d --force-recreate

# Shell access
docker exec -it ha-smart-vent-dev bash
```

### Connecting Real Hardware

When ready to test with actual devices:

1. **Add Shelly integration** via Home Assistant UI
2. **Add Xiaomi BLE** - auto-discovered with bluetooth enabled
3. **Update configuration** to use real entity IDs:

**Option A: Using Shelly Dimmer Light Entity (Recommended for 0-10V control)**
```yaml
smart_vent:
  # Use the light entity directly from Shelly Dimmer
  fan_entity: light.shelly0110dimg3_e4b3233d0e54_light_0
  humidity_sensor: sensor.temperature_humidity_sensor_9970_humidity
  input_0: binary_sensor.shelly0110dimg3_e4b3233d0e54_input_0
  input_1: binary_sensor.shelly0110dimg3_e4b3233d0e54_input_1
  speeds:
    low: 30
    mid: 52
    boost: 100
  check_interval: 20
  auto_boost_duration: 20
  max_boosts_per_day: 5
```

**Option B: Using Template Fan Entity (Alternative)**
```yaml
# If you prefer using a fan entity wrapper
smart_vent:
  fan_entity: fan.house_extractor  # Template fan that wraps the light
  humidity_sensor: sensor.temperature_humidity_sensor_9970_humidity
  input_0: binary_sensor.shelly_input_0
  input_1: binary_sensor.shelly_input_1
  speeds:
    low: 30
    mid: 52
    boost: 100
  check_interval: 20
  auto_boost_duration: 20
  max_boosts_per_day: 5
```

### Troubleshooting Development Environment

**HA won't start:**
```bash
docker-compose logs
docker-compose down && docker-compose up -d
```

**Component not loading:**
- Check file structure in `custom_components/smart_vent/`
- Verify `manifest.json` is valid JSON
- Check logs: `docker-compose logs | grep -i error`
- Validate config: Developer Tools > YAML > Check Configuration

**Code changes not applying:**
```bash
docker-compose restart
# Or via UI: Developer Tools > YAML > Restart Home Assistant
```

**Port 8123 occupied:**
```bash
sudo lsof -i :8123
# Stop conflicting process or change port in docker-compose.yml
```

## Project Structure

```
ha-dev/
├── custom_components/
│   └── smart_vent/          # Component code
│       ├── __init__.py
│       ├── coordinator.py
│       ├── fan.py
│       ├── binary_sensor.py
│       ├── const.py
│       ├── manifest.json
│       ├── services.yaml
│       ├── README.md        # User documentation
│       ├── EXAMPLES.md      # Automation examples
│       ├── TROUBLESHOOTING.md
│       └── FAQ.md
├── config/                  # Home Assistant config
│   └── configuration.yaml
├── docs/                    # Development docs
│   ├── DESIGN.md           # Implementation plan
│   ├── DEPLOYMENT.md
│   └── TEST_SCENARIOS.md
├── docker-compose.yml       # Development environment
└── README.md               # This file
```

## Resources

- **[Home Assistant Developer Docs](https://developers.home-assistant.io/)**
- **[Integration Development Guide](https://developers.home-assistant.io/docs/creating_integration)**
- **[Template Platform](https://www.home-assistant.io/integrations/template/)**
- **[Logger Component](https://www.home-assistant.io/integrations/logger/)**

## License

MIT License - see LICENSE file for details

## Support

For bug reports and feature requests, please open an issue on [GitHub](https://github.com/elisey/smart-vent/issues).
