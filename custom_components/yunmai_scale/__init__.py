"""The Yunmai Scale integration."""

import asyncio
import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol
from bleak import BleakError, BleakScanner
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AGE,
    CONF_GENDER,
    CONF_HEIGHT,
    CONF_IS_ACTIVE,
    DOMAIN,
    SCAN_INTERVAL,
    SERVICE_UUID_PREFIX,
)
from .parse_data import process_data

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Yunmai Scale from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = YunmaiDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class YunmaiDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Yunmai Scale data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the data coordinator."""
        self.entry = entry
        self.mac_address = entry.data.get(CONF_MAC)
        self.user_info = {
            CONF_GENDER: entry.data.get(CONF_GENDER, 1),  # 1 for male, 0 for female
            CONF_HEIGHT: entry.data.get(CONF_HEIGHT, 170),
            CONF_IS_ACTIVE: entry.data.get(CONF_IS_ACTIVE, False),
            CONF_AGE: entry.data.get(CONF_AGE, 30),
        }
        self._last_data = {}
        self._device_info = {
            "name": entry.data.get(CONF_NAME, "Yunmai Scale"),
            "model": "Yunmai Scale",
            "manufacturer": "Yunmai",
            "identifiers": {(DOMAIN, self.mac_address)},
        }

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.mac_address}",
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self._device_info

    async def _async_update_data(self) -> dict:
        """Scan for BLE advertisements from Yunmai scale and process the data."""
        try:
            detected_data = {}

            def detection_callback(device, advertisement_data):
                """Process advertisement data."""
                if not device or not advertisement_data:
                    return

                # Check for matching services
                matching_services = {
                    service_uuid
                    for service_uuid in advertisement_data.service_uuids
                    if str(service_uuid).startswith(SERVICE_UUID_PREFIX)
                }

                if not matching_services:
                    return

                # Check manufacturer data
                for mfr_id, mfr_data in advertisement_data.manufacturer_data.items():
                    # Compute MAC from manufacturer data if needed
                    manufacturer_data_hex = (
                        mfr_id.to_bytes(2, "little").hex() + mfr_data.hex()
                    )
                    device_mac = ':'.join(
                        manufacturer_data_hex[:12].upper()[i : i + 2]
                        for i in range(10, -2, -2)
                    )

                    if device_mac.upper() == self.mac_address.upper():
                        data_hex = mfr_data.hex()
                        processed_data = process_data(
                            data_hex,
                            self.user_info[CONF_AGE],
                            self.user_info[CONF_GENDER],
                            self.user_info[CONF_HEIGHT],
                            self.user_info[CONF_IS_ACTIVE],
                        )
                        if processed_data:
                            nonlocal detected_data
                            detected_data = processed_data

            scanner = BleakScanner(detection_callback=detection_callback)

            # Start scanning
            await scanner.start()
            _LOGGER.debug("Scanning for Yunmai scale advertisements")

            # Scan for a few seconds
            await asyncio.sleep(5)

            # Stop scanning
            await scanner.stop()

            # Return data if we found something
            if detected_data:
                self._last_data = detected_data
                return detected_data

            # Return last known data if we have it
            if self._last_data:
                return self._last_data

            # Return empty if no data found
            return {}

        except BleakError as err:
            raise UpdateFailed(f"Error communicating with Yunmai Scale: {err}") from err
