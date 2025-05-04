"""Constants for the iopool integration."""

from datetime import timedelta

DOMAIN = "iopool"
MANUFACTURER = "iopool"

# Configuration versions
CONFIG_VERSION = 1
CONFIG_MINOR_VERSION = 1

# Configuration options
CONF_API_KEY = "api_key"

# Polling interval - cloud service so minimum 60s
DEFAULT_SCAN_INTERVAL = timedelta(seconds=300)

# API endpoints
API_BASE_URL = "https://api.iopool.com/v1"
POOLS_ENDPOINT = f"{API_BASE_URL}/pools"
POOL_ENDPOINT = f"{API_BASE_URL}/pool/{{pool_id}}"

# Sensor types
SENSOR_TEMPERATURE = "temperature"
SENSOR_PH = "ph"
SENSOR_ORP = "orp"
SENSOR_MODE = "mode"
SENSOR_ACTION_REQUIRED = "action_required"
SENSOR_FILTRATION_DURATION = "filtration_duration"

# Sensor attributes
ATTR_MEASURED_AT = "measured_at"
ATTR_IS_VALID = "is_valid"
ATTR_MEASURE_MODE = "measure_mode"
