# Yunmai Scale Integration for Home Assistant

A custom component for Home Assistant that integrates Yunmai body scales using Bluetooth Low Energy (BLE).

## Features

- Automatically discovers Yunmai scales in BLE range
- Displays weight and body composition metrics
- Supports user-specific configuration (gender, height, age)
- Customizable scan interval

## Tested Models

- Yunmai SE 3S (YMBS-M267)

## Supported Models

- Yunmai SE 3S
- Yunmai Mini 2S

## Installation

1. Copy the `custom_components/yunmai_scale` folder to your Home Assistant's `custom_components` directory.
2. Restart Home Assistant.
3. Go to Configuration -> Integrations -> Add Integration and search for "Yunmai Scale".
4. Follow the setup wizard to configure your scale.

## Available Sensors

- **Weight**: Current weight in kg
- **BMI**: Body Mass Index
- **Body Fat**: Body fat percentage
- **Muscle Mass**: Muscle mass percentage
- **Water Percentage**: Body water percentage
- **Bone Mass**: Bone mass in kg
- **Skeletal Muscle**: Skeletal muscle percentage
- **Lean Body Mass**: Lean body mass in kg
- **Visceral Fat**: Visceral fat level
- **Scale Status**: Current status of the scale (measuring, stable, idle)

## Requirements

- Home Assistant 2024.12.5 or newer
- A compatible Yunmai scale
- Bluetooth adapter that supports BLE

## Thanks

Thanks to the following open source projects and resources:

- [yunmai-mqtt](https://github.com/Paxy/yunmai-mqtt) - For providing integration between Yunmai scales and MQTT systems
- [openScale](https://github.com/oliexdev/openScale) - Open source weight and body metrics tracking application
- [https://bbs.hassbian.com/thread-14002-1-1.html](https://bbs.hassbian.com/thread-14002-1-1.html) - `Yunmai` scale ble advertisement data parse
