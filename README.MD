# HARadiator

HARadiator is a Home Assistant custom integration for controlling **Neon Captain Radiator** over OSC.

The integration is mainly built for show-control workflows where Home Assistant needs to trigger Radiator presets, control blackout, and receive status feedback from Radiator. It is still in beta, but basic OSC sending and receiving is working.

At the moment the integration keeps the control side intentionally simple. It creates a preset selector, a global blackout switch, a manual OSC service, and read-only sensors for OSC feedback coming back from Radiator.

## Current state

HARadiator currently provides a preset dropdown through `select.radiator_preset`, a global blackout switch through `switch.radiator_blackout`, and read-only feedback sensors using the `sensor.radiator_read_*` naming pattern.

There is also a manual service called `haradiator.send_message`. This service is useful for testing OSC addresses directly from Home Assistant’s Developer Tools.

The read sensors are passive. They only update when Radiator sends OSC feedback. Radiator usually sends a large burst of feedback when changing presets, so switching presets is a good way to populate the sensors after startup.

## Requirements

You need Home Assistant, HACS, and a Radiator version with OSC support enabled. Home Assistant and the Radiator machine need to be able to reach each other on the network, and UDP traffic must be allowed between them.

The default setup assumes Radiator receives OSC on port `8000` and sends OSC feedback to Home Assistant on port `9000`.

## Installing with HACS

Add this repository to HACS as a custom integration repository:

```text
https://github.com/mrfloppy88/HARadiator
```

Use `Integration` as the category.

After adding the repository, install HARadiator from HACS and restart Home Assistant. Once Home Assistant has restarted, add the integration from **Settings > Devices & services**.

## Radiator OSC settings

In Radiator, enable OSC RX and OSC TX.

The recommended Radiator settings are:

| Radiator setting | Value                  |
| ---------------- | ---------------------- |
| OSC RX           | On                     |
| OSC Port         | `8000`                 |
| OSC TX           | On                     |
| OSC TX IP        | Your Home Assistant IP |
| OSC TX Port      | `9000`                 |

The important thing to remember is that Radiator’s RX port is where Radiator receives commands. HARadiator sends to this port.

Radiator’s TX settings are used for feedback. The TX IP must be the IP address of your Home Assistant machine, otherwise the feedback sensors in Home Assistant will not update.

A typical setup looks like this:

```text
Radiator IP:       192.168.1.152
Home Assistant IP: 192.168.1.100
Radiator OSC RX:   8000
Radiator OSC TX:   9000
```

## HARadiator settings

When adding HARadiator in Home Assistant, use the Radiator machine IP as the host.

| HARadiator setting | Value               |
| ------------------ | ------------------- |
| Host               | Radiator machine IP |
| Send port          | `8000`              |
| Listen host        | `0.0.0.0`           |
| Listen port        | `9000`              |

For example:

| HARadiator setting | Example         |
| ------------------ | --------------- |
| Host               | `192.168.1.152` |
| Send port          | `8000`          |
| Listen host        | `0.0.0.0`       |
| Listen port        | `9000`          |

In short, Home Assistant sends commands to Radiator on port `8000`, and Radiator sends feedback back to Home Assistant on port `9000`.

## Changing settings later

HARadiator supports Home Assistant’s configure/options flow. This means you do not need to remove and re-add the integration just to change the host or port settings.

Open **Settings > Devices & services**, select **HARadiator**, and choose **Configure**. After saving changes, Home Assistant should reload the integration with the new settings.

## Preset control

The main control entity is:

```text
select.radiator_preset
```

This selector is intended to support up to 1000 Radiator presets.

Example automation action:

```yaml
action: select.select_option
target:
  entity_id: select.radiator_preset
data:
  option: "Preset 1"
```

This can be used to build preset playlists, time-based changes, scene triggers, or show-control automations.

## Blackout control

The global blackout entity is:

```text
switch.radiator_blackout
```

To turn blackout on:

```yaml
action: switch.turn_on
target:
  entity_id: switch.radiator_blackout
```

To turn blackout off:

```yaml
action: switch.turn_off
target:
  entity_id: switch.radiator_blackout
```

Blackout control from Home Assistant is useful, but it should not replace proper physical laser safety controls.

## Read-only feedback sensors

HARadiator can expose Radiator OSC feedback as Home Assistant sensors. These usually appear as:

```text
sensor.radiator_read_*
```

These sensors can include preset state, master values, color values, LFO values, shape values, transform values, clone values, and other Radiator feedback addresses.

The sensors only update when Radiator sends OSC data. If the sensors stay unknown after startup, change a preset or parameter in Radiator. That usually causes Radiator to send a larger feedback update.

You can disable sensors you do not need from Home Assistant’s entity settings. Search for `radiator_read` in **Settings > Devices & services > Entities**.

## Manual OSC service

HARadiator includes a manual OSC service:

```text
haradiator.send_message
```

This is useful for testing OSC commands from **Developer Tools > Actions**.

Blackout on:

```yaml
action: haradiator.send_message
data:
  address: /radiator/master/blackout
  value: "1.0"
```

Blackout off:

```yaml
action: haradiator.send_message
data:
  address: /radiator/master/blackout
  value: "0.0"
```

Switch to preset 2:

```yaml
action: haradiator.send_message
data:
  address: /radiator/preset
  value: "2.0"
```

Change LFO 1 speed:

```yaml
action: haradiator.send_message
data:
  address: /radiator/lfo1/speed
  value: "1.0"
```

Radiator appears to report most numeric values as floats, including values that behave like on/off states. For that reason, values like `"1.0"` and `"0.0"` are recommended when testing manually.

## Example preset playlist

This example cycles through four presets with a delay between each one.

```yaml
alias: Radiator Preset Playlist
mode: restart
sequence:
  - action: select.select_option
    target:
      entity_id: select.radiator_preset
    data:
      option: "Preset 1"

  - delay:
      seconds: 30

  - action: select.select_option
    target:
      entity_id: select.radiator_preset
    data:
      option: "Preset 2"

  - delay:
      seconds: 30

  - action: select.select_option
    target:
      entity_id: select.radiator_preset
    data:
      option: "Preset 3"

  - delay:
      seconds: 30

  - action: select.select_option
    target:
      entity_id: select.radiator_preset
    data:
      option: "Preset 4"
```

## Troubleshooting OSC sending

If Home Assistant sends commands but Radiator does not react, first check that Radiator OSC RX is enabled. HARadiator must send to the Radiator machine IP, and the send port must match Radiator’s OSC RX port. In the default setup this is port `8000`.

Also check the firewall on the Radiator machine. It must allow incoming UDP traffic on the OSC RX port.

A correct default command path looks like this:

```text
Home Assistant -> Radiator IP -> UDP 8000
```

If you are unsure whether Home Assistant is sending OSC at all, Protokol by Hexler is useful for testing. Run Protokol on a PC, temporarily point HARadiator at that PC’s IP, and check whether the OSC messages arrive.

## Troubleshooting OSC feedback

If commands work but sensors stay unknown, the problem is usually on the Radiator TX side.

Radiator must have OSC TX enabled, and the OSC TX IP must be the Home Assistant IP. The Radiator TX port must match HARadiator’s listen port. In the default setup this is port `9000`.

A correct default feedback path looks like this:

```text
Radiator -> Home Assistant IP -> UDP 9000
```

Make sure no other application or integration is already listening on the same UDP port. Only one process can listen on a UDP port at a time.

After changing the TX settings, change a preset in Radiator to force a feedback update.

## HACS download issues

If HACS does not seem to install the newest version, make sure the latest commit is pushed to the `main` branch on GitHub. Then use **Redownload** in HACS and restart Home Assistant.

If HACS keeps downloading the wrong version, remove the custom repository from HACS, restart Home Assistant, add the repository again, and reinstall the integration.

The installed files can be checked in:

```text
/config/custom_components/haradiator/
```

The installed manifest is here:

```text
/config/custom_components/haradiator/manifest.json
```

If Home Assistant blocks the integration because of an invalid version, check the version field in `manifest.json`. Valid examples are:

```json
"version": "0.3.0-beta.1"
```

```json
"version": "0.3.1"
```

A version like this is not valid for Home Assistant:

```json
"version": "0.3RC1"
```

## Common OSC addresses

| Purpose                 | OSC address                 | Example value         |
| ----------------------- | --------------------------- | --------------------- |
| Set preset              | `/radiator/preset`          | `"1.0"`               |
| Current preset feedback | `/radiator/preset/current`  | `1.0`                 |
| Blackout                | `/radiator/master/blackout` | `"1.0"` or `"0.0"`    |
| Master level            | `/radiator/master/level`    | `1.0`                 |
| Master size             | `/radiator/master/size`     | `0.5`                 |
| LFO 1 speed             | `/radiator/lfo1/speed`      | `1.0`                 |
| LFO 1 on/off            | `/radiator/lfo1/on`         | `1.0` or `0.0`        |
| Color hue               | `/radiator/color/hue`       | `0.5`                 |
| Color mode name         | `/radiator/color/mode/name` | `HSV`                 |
| Ether Dream status      | `/radiator/ed/status`       | `Online` or `Offline` |

## Development notes

HARadiator uses `python-osc` for UDP OSC communication.

The integration is local-only and uses Home Assistant’s `local_push` IoT class.

Default ports:

```text
Radiator RX / HARadiator send:     8000
Radiator TX / HARadiator listen:   9000
```

## Safety note

Laser control can be safety-critical. This integration is experimental and should not be used as the only safety mechanism for laser output.

Home Assistant blackout control is useful for automation, but it should not replace physical emergency stops, key switches, interlocks, scan-fail protection, or any other required laser safety systems.

## License

This project is released under the MIT License.

Do whatever you want with it, just keep the license text included. The software is provided as-is, without warranty.
