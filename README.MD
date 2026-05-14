# HARadiator OSC

Home Assistant custom integration for controlling Neon Captain Radiator over OSC.

This is a prepared **OSC-first beta** for the upcoming Radiator update that adds OSC support. Because the Radiator OSC update is not public yet, expect that some addresses, ranges, or ports may need small changes once the final OSC reference is published.

## What this version does

- Adds a Home Assistant config flow.
- Sends OSC messages to Radiator over UDP.
- Listens for OSC state feedback from Radiator over UDP.
- Creates preset buttons.
- Creates safe default entities for blackout, color, LFO, and Shape A/B controls.
- Includes the full OSC reference as disabled-by-default advanced entities when `Expose advanced entities` is enabled during setup.
- Adds a `haradiator.send_message` service so you can manually test new or changed OSC addresses before adding dedicated entities.

## Install

Copy this folder:

```text
custom_components/haradiator
```

into your Home Assistant config folder:

```text
/config/custom_components/haradiator
```

Then restart Home Assistant.

After restart, go to:

```text
Settings > Devices & services > Add integration > HARadiator
```

## Default ports

The defaults are placeholders based on the early OSC reference/screenshot:

```text
Radiator OSC receive port: 9000
Home Assistant OSC listen address: 0.0.0.0
Home Assistant OSC listen port: 9000
```

If Radiator and Home Assistant run on the same machine, they cannot both bind the same UDP receive port. In that case, change one side so Radiator sends feedback to the Home Assistant listen port and Home Assistant sends commands to the Radiator receive port.

## Safe defaults

By default, this integration enables only the safer/common entities:

- Preset buttons
- Master blackout
- HSV color values
- LFO speed/level/on/warp for LFO 1-3
- Shape A/B on, size, speed, and warp

Advanced entities are generated from the OSC spreadsheet but are disabled by default unless you enable `Expose advanced entities` during setup. Geometry correction, corner mesh, scale/offset, bias, and other setup/calibration controls should be treated carefully.

## Raw OSC testing service

Use Developer Tools > Services:

```yaml
service: haradiator.send_message
data:
  address: /radiator/master/blackout
  value: 1
```

Another example:

```yaml
service: haradiator.send_message
data:
  address: /radiator/color/hue
  value: 0.5
```

## Notes while waiting for the Radiator OSC update

This integration is intentionally prepared before the Radiator OSC release. Once the update lands, check:

1. Actual Radiator receive port.
2. Actual feedback/dump behavior.
3. Whether `/radiator/master/blackout` uses `1 = blackout` or `1 = output enabled`.
4. Whether parameters are normalized floats or have device-specific scaling.
5. Whether there is a command to request a full state dump.

## Development

The OSC endpoint definitions are in:

```text
custom_components/haradiator/const.py
```

The UDP OSC bridge is in:

```text
custom_components/haradiator/hub.py
```

Entity platforms are split into:

```text
button.py
number.py
sensor.py
switch.py
```

