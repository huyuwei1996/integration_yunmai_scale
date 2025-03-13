#!/usr/bin/env python3
import asyncio
import signal

from bleak import BleakScanner

from custom_components.yunmai_scale.const import SERVICE_UUID_PREFIX
from custom_components.yunmai_scale.parse_data import process_data

sex = 1  # 1=Male, 2=Female
height = 170
veryActive = True
age = 25


# Global variables for stopping the scan
scanner = None
should_continue = True


def handle_sigint(signal, frame):
    """Handle Ctrl+C interrupt signal"""
    global should_continue
    print("\nStopping scan...")
    should_continue = False


async def detection_callback(device, advertisement_data):
    """Callback function called each time a device broadcast is detected"""
    for mfr_id, mfr_data in advertisement_data.manufacturer_data.items():
        # print(
        #     f"Detected device: {device.name}, Service UUID: {advertisement_data.service_uuids}"
        # )

        # Check if this is the target device
        matching_services = {
            service_uuid
            for service_uuid in advertisement_data.service_uuids
            if str(service_uuid).startswith(SERVICE_UUID_PREFIX)
        }

        if matching_services:
            # Calculate device MAC
            manufacturer_data_hex = mfr_id.to_bytes(2, "little").hex() + mfr_data.hex()
            device_mac = ':'.join(
                manufacturer_data_hex[:12].upper()[i : i + 2] for i in range(10, -2, -2)
            )
            print(f"Detected device MAC: {device_mac}")
            print("Broadcast data: ", mfr_data.hex())

            # Process the received data
            print(process_data(mfr_data.hex()))
            print("-" * 40)


async def main():
    global scanner, should_continue

    try:
        # Register signal handler
        signal.signal(signal.SIGINT, handle_sigint)

        print("Starting continuous scan for Yunmai scale...")
        scanner = BleakScanner(detection_callback=detection_callback)

        # Start scanning
        await scanner.start()
        print("Scanning started, press Ctrl+C to stop")

        # Keep program running until user interrupts
        while should_continue:
            await asyncio.sleep(1)

    except Exception as e:
        print(f'Error: "{e}"')
    finally:
        # Ensure scanner stops
        if scanner:
            await scanner.stop()
        print("Scanning stopped")


if __name__ == "__main__":
    asyncio.run(main())
