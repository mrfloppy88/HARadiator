# HARadiator (Home Assistant / HACS)

Controls the Radiator laser controller over TCP (port 4815).

## Features
- Service: `radiator.recall_preset` (global preset 1..1000 mapped to page + slot)
- Buttons: Preset 1..10
- Config flow: host + port

## Manual install
Copy `custom_components/radiator` into your Home Assistant `/config/custom_components/` folder and restart HA.

## HACS install
Add this repository as a custom repository (category: Integration) and install.
