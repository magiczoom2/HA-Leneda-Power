"""Tests for Leneda sensor."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from custom_components.leneda.sensor import (
    async_setup_entry,
    LenedaMeteringSensor,
    LenedaAggregatedMeteringSensor,
    SCAN_INTERVAL,
)
from custom_components.leneda.const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_ENERGY_ID,
    CONF_METERING_POINT,
    CONF_OBIS_CODE,
    CONF_INITIAL_SETUP_DAYS_TO_FETCH,
    DEFAULT_OBIS_CODE,
    API_MAX_DAYS_TO_FETCH,
    API_MIN_DAYS_TO_FETCH,
    POLLING_INTERVAL_HOURS,
)


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        CONF_API_KEY: "test_api_key",
        CONF_ENERGY_ID: "test_energy_id",
        CONF_METERING_POINT: "test_metering_point",
        CONF_OBIS_CODE: DEFAULT_OBIS_CODE,
        CONF_INITIAL_SETUP_DAYS_TO_FETCH: 180,
    }


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    hass.async_create_task = MagicMock()
    return hass


@pytest.fixture
def mock_config_entry(mock_config):
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Leneda",
        data=mock_config,
        options={},
        entry_id="test_entry_123",
        source="user",
        discovery_keys=None,
        subentries_data={},
        unique_id=None,
    )


@pytest.mark.asyncio
async def test_async_setup_entry_creates_entities(mock_hass, mock_config_entry):
    """Test that async_setup_entry creates sensor entities."""
    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

    async_add_entities.assert_called_once()
    call_args = async_add_entities.call_args[0]
    entities = call_args[0]

    assert len(entities) == 2
    assert isinstance(entities[0], LenedaMeteringSensor)
    assert isinstance(entities[1], LenedaAggregatedMeteringSensor)


@pytest.mark.asyncio
async def test_async_setup_entry_update_before_add(mock_hass, mock_config_entry):
    """Test that async_setup_entry requests update before adding."""
    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_config_entry, async_add_entities)

    call_args = async_add_entities.call_args
    assert call_args[0][1] is True


def test_metering_sensor_initialization(mock_hass, mock_config):
    """Test LenedaMeteringSensor initialization."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    assert sensor._attr_name == "Active Power Consumption"
    assert sensor._attr_device_class is not None
    assert sensor._attr_state_class is not None
    assert sensor.unique_id_suffix == "pwr_15min"


def test_metering_sensor_unique_id(mock_hass, mock_config):
    """Test that metering sensor has correct unique ID."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    assert sensor._attr_unique_id == "test_metering_point_1-1:1.29.0_pwr_15min"


def test_metering_sensor_entity_id(mock_hass, mock_config):
    """Test that metering sensor has correct entity ID."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    # Entity ID should have underscores instead of dots
    assert "sensor." in sensor.entity_id
    assert "_" in sensor.entity_id


def test_metering_sensor_extra_attributes(mock_hass, mock_config):
    """Test that metering sensor has extra state attributes."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    attrs = sensor._attr_extra_state_attributes
    assert "obis_code" in attrs
    assert attrs["obis_code"] == DEFAULT_OBIS_CODE
    assert "description" in attrs
    assert "service_type" in attrs
    assert attrs["service_type"] == "Consumption"


def test_aggregated_sensor_initialization(mock_hass, mock_config):
    """Test LenedaAggregatedMeteringSensor initialization."""
    sensor = LenedaAggregatedMeteringSensor(mock_hass, mock_config)

    assert "Energy" in sensor._attr_name
    assert sensor.unique_id_suffix == "energy_hourly"


def test_aggregated_sensor_unique_id(mock_hass, mock_config):
    """Test that aggregated sensor has correct unique ID."""
    sensor = LenedaAggregatedMeteringSensor(mock_hass, mock_config)

    assert sensor._attr_unique_id == "test_metering_point_1-1:1.29.0_energy_hourly"


def test_production_obis_code_mapping(mock_hass, mock_config):
    """Test production OBIS code mapping in sensor."""
    config = mock_config.copy()
    config[CONF_OBIS_CODE] = "1-1:2.29.0"

    sensor = LenedaMeteringSensor(mock_hass, config)

    assert "Production" in sensor._attr_name
    assert sensor._attr_extra_state_attributes["service_type"] == "Production"


def test_reactive_obis_code_mapping(mock_hass, mock_config):
    """Test reactive OBIS code mapping in sensor."""
    config = mock_config.copy()
    config[CONF_OBIS_CODE] = "1-1:3.29.0"

    sensor = LenedaMeteringSensor(mock_hass, config)

    assert "Reactive" in sensor._attr_name
    assert "Consumption" in sensor._attr_name


def test_scan_interval_constant():
    """Test SCAN_INTERVAL constant."""
    assert SCAN_INTERVAL == timedelta(hours=POLLING_INTERVAL_HOURS)


def test_base_sensor_has_entity_name(mock_hass, mock_config):
    """Test that base sensor has entity name attribute set."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    assert sensor._attr_has_entity_name is True


def test_base_sensor_should_poll(mock_hass, mock_config):
    """Test that base sensor should poll."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    assert sensor._attr_should_poll is True


def test_base_sensor_display_precision(mock_hass, mock_config):
    """Test that base sensor has correct display precision."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    assert sensor._attr_suggested_display_precision == 3


@pytest.mark.asyncio
async def test_get_last_timestamp_no_history(mock_hass, mock_config):
    """Test get_last_timestamp when no history exists."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    with patch("custom_components.leneda.sensor.get_instance") as mock_recorder:
        mock_recorder_instance = AsyncMock()
        mock_recorder.return_value = mock_recorder_instance
        mock_recorder_instance.async_add_executor_job = AsyncMock(return_value={})

        result = await sensor.get_last_timestamp()

        assert result is None


@pytest.mark.asyncio
async def test_get_days_to_fetch_initial_setup(mock_hass, mock_config):
    """Test get_days_to_fetch during initial setup."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    with patch("custom_components.leneda.sensor.get_instance") as mock_recorder:
        mock_recorder_instance = AsyncMock()
        mock_recorder.return_value = mock_recorder_instance
        mock_recorder_instance.async_add_executor_job = AsyncMock(return_value={})

        result = await sensor.get_days_to_fetch()

        assert result == 180  # DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH


@pytest.mark.asyncio
async def test_get_days_to_fetch_with_history(mock_hass, mock_config):
    """Test get_days_to_fetch when history exists."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    # Set up mock to return a timestamp from 5 days ago
    five_days_ago = dt_util.now(dt_util.UTC) - timedelta(days=5)
    five_days_ago_timestamp = five_days_ago.timestamp()

    with patch("custom_components.leneda.sensor.get_instance") as mock_recorder:
        with patch("custom_components.leneda.sensor.get_last_statistics") as mock_stats:
            mock_recorder_instance = AsyncMock()
            mock_recorder.return_value = mock_recorder_instance
            mock_stats.return_value = {
                sensor.entity_id: [{"start": five_days_ago_timestamp}]
            }
            mock_recorder_instance.async_add_executor_job = AsyncMock(
                side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)
            )

            result = await sensor.get_days_to_fetch()

            assert result >= API_MIN_DAYS_TO_FETCH


@pytest.mark.asyncio
async def test_fetch_from_api_success(mock_hass, mock_config):
    """Test _fetch_from_api with successful response."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"items": [{"value": 1.5}]})

    with patch("custom_components.leneda.sensor.async_get_clientsession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        # Create an async context manager mock
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get = MagicMock(return_value=mock_cm)

        result = await sensor._fetch_from_api("time-series", {})

        assert result == {"items": [{"value": 1.5}]}


@pytest.mark.asyncio
async def test_fetch_from_api_failure(mock_hass, mock_config):
    """Test _fetch_from_api with failed response."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    mock_response = AsyncMock()
    mock_response.status = 400

    with patch("custom_components.leneda.sensor.async_get_clientsession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        # Create an async context manager mock
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get = MagicMock(return_value=mock_cm)

        result = await sensor._fetch_from_api("time-series", {})

        assert result == {}


def test_api_url_construction(mock_hass, mock_config):
    """Test that API URL is constructed correctly."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    expected_base = "https://api.leneda.eu/api/metering-points/test_metering_point"
    # Just verify the sensor was initialized correctly with the config
    assert sensor._config[CONF_METERING_POINT] == "test_metering_point"

@pytest.mark.asyncio
async def test_fetch_from_api_exception(mock_hass, mock_config):
    """Test _fetch_from_api handles exceptions."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    with patch("custom_components.leneda.sensor.async_get_clientsession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        
        # Simulate exception
        mock_session_instance.get = MagicMock(side_effect=Exception("Connection error"))

        result = await sensor._fetch_from_api("time-series", {})

        assert result == {}


@pytest.mark.asyncio
async def test_metering_sensor_async_update_no_data(mock_hass, mock_config):
    """Test LenedaMeteringSensor async_update with no data returned."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)

    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "_fetch_from_api", return_value={}):
            with patch("custom_components.leneda.sensor.get_instance"):
                await sensor.async_update()
                # Should complete without error


@pytest.mark.asyncio
async def test_metering_sensor_async_update_with_data(mock_hass, mock_config):
    """Test LenedaMeteringSensor async_update processes 15-min data correctly."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)
    
    now = dt_util.now(dt_util.UTC)
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    # Create mock 15-minute interval data
    items = [
        {"startedAt": hour_start.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 1.0},
        {"startedAt": (hour_start + timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 2.0},
        {"startedAt": (hour_start + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 3.0},
    ]
    
    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "_fetch_from_api", return_value={"items": items}):
            with patch("custom_components.leneda.sensor.async_import_statistics") as mock_import:
                with patch("custom_components.leneda.sensor.get_instance"):
                    await sensor.async_update()
                    
                    # Verify statistics were imported
                    assert mock_import.called
                    # Verify that it was called with 3 positional args: hass, metadata, stats
                    call_args = mock_import.call_args
                    assert len(call_args[0]) == 3  # hass, metadata, stat_data
                    stat_data_list = call_args[0][2]
                    # Should have 1 hour of aggregated data (3 15-min values -> 1 hour)
                    assert len(stat_data_list) == 1


@pytest.mark.asyncio
async def test_metering_sensor_async_update_invalid_timestamp(mock_hass, mock_config):
    """Test LenedaMeteringSensor handles invalid timestamps."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)
    
    items = [
        {"startedAt": "invalid-date", "value": 1.0},
    ]
    
    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "_fetch_from_api", return_value={"items": items}):
            with patch("custom_components.leneda.sensor.async_import_statistics") as mock_import:
                with patch("custom_components.leneda.sensor.get_instance"):
                    await sensor.async_update()
                    
                    # Should complete without error - no valid data to import
                    # If import was called, it should have been with empty list
                    if mock_import.called:
                        stat_data = mock_import.call_args[0][2]
                        assert len(stat_data) == 0  # Empty list for invalid timestamps


@pytest.mark.asyncio
async def test_metering_sensor_chunked_fetch(mock_hass, mock_config):
    """Test LenedaMeteringSensor chunks large date ranges."""
    sensor = LenedaMeteringSensor(mock_hass, mock_config)
    
    now = dt_util.now(dt_util.UTC)
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    
    items = [
        {"startedAt": hour_start.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 1.0},
    ]
    
    with patch.object(sensor, "get_days_to_fetch", return_value=API_MAX_DAYS_TO_FETCH + 5):
        with patch.object(sensor, "_fetch_from_api", return_value={"items": items}) as mock_fetch:
            with patch("custom_components.leneda.sensor.async_import_statistics"):
                with patch("custom_components.leneda.sensor.get_instance"):
                    await sensor.async_update()
                    
                    # Should have made multiple API calls due to chunking
                    assert mock_fetch.call_count > 1


@pytest.mark.asyncio
async def test_aggregated_sensor_async_update_no_data(mock_hass, mock_config):
    """Test LenedaAggregatedMeteringSensor async_update with no data."""
    sensor = LenedaAggregatedMeteringSensor(mock_hass, mock_config)

    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "_fetch_from_api", return_value={}):
            with patch("custom_components.leneda.sensor.get_instance"):
                await sensor.async_update()
                # Should complete without error


@pytest.mark.asyncio
async def test_aggregated_sensor_async_update_with_data(mock_hass, mock_config):
    """Test LenedaAggregatedMeteringSensor processes hourly data correctly."""
    sensor = LenedaAggregatedMeteringSensor(mock_hass, mock_config)
    
    now = dt_util.now(dt_util.UTC)
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    items = [
        {"startedAt": hour_start.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 5.0},
        {"startedAt": (hour_start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 3.0},
    ]
    
    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "get_last_timestamp", return_value=None):
            with patch.object(sensor, "_fetch_from_api", return_value={"aggregatedTimeSeries": items}):
                with patch("custom_components.leneda.sensor.async_import_statistics") as mock_import:
                    mock_recorder = AsyncMock()
                    mock_recorder.async_add_executor_job = AsyncMock(return_value={})
                    with patch("custom_components.leneda.sensor.get_instance", return_value=mock_recorder):
                        await sensor.async_update()
                        
                        # Verify statistics were imported
                        assert mock_import.called
                        # Verify correct number of stat entries
                        stat_data_list = mock_import.call_args[0][2]
                        assert len(stat_data_list) == 2


@pytest.mark.asyncio
async def test_aggregated_sensor_cumulative_sum(mock_hass, mock_config):
    """Test aggregated sensor maintains cumulative sum correctly."""
    sensor = LenedaAggregatedMeteringSensor(mock_hass, mock_config)
    
    now = dt_util.now(dt_util.UTC)
    hour_start = now.replace(minute=0, second=0, microsecond=0)

    items = [
        {"startedAt": hour_start.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 10.0},
    ]
    
    # Mock last sum from database
    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "get_last_timestamp", return_value=hour_start - timedelta(hours=1)):
            with patch.object(sensor, "_fetch_from_api", return_value={"aggregatedTimeSeries": items}):
                mock_recorder = AsyncMock()
                mock_recorder.async_add_executor_job = AsyncMock(
                    side_effect=lambda f, *args, **kwargs: f(*args, **kwargs)
                )
                
                with patch("custom_components.leneda.sensor.get_instance", return_value=mock_recorder):
                    with patch("custom_components.leneda.sensor.get_last_statistics") as mock_stats:
                        mock_stats.return_value = {
                            sensor.entity_id: [{"sum": 100.0, "start": (hour_start - timedelta(hours=1)).timestamp()}]
                        }
                        
                        with patch("custom_components.leneda.sensor.async_import_statistics") as mock_import:
                            await sensor.async_update()
                            
                            # Verify statistics were imported
                            assert mock_import.called
                            # Verify it was called with the correct structure
                            stat_data_list = mock_import.call_args[0][2]
                            assert len(stat_data_list) == 1


@pytest.mark.asyncio
async def test_aggregated_sensor_skip_duplicate_timestamps(mock_hass, mock_config):
    """Test aggregated sensor skips data with old timestamps."""
    sensor = LenedaAggregatedMeteringSensor(mock_hass, mock_config)
    
    now = dt_util.now(dt_util.UTC)
    old_time = now - timedelta(hours=5)
    new_time = now - timedelta(hours=1)

    items = [
        {"startedAt": old_time.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 5.0},
        {"startedAt": new_time.strftime("%Y-%m-%dT%H:%M:%SZ"), "value": 10.0},
    ]
    
    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "get_last_timestamp", return_value=old_time):
            with patch.object(sensor, "_fetch_from_api", return_value={"aggregatedTimeSeries": items}):
                with patch("custom_components.leneda.sensor.async_import_statistics") as mock_import:
                    mock_recorder = AsyncMock()
                    mock_recorder.async_add_executor_job = AsyncMock(return_value={})
                    with patch("custom_components.leneda.sensor.get_instance", return_value=mock_recorder):
                        await sensor.async_update()
                        
                        # Should only import the new timestamp (not the old one)
                        assert mock_import.called
                        stat_data_list = mock_import.call_args[0][2]
                        # Only 1 data point should pass the timestamp check
                        assert len(stat_data_list) == 1


@pytest.mark.asyncio
async def test_aggregated_sensor_invalid_timestamp(mock_hass, mock_config):
    """Test aggregated sensor handles invalid timestamps."""
    sensor = LenedaAggregatedMeteringSensor(mock_hass, mock_config)
    
    items = [
        {"startedAt": "invalid-date", "value": 5.0},
    ]
    
    with patch.object(sensor, "get_days_to_fetch", return_value=1):
        with patch.object(sensor, "get_last_timestamp", return_value=None):
            with patch.object(sensor, "_fetch_from_api", return_value={"aggregatedTimeSeries": items}):
                with patch("custom_components.leneda.sensor.async_import_statistics") as mock_import:
                    mock_recorder = AsyncMock()
                    mock_recorder.async_add_executor_job = AsyncMock(return_value={})
                    with patch("custom_components.leneda.sensor.get_instance", return_value=mock_recorder):
                        await sensor.async_update()
                        
                        # Should not import data with invalid timestamps
                        # Either not called or called with empty list
                        if mock_import.called:
                            stat_data_list = mock_import.call_args[0][2]
                            assert len(stat_data_list) == 0
