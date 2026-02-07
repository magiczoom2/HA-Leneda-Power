"""Tests for Leneda config flow."""
import pytest
from unittest.mock import MagicMock, AsyncMock
import voluptuous as vol

from homeassistant.core import HomeAssistant

from custom_components.leneda.config_flow import LenedaConfigFlow
from custom_components.leneda.const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_ENERGY_ID,
    CONF_METERING_POINT,
    CONF_OBIS_CODE,
    CONF_INITIAL_SETUP_DAYS_TO_FETCH,
    DEFAULT_OBIS_CODE,
    DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH,
)


@pytest.fixture
def config_flow():
    """Create a LenedaConfigFlow instance."""
    flow = LenedaConfigFlow()
    flow.hass = MagicMock(spec=HomeAssistant)
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = MagicMock()
    flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})
    flow.async_show_form = MagicMock(return_value={"type": "form"})
    return flow


@pytest.fixture
def valid_user_input():
    """Create valid user input."""
    return {
        CONF_API_KEY: "test_api_key_123",
        CONF_ENERGY_ID: "energy_id_456",
        CONF_METERING_POINT: "metering_point_789",
        CONF_OBIS_CODE: "1-1:1.29.0",
        CONF_INITIAL_SETUP_DAYS_TO_FETCH: 180,
    }


@pytest.mark.asyncio
async def test_async_step_user_no_input(config_flow):
    """Test async_step_user with no input shows form."""
    result = await config_flow.async_step_user(user_input=None)

    config_flow.async_show_form.assert_called_once()
    call_args = config_flow.async_show_form.call_args
    assert call_args[1]["step_id"] == "user"
    assert CONF_API_KEY in call_args[1]["data_schema"].schema


@pytest.mark.asyncio
async def test_async_step_user_form_schema(config_flow):
    """Test that form schema has correct fields."""
    result = await config_flow.async_step_user(user_input=None)

    config_flow.async_show_form.assert_called_once()
    call_args = config_flow.async_show_form.call_args
    data_schema = call_args[1]["data_schema"]

    # Check that all required fields are in the schema
    assert vol.Required(CONF_API_KEY) in data_schema.schema
    assert vol.Required(CONF_ENERGY_ID) in data_schema.schema
    assert vol.Required(CONF_METERING_POINT) in data_schema.schema
    assert vol.Required(CONF_OBIS_CODE) in data_schema.schema
    assert vol.Required(CONF_INITIAL_SETUP_DAYS_TO_FETCH) in data_schema.schema


@pytest.mark.asyncio
async def test_async_step_user_form_defaults(config_flow):
    """Test that form has correct default values."""
    result = await config_flow.async_step_user(user_input=None)

    config_flow.async_show_form.assert_called_once()
    call_args = config_flow.async_show_form.call_args
    data_schema = call_args[1]["data_schema"]

    obis_field = vol.Required(CONF_OBIS_CODE, default=DEFAULT_OBIS_CODE)
    days_field = vol.Required(
        CONF_INITIAL_SETUP_DAYS_TO_FETCH, default=DEFAULT_INITIAL_SETUP_DAYS_TO_FETCH
    )

    assert obis_field in data_schema.schema
    assert days_field in data_schema.schema


@pytest.mark.asyncio
async def test_async_step_user_with_valid_input(config_flow, valid_user_input):
    """Test async_step_user with valid input creates entry."""
    await config_flow.async_step_user(user_input=valid_user_input)

    expected_unique_id = (
        f"{valid_user_input[CONF_METERING_POINT]}_{valid_user_input[CONF_OBIS_CODE]}"
    )
    config_flow.async_set_unique_id.assert_called_once_with(expected_unique_id)
    config_flow._abort_if_unique_id_configured.assert_called_once()
    config_flow.async_create_entry.assert_called_once()


@pytest.mark.asyncio
async def test_async_step_user_creates_entry_with_title(config_flow, valid_user_input):
    """Test that async_step_user creates entry with correct title."""
    await config_flow.async_step_user(user_input=valid_user_input)

    call_args = config_flow.async_create_entry.call_args
    unique_id = (
        f"{valid_user_input[CONF_METERING_POINT]}_{valid_user_input[CONF_OBIS_CODE]}"
    )
    expected_title = f"Leneda {unique_id}"
    assert call_args[1]["title"] == expected_title
    assert call_args[1]["data"] == valid_user_input


@pytest.mark.asyncio
async def test_async_step_user_with_custom_obis_code(config_flow):
    """Test async_step_user with custom OBIS code."""
    user_input = {
        CONF_API_KEY: "test_key",
        CONF_ENERGY_ID: "energy_id",
        CONF_METERING_POINT: "metering_point",
        CONF_OBIS_CODE: "1-1:2.29.0",  # Production OBIS code
        CONF_INITIAL_SETUP_DAYS_TO_FETCH: 90,
    }

    await config_flow.async_step_user(user_input=user_input)

    config_flow.async_create_entry.assert_called_once()
    call_args = config_flow.async_create_entry.call_args
    assert call_args[1]["data"][CONF_OBIS_CODE] == "1-1:2.29.0"


@pytest.mark.asyncio
async def test_config_flow_version():
    """Test that LenedaConfigFlow has correct VERSION."""
    assert LenedaConfigFlow.VERSION == 1


@pytest.mark.asyncio
async def test_unique_id_format(config_flow, valid_user_input):
    """Test that unique ID is formatted correctly."""
    await config_flow.async_step_user(user_input=valid_user_input)

    call_args = config_flow.async_set_unique_id.call_args[0][0]
    assert valid_user_input[CONF_METERING_POINT] in call_args
    assert valid_user_input[CONF_OBIS_CODE] in call_args
    assert "_" in call_args
