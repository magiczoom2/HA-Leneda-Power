# Leneda Power
A small Home Assistant integration that imports power and energy statistics from the [Leneda API](https://www.leneda.lu/en/docs/api-reference#get-aggregated-metering-data) and exposes them as sensors with recorder statistics.

## Features
- `Power Demand` — 15-minute power measurements (kW) aggregated to hourly statistics with min, max and mean.
- `Energy Consumption` — hourly aggregated energy (kWh) statistics with cumulative sum and mean.

## Installation (Manual)
1. Copy the `leneda_power` folder into your Home Assistant `custom_components` directory so the path looks like `custom_components/leneda_power`.
2. Restart Home Assistant.
3. Go to Settings → Devices & Services → Add Integration and search for “Leneda Power”.

### Configuration options
When adding the integration you will be prompted for the following values:
- `metering_point` — your Leneda metering point identifier.
- `energy_id` — your Leneda energy identifier.
- `api_key` — Leneda API key.
- `obis_code` — OBIS code to read (default: `1-1:1.29.0`).


