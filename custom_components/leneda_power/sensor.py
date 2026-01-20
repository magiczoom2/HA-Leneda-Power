"""Leneda Historical Sensors - Power (kW) and Energy (kWh)."""
import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.recorder.statistics import StatisticData, StatisticMetaData

from homeassistant_historical_sensor import (
    HistoricalSensor, 
    HistoricalState, 
    PollUpdateMixin,
    group_by_interval
)
from .const import API_BASE_URL, CONF_API_KEY, CONF_ENERGY_ID, CONF_METERING_POINT, CONF_OBIS_CODE, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up both sensors."""
    async_add_entities([
        LenedaHistoricalPowerSensor(hass, entry.data),
        LenedaHistoricalEnergySensor(hass, entry.data)
    ], True)

class LenedaHistoricalBase(PollUpdateMixin, HistoricalSensor, SensorEntity):
    """Base class for shared API fetching logic."""
    _attr_has_entity_name = True
    _poll_interval = timedelta(minutes=15)

    def __init__(self, hass, config):
        self.hass = hass
        self._config = config
        self._attr_historical_states = []

    async def async_update_historical(self) -> None:
        """Fetch 15-min data (shared by Power and Energy sensors)."""
        session = async_get_clientsession(self.hass)
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=14)
        
        url = f"{API_BASE_URL}/metering-points/{self._config[CONF_METERING_POINT]}/time-series"
        params = {
            "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "obisCode": self._config[CONF_OBIS_CODE],
        }
        headers = {"X-API-KEY": self._config[CONF_API_KEY], "X-ENERGY-ID": self._config[CONF_ENERGY_ID]}

        try:
            async with session.get(url, params=params, headers=headers, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ts_data = data.get("items", [])
                    states = []
                    for item in ts_data:
                        ts_str = item["startedAt"].replace("Z", "+00:00")
                        dt = datetime.fromisoformat(ts_str)
                        states.append(HistoricalState(state=float(item["value"]), timestamp=dt.timestamp()))
                    self._attr_historical_states = states
        except Exception as err:
            _LOGGER.error("Leneda API error: %s", err)

class LenedaHistoricalPowerSensor(LenedaHistoricalBase):
    """kW Power Sensor - Represents the average load per hour."""
    _attr_name = "Power Demand"
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_device_class = SensorDeviceClass.POWER

    def __init__(self, hass, config):
        super().__init__(hass, config)
        self._attr_unique_id = f"{config[CONF_METERING_POINT]}_{config[CONF_OBIS_CODE]}_pwr_hourly"

    def get_statistic_metadata(self) -> StatisticMetaData:
        meta = super().get_statistic_metadata()
        meta["has_mean"] = True
        meta["has_sum"] = False
        return meta

    async def async_calculate_statistic_data(self, hist_states, *, latest=None) -> list[StatisticData]:
        ret = []
        for block_ts, collection_it in group_by_interval(hist_states, granularity=3600):
            collection = list(collection_it)
            if not collection: continue
            mean = statistics.mean([x.state for x in collection])
            ret.append(
                StatisticData(
                    start=datetime.fromtimestamp(block_ts, tz=timezone.utc), 
                    state=mean,
                    mean=mean
                )
            )
        return ret

class LenedaHistoricalEnergySensor(LenedaHistoricalBase):
    """kWh Energy Sensor - For the Home Assistant Energy Dashboard."""
    _attr_name = "Energy Consumption"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(self, hass, config):
        super().__init__(hass, config)
        self._attr_unique_id = f"{config[CONF_METERING_POINT]}_{config[CONF_OBIS_CODE]}_energy_hourly"

    def get_statistic_metadata(self) -> StatisticMetaData:
        meta = super().get_statistic_metadata()
        meta["has_mean"] = True
        meta["has_sum"] = True
        return meta

    async def async_calculate_statistic_data(self, hist_states, *, latest=None) -> list[StatisticData]:
        # Start from the last sum recorded in the DB
        accumulated = latest["sum"] if latest else 0
        ret = []
        
        # We MUST sort states to build the sum correctly
        sorted_states = sorted(hist_states, key=lambda x: x.timestamp)

        for block_ts, collection_it in group_by_interval(sorted_states, granularity=3600):
            collection = list(collection_it)
            if not collection: continue

            # Hourly Energy (kWh) = Average Power (kW) * 1 Hour
            hourly_energy = statistics.mean([x.state for x in collection])
            accumulated += hourly_energy

            ret.append(
                StatisticData(
                    start=datetime.fromtimestamp(block_ts, tz=timezone.utc),
                    state=hourly_energy,
                    sum=accumulated,
                    mean=hourly_energy
                )
            )
        return ret