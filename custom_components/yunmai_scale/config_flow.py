"""Config flow for Yunmai Scale integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol
from bluetooth_data_tools import short_address
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS, CONF_NAME
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


def format_unique_id(address: str) -> str:
    """Format the unique ID."""
    return address.replace(":", "").lower()


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
        name = f"Yunmai Scale {short_address(address)}"

        # Check if this device is already configured
        await self.async_set_unique_id(format_unique_id(address))
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
            CONF_ADDRESS: address,
        }

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device or manual entry."""
        errors = {}

        if user_input is not None:
            if CONF_ADDRESS in user_input:
                mac = user_input[CONF_ADDRESS].upper()

                # Validate MAC address format
                if MAC_REGEX.match(mac):
                    await self.async_set_unique_id(format_unique_id(mac))
                    self._abort_if_unique_id_configured()

                    self.selected_device = {
                        CONF_NAME: user_input.get(
                            CONF_NAME, f"Yunmai Scale {short_address(mac)}"
                        ),
                        CONF_ADDRESS: mac,
                    }
                    return await self.async_step_user_settings()
                else:
                    errors[CONF_ADDRESS] = "invalid_mac"
            elif user_input.get("use_discovered") and self.discovered_devices:
                # User selected a discovered device
                selected_mac = user_input["discovered_device"]
                await self.async_set_unique_id(format_unique_id(selected_mac))
                self._abort_if_unique_id_configured()

                self.selected_device = {
                    CONF_NAME: f"Yunmai Scale {short_address(selected_mac)}",
                    CONF_ADDRESS: selected_mac,
                }
                return await self.async_step_user_settings()

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
                    vol.Required(CONF_NAME, default="Yunmai Scale"): str,
                    vol.Required(
                        CONF_ADDRESS,
                        description={"suggested_value": "AA:BB:CC:DD:EE:FF"},
                    ): str,
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

            entry_title = f"Yunmai Scale {short_address(data[CONF_ADDRESS])}"

            return self.async_create_entry(
                title=entry_title,
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

        if not self.selected_device:
            return self.async_abort(reason="no_device_selected")

        display_name = (
            f"Yunmai Scale {short_address(self.selected_device[CONF_ADDRESS])}"
        )
        return self.async_show_form(
            step_id="user_settings",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "name": display_name,
                "mac": self.selected_device[CONF_ADDRESS],
            },
        )
