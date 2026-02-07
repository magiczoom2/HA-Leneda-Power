"""Tests for Leneda integration initialization."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from custom_components.leneda import (
    async_setup_entry,
    async_unload_entry,
    PLATFORMS,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Test Leneda",
        data={
            "metering_point": "123456",
            "energy_id": "energy_123",
            "api_key": "test_key",
            "obis_code": "1-1:1.29.0",
            "days_to_fetch_during_initial_setup": 180,
        },
        options={},
        entry_id="test_entry_123",
        source="user",
        discovery_keys=None,
        subentries_data={},
        unique_id=None,
    )


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=None)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_config_entry):
    """Test async_setup_entry."""
    result = await async_setup_entry(mock_hass, mock_config_entry)

    assert result is True
    assert DOMAIN in mock_hass.data
    mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
        mock_config_entry, PLATFORMS
    )


@pytest.mark.asyncio
async def test_async_setup_entry_initializes_domain_data(mock_hass, mock_config_entry):
    """Test that async_setup_entry initializes domain data."""
    await async_setup_entry(mock_hass, mock_config_entry)

    assert mock_hass.data[DOMAIN] == {}


@pytest.mark.asyncio
async def test_async_unload_entry(mock_hass, mock_config_entry):
    """Test async_unload_entry."""
    result = await async_unload_entry(mock_hass, mock_config_entry)

    assert result is True
    mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
        mock_config_entry, PLATFORMS
    )


@pytest.mark.asyncio
async def test_platforms_constant():
    """Test PLATFORMS constant."""
    assert Platform.SENSOR in PLATFORMS
    assert len(PLATFORMS) == 1
