"""Constants for the iopool integration."""

from datetime import timedelta

DOMAIN = "iopool"
MANUFACTURER = "iopool"

# Configuration versions
CONFIG_VERSION = 1
CONFIG_MINOR_VERSION = 1

# Configuration options
CONF_API_KEY = "api_key"
CONF_POOL_ID = "pool_id"
CONF_OPTIONS_FILTRATION = "filtration"
CONF_OPTIONS_FILTRATION_SWITCH_ENTITY = "switch_entity"
CONF_OPTIONS_FILTRATION_SUMMER = "summer_filtration"
CONF_OPTIONS_FILTRATION_WINTER = "winter_filtration"
CONF_OPTIONS_FILTRATION_STATUS = "status"
CONF_OPTIONS_FILTRATION_MIN_DURATION = "min_duration"
CONF_OPTIONS_FILTRATION_MAX_DURATION = "max_duration"
CONF_OPTIONS_FILTRATION_SLOT1 = "slot1"
CONF_OPTIONS_FILTRATION_SLOT2 = "slot2"
CONF_OPTIONS_FILTRATION_NAME = "name"
CONF_OPTIONS_FILTRATION_START = "start"
CONF_OPTIONS_FILTRATION_DURATION_PERCENT = "duration_percent"
CONF_OPTIONS_FILTRATION_DURATION = "duration"

# Event types for boost operations
EVENT_TYPE_BOOST_START = "BOOST_START"
EVENT_TYPE_BOOST_END = "BOOST_END"
EVENT_TYPE_BOOST_CANCELED = "BOOST_CANCELED"
EVENT_TYPE_SLOT1_START = "SLOT1_START"
EVENT_TYPE_SLOT1_END = "SLOT1_END"
EVENT_TYPE_SLOT2_START = "SLOT2_START"
EVENT_TYPE_SLOT2_END = "SLOT2_END"
EVENT_TYPE_WINTER_START = "WINTER_START"
EVENT_TYPE_WINTER_END = "WINTER_END"

# Polling interval - 5 minutes
DEFAULT_SCAN_INTERVAL = timedelta(seconds=300)

# API endpoints
API_BASE_URL = "https://api.iopool.com/v1"
POOLS_ENDPOINT = f"{API_BASE_URL}/pools"
POOL_ENDPOINT = f"{API_BASE_URL}/pool/{{pool_id}}"

# Sensor types
SENSOR_TEMPERATURE = "temperature"
SENSOR_PH = "ph"
SENSOR_ORP = "orp"
SENSOR_IOPOOL_MODE = "iopool_mode"
SENSOR_POOL_MODE = "pool_mode"
SENSOR_BOOST_SELECTOR = "boost_selector"
SENSOR_ACTION_REQUIRED = "action_required"
SENSOR_FILTRATION_RECOMMENDATION = "filtration_recommendation"
SENSOR_ELAPSED_FILTRATION = "elapsed_filtration_duration"
SENSOR_HISTORY_STATS_PLATFORM = "history_stats"
SENSOR_FILTRATION = "filtration"

# Sensor attributes
ATTR_MEASURED_AT = "measured_at"
ATTR_IS_VALID = "is_valid"
ATTR_MEASURE_MODE = "measure_mode"
