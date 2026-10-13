# Hardware plan — revision A.2

## Architecture

One central controller supports ten independent host channels. Each PC has a passive pass-through adapter between its motherboard front-panel signals and its original case wiring. Four signal pairs and one host reference return to the controller via a dedicated locking harness.

The controller illustration has a provisional 280 × 220 mm envelope. Component packages, clearances, mounting positions and enclosure dimensions are placeholders. No traces in the illustration are PCB routing. Each host adapter is passive and unpowered; a custom Y harness may replace it.

## Custom host connector

The table below is a SIGNAL ALLOCATION LIST, not a cavity-location or mating-face drawing. The manufacturer drawing and physical pin-1 marking must be checked before harness fabrication. Do not infer contact orientation or a solder-side mirror from this table.

| Left | Right |
|---|---|
| 1 — PWR_A | 2 — PWR_B |
| 3 — RST_A | 4 — RST_B |
| 5 — PLED+ | 6 — PLED− |
| 7 — HDD+ | 8 — HDD− |
| 9 — HOST_REF | 10 — NC |

This is a project-defined connector. Motherboard signal locations must be read from the specific board manual. Host reference must be independently verified; neither LED negative terminal may be assumed to be ground. Do not merge grounds across channels or connect HOST_REF to controller ground. No controller supply voltage is intentionally sent to motherboard front-panel headers.

## Preserve original controls

POWER and RESET each retain a direct connection to their original case switch. A normally-open isolated photorelay connects across the same two contacts. Controller boot, reset and loss of power must leave these contacts open. Hardware-bounded pulse duration and watchdog gating remain to be designed. A TLP3122A is a candidate, not a finalized purchasing choice or footprint.

Both original LEDs also remain directly connected. A protected high-impedance differential branch observes voltage across each LED without using LED− as a shared ground. Each host's active sensing electronics receive independently isolated, regulated power and report through an isolation barrier. Include current-limiting near the tap, input protection, hysteresis, and measures to prevent unacceptable loading/backfeed when the controller is unpowered. The real sensor resistor values, common-mode range and thresholds require measurement on the target board. An ordinary optocoupler directly paralleled with an LED does not guarantee preserved brightness.

The passive pass-through path stays functional when the controller is unpowered under normal operation; this is not a guarantee against every component or cable short-circuit fault. Check branch-fault behavior during circuit design.

## Cable and installation

Revision A.2 candidate parts, verified against manufacturer specifications:

| Function | Part | Quantity for 10 hosts | Selection basis |
|---|---|---:|---|
| Board header at controller and passive adapter | Molex 43045-1000 | 20 | 10 circuits, 3 mm pitch, right-angle through-hole |
| Cable receptacle housing, both ends | Molex 43025-1000 | 20 | 10 circuits, polarized and locking |
| Female crimp contact | Molex 43030-0007 | 180 populated + spares | 24–20 AWG, insulation diameter up to 1.85 mm |
| Bulk cable | Belden 9505 | Cut to actual lengths | 5 twisted pairs, 24 AWG stranded, 1.1 mm conductor insulation diameter, overall foil shield, 7.34 mm outside diameter |

The cable and contact wire ranges are compatible on paper; crimp tooling, strip length, pull-force, insulation grip, cavity geometry and strain relief still require samples and the manufacturer application drawings. This is a custom harness, not a pre-made cable assembly with a single purchase number. The 3D header is a simplified shape, not an imported manufacturer STEP model.

Pair assignment: red/black → pins 1/2; white/black → 3/4; green/black → 5/6; blue/black → 7/8; fifth-pair black → 9. Insulate the fifth-pair yellow conductor at BOTH ends; leave pin 10 without a terminal. Identify black wires by their original twisted pair, and label after breakout. The foil/drain wire is separate from all ten contacts. Prototype shield termination is to controller enclosure at one end, with the PC end insulated, subject to EMI/ESD testing; it must not replace HOST_REF or connect isolated signal grounds.

Keep external cable strain on an enclosure clamp, not on the PCB connector. Motherboard-side 2.54 mm connector series and exact harness length remain TBD until target board headers are confirmed.

Manufacturer references: [43045-1000](https://www.molex.com/en-us/products/part-detail/430451000), [43025-1000](https://www.molex.com/en-us/products/part-detail/430251000), [43030-0007](https://www.molex.com/en-us/products/part-detail/430300007), [Belden 9505](https://www.belden.com/products/cable/electronic-wire-cable/multi-pair-cable/9505).

- Four signal pairs plus HOST_REF, with one unused position in a keyed 10-pin connector. This requires a dedicated multi-conductor harness, not an unmodified 8-conductor Ethernet patch cable.
- Use labeled 2.54 mm motherboard leads only inside the enclosure, with strain relief and a secured pass-through adapter.
- Initial 1–3 m harness length is a prototype test target, not a supported maximum. Assess EMI, ESD, disconnect behavior and LED pulse capture with actual harnesses.
- If longer runs are required, move sensing/control to an active local adapter and redesign the cable as a differential communications link. RS-485 topology and termination must be designed; do not create an unbuffered long star bus.
- Separate dedicated J01–J10 harness connectors from the real Ethernet LAN jack.

## Controller blocks

ESP32-S3, W5500 with magnetics, three MCP23S17 expanders (48 I/O total), 20 photorelays, 20 LED sensing channels with isolated returns, ten host-domain isolated power supplies, independent external power and onboard regulators. All part numbers are candidates. Do not order a full BOM from the visual model.

The 40 functional signals fit the three expanders. The final assignment must also account for interrupt handling and pulse capture; HDD activity should be stretched or latched if ordinary polling would miss it. HDD LED activity is not a drive health or OS health metric.

Long-press POWER is motherboard soft-power control, not removal of AC or standby power. Actual AC power cycling would be a separate PDU function.

## Validation before PCB manufacture

1. Confirm each motherboard's actual switch and LED pinout, LED polarity and operating voltage/current.
2. Verify original buttons and LED brightness with the controller on, off, rebooting and disconnected.
3. Measure powered and unpowered sensor loading, backfeed, isolation, and branch-short behavior.
4. Verify power/reset pulse timing and hardware release after MCU or I/O failure.
5. Check short activity pulses and actual cable lengths under representative rack noise.
6. Complete electrical rule checks, power/thermal budget, connector orientation review, PCB design rule checks and physical fit checks.

## Primary references

- [PiKVM pass-through ATX board](https://docs.pikvm.org/atx_board/)
- [Toshiba TLP3122A](https://toshiba.semicon-storage.com/ap-en/semiconductor/product/isolators-solid-state-relays/photorelay-mosfet-output/detail.TLP3122A.html)
- [WIZnet W5500](https://docs.wiznet.io/Product/Chip/Ethernet/W5500)
- [Microchip MCP23S17 family data sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf)
- [TI difference-amplifier input impedance](https://e2e.ti.com/blogs_/archives/b/precisionhub/posts/overlooking-the-obvious-the-input-impedance-of-a-difference-amplifier)
