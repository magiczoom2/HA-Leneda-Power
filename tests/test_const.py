"""Tests for Leneda constants."""
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.leneda.const import (
    DOMAIN,
    CONF_METERING_POINT,
    CONF_ENERGY_ID,
    CONF_API_KEY,
    CONF_OBIS_CODE,
    CONF_INITIAL_SETUP_DAYS_TO_FETCH,
    API_BASE_URL,
    DEFAULT_OBIS_CODE,
    DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH,
    POLLING_INTERVAL_HOURS,
    API_MAX_DAYS_TO_FETCH,
    API_MIN_DAYS_TO_FETCH,
    OBIS_HA_MAP,
)


def test_domain_constant():
    """Test DOMAIN constant."""
    assert DOMAIN == "leneda"


def test_config_constants():
    """Test configuration constants."""
    assert CONF_METERING_POINT == "metering_point"
    assert CONF_ENERGY_ID == "energy_id"
    assert CONF_API_KEY == "api_key"
    assert CONF_OBIS_CODE == "obis_code"
    assert CONF_INITIAL_SETUP_DAYS_TO_FETCH == "days_to_fetch_during_initial_setup"


def test_api_base_url():
    """Test API base URL."""
    assert API_BASE_URL == "https://api.leneda.eu/api"


def test_default_values():
    """Test default configuration values."""
    assert DEFAULT_OBIS_CODE == "1-1:1.29.0"
    assert DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH == 180


def test_polling_constants():
    """Test polling-related constants."""
    assert POLLING_INTERVAL_HOURS == 2
    assert API_MAX_DAYS_TO_FETCH == 30
    assert API_MIN_DAYS_TO_FETCH == 2


def test_obis_map_exists():
    """Test that OBIS_HA_MAP exists and has entries."""
    assert isinstance(OBIS_HA_MAP, dict)
    assert len(OBIS_HA_MAP) > 0


def test_obis_map_default_entry():
    """Test that default OBIS code is in map."""
    assert DEFAULT_OBIS_CODE in OBIS_HA_MAP


def test_obis_map_entry_structure():
    """Test that OBIS map entries have required fields."""
    mapping = OBIS_HA_MAP[DEFAULT_OBIS_CODE]

    required_fields = [
        "description",
        "service_type",
        "name",
        "unit",
        "device_class",
        "state_class",
        "aggregated_name",
        "aggregation_unit",
        "aggregation_device_class",
        "aggregation_state_class",
    ]

    for field in required_fields:
        assert field in mapping, f"Missing field: {field}"


def test_obis_consumption_mapping():
    """Test consumption OBIS code mapping."""
    mapping = OBIS_HA_MAP["1-1:1.29.0"]

    assert "Consumption" in mapping["name"]
    assert mapping["service_type"] == "Consumption"
    assert mapping["unit"] == UnitOfPower.KILO_WATT
    assert mapping["device_class"] == SensorDeviceClass.POWER
    assert mapping["state_class"] == SensorStateClass.MEASUREMENT


def test_obis_production_mapping():
    """Test production OBIS code mapping."""
    mapping = OBIS_HA_MAP["1-1:2.29.0"]

    assert "Production" in mapping["name"]
    assert mapping["service_type"] == "Production"
    assert mapping["unit"] == UnitOfPower.KILO_WATT
    assert mapping["device_class"] == SensorDeviceClass.POWER
    assert mapping["state_class"] == SensorStateClass.MEASUREMENT


def test_obis_reactive_consumption_mapping():
    """Test reactive consumption OBIS code mapping."""
    mapping = OBIS_HA_MAP["1-1:3.29.0"]

    assert "Reactive" in mapping["name"]
    assert "Consumption" in mapping["name"]
    assert mapping["device_class"] == SensorDeviceClass.REACTIVE_POWER


def test_obis_aggregated_mapping():
    """Test that aggregated fields exist for all entries."""
    for obis_code, mapping in OBIS_HA_MAP.items():
        assert "aggregated_name" in mapping
        assert "aggregation_unit" in mapping
        assert "aggregation_device_class" in mapping
        assert "aggregation_state_class" in mapping


def test_obis_map_energy_unit_for_aggregation():
    """Test that aggregated energy mapping uses energy units."""
    mapping = OBIS_HA_MAP[DEFAULT_OBIS_CODE]

    assert mapping["aggregation_unit"] == UnitOfEnergy.KILO_WATT_HOUR
    assert (
        mapping["aggregation_device_class"] == SensorDeviceClass.ENERGY
    )
    assert mapping["aggregation_state_class"] == SensorStateClass.TOTAL_INCREASING


def test_multiple_obis_codes_available():
    """Test that multiple OBIS codes are available."""
    expected_codes = [
        "1-1:1.29.0",  # Consumption
        "1-1:2.29.0",  # Production
        "1-1:3.29.0",  # Reactive Consumption
        "1-1:4.29.0",  # Reactive Production
        "1-65:1.29.1",  # Sharing Group L1
        "1-65:1.29.3",  # Sharing Group L2
    ]

    for code in expected_codes:
        assert code in OBIS_HA_MAP, f"OBIS code {code} not found in map"
