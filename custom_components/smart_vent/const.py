"""Constants for Smart Ventilation Controller."""

# Component domain
DOMAIN = "smart_vent"

# Mode constants
MODE_LOW = "low"
MODE_MID = "mid"
MODE_BOOST = "boost"

# Default speed percentages for each mode
DEFAULT_SPEEDS = {
    MODE_LOW: 30,
    MODE_MID: 52,
    MODE_BOOST: 100,
}

# Default check interval in seconds
DEFAULT_CHECK_INTERVAL = 20

# Default maximum number of automatic boost activations per day
DEFAULT_MAX_BOOSTS_PER_DAY = 5
