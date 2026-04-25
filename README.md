# Leapmotor Vehicle Command Center

Web dashboard for monitoring and controlling Leapmotor vehicles via the Leapmotor Cloud API.

## Features

- **Live vehicle status**: Battery, range, speed, odometer, temperature, lock status
- **Remote controls**: Lock/unlock, trunk, windows, sunshade, climate (A/C, quick cool/heat, defrost), battery preheat, find car
- **Charge limit**: Adjustable charge limit slider
- **Vehicle details**: Doors, windows, tire pressure, climate, connectivity, ignition
- **Location**: OpenStreetMap embedded view with coordinates
- **Mileage & energy**: Delivery history, total mileage
- **Car picture**: View link when available
- **Raw data viewer**: Full JSON inspection for debugging
- **Multi-vehicle**: Tab switching for accounts with multiple vehicles

## Requirements

- Python 3.12+
- The `leapmotor-api` package (from the parent project)
- Leapmotor app certificate files (`.pem`)

## Quick Start

```bash
# From the project root
cd webapp
pip install -r requirements.txt
pip install -e ..

# Run the server
python main.py
```

Then open **http://localhost:8099** in your browser.

## Login

You will need:
- **Email & Password**: Your Leapmotor account credentials
- **App Certificate & Key**: Paths to the `.pem` files on the server
- **Vehicle PIN** (optional): Required for remote control actions (lock, unlock, climate, etc.)
- **P12 Password** (optional): Usually auto-derived from login response
