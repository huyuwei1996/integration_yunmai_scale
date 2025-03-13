"""Config flow for Yunmai Scale integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from bleak import BleakScanner
from homeassistant import config_entries
from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_AGE,
    CONF_GENDER,
    CONF_HEIGHT,
    CONF_IS_ACTIVE,
    DOMAIN,
    SERVICE_UUID_PREFIX,
)

_LOGGER = logging.getLogger(__name__)

MAC_REGEX = re.compile(r"^([0-9A-F]{2}:){5}([0-9A-F]{2})$")


class YunmaiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yunmai Scale."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self.discovered_devices = {}
        self.selected_device = None

    async def async_step_bluetooth(self, discovery_info) -> FlowResult:
        """Handle the bluetooth discovery step."""
        # Extract necessary information from discovery
        address = discovery_info.address
        name = discovery_info.name or "Yunmai Scale"

        # Check if this device is already configured
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        # Check if it's a Yunmai scale
        is_yunmai = False
        for service_uuid in discovery_info.advertisement.service_uuids:
            if str(service_uuid).startswith(SERVICE_UUID_PREFIX):
                is_yunmai = True
                break

        if not is_yunmai:
            return self.async_abort(reason="not_yunmai_device")

        # Store device for later steps
        self.discovered_devices[address] = name
        self.selected_device = {
            CONF_NAME: name,
            CONF_MAC: address,
        }

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device or manual entry."""
        errors = {}

        if user_input is not None:
            if CONF_MAC in user_input:
                mac = user_input[CONF_MAC].upper()

                # Validate MAC address format
                if MAC_REGEX.match(mac):
                    await self.async_set_unique_id(mac)
                    self._abort_if_unique_id_configured()

                    self.selected_device = {
                        CONF_NAME: user_input.get(CONF_NAME, "Yunmai Scale"),
                        CONF_MAC: mac,
                    }
                    return await self.async_step_user_settings()
                else:
                    errors[CONF_MAC] = "invalid_mac"
            elif user_input.get("use_discovered") and self.discovered_devices:
                # User selected a discovered device
                selected_mac = user_input["discovered_device"]
                await self.async_set_unique_id(selected_mac)
                self._abort_if_unique_id_configured()

                self.selected_device = {
                    CONF_NAME: self.discovered_devices[selected_mac],
                    CONF_MAC: selected_mac,
                }
                return await self.async_step_user_settings()

        # If no discovered devices yet, try to discover
        if not self.discovered_devices:
            await self._discover_devices()

        # If we have discovered devices, show them as options
        if self.discovered_devices:
            schema = vol.Schema(
                {
                    vol.Required("use_discovered", default=True): bool,
                    vol.Optional("discovered_device"): vol.In(
                        {
                            mac: f"{name} ({mac})"
                            for mac, name in self.discovered_devices.items()
                        }
                    ),
                }
            )
        else:
            # Otherwise, show manual entry form
            schema = vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_MAC): str,
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_user_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user settings input."""
        errors = {}
        if user_input is not None:
            # Create final configuration and finish flow
            data = {
                **self.selected_device,
                CONF_GENDER: user_input.get(CONF_GENDER, 1),
                CONF_HEIGHT: user_input.get(CONF_HEIGHT, 170),
                CONF_IS_ACTIVE: user_input.get(CONF_IS_ACTIVE, False),
                CONF_AGE: user_input.get(CONF_AGE, 30),
            }

            return self.async_create_entry(
                title=data[CONF_NAME],
                data=data,
            )

        # Show form for user settings
        schema = vol.Schema(
            {
                vol.Required(CONF_GENDER, default=1): vol.In({1: "Male", 0: "Female"}),
                vol.Required(CONF_HEIGHT, default=170): vol.All(
                    vol.Coerce(int), vol.Range(min=100, max=220)
                ),
                vol.Required(CONF_AGE, default=30): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=99)
                ),
                vol.Required(CONF_IS_ACTIVE, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user_settings",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "name": self.selected_device[CONF_NAME],
                "mac": self.selected_device[CONF_MAC],
            },
        )

    async def _discover_devices(self) -> None:
        """Discover Yunmai BLE devices."""
        self.discovered_devices = {}

        # Scan for devices
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name and (
                "yunmai" in device.name.lower() or "scale" in device.name.lower()
            ):
                self.discovered_devices[device.address] = device.name
