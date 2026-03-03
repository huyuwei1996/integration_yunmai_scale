"""The Yunmai Scale integration."""

import logging
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_AGE,
    CONF_GENDER,
    CONF_HEIGHT,
    CONF_IS_ACTIVE,
    DOMAIN,
    SERVICE_UUID,
)
from .parse_data import process_data

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Yunmai Scale from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = YunmaiDataCoordinator(hass, entry)

    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(
        async_register_callback(
            hass,
            coordinator.async_handle_bluetooth_event,
            BluetoothCallbackMatcher(service_uuid=SERVICE_UUID),
            BluetoothScanningMode.PASSIVE,
        )
    )

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
        self.mac_address = entry.data.get(CONF_ADDRESS)
        self.user_info = {
            CONF_GENDER: entry.data.get(CONF_GENDER, 1),  # 1 for male, 0 for female
            CONF_HEIGHT: entry.data.get(CONF_HEIGHT, 170),
            CONF_IS_ACTIVE: entry.data.get(CONF_IS_ACTIVE, False),
            CONF_AGE: entry.data.get(CONF_AGE, 30),
        }
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
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return self._device_info

    async def _async_update_data(self) -> dict:
        """No-op: data is pushed via Bluetooth callbacks."""
        return self.data or {}

    @callback
    def async_handle_bluetooth_event(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Handle a Bluetooth event from Home Assistant."""
        _LOGGER.debug(
            "Received Bluetooth event from %s (change=%s)",
            service_info.address,
            change,
        )

        for mfr_id, mfr_data in service_info.advertisement.manufacturer_data.items():
            # Compute MAC from manufacturer data
            manufacturer_data_hex = (
                mfr_id.to_bytes(2, "little").hex() + mfr_data.hex()
            )
            device_mac = ':'.join(
                manufacturer_data_hex[:12].upper()[i : i + 2]
                for i in range(10, -2, -2)
            )

            if device_mac.upper() != self.mac_address.upper():
                continue

            data_hex = mfr_data.hex()
            processed_data = process_data(
                data_hex,
                self.user_info[CONF_AGE],
                self.user_info[CONF_GENDER],
                self.user_info[CONF_HEIGHT],
                self.user_info[CONF_IS_ACTIVE],
            )
            if processed_data:
                self.async_set_updated_data(processed_data)
                return
