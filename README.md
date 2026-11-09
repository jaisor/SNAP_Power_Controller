# Solar Node Charge Controller

A small solar charger board for a single-cell (1S) Li-ion/LiPo battery, built for solar-powered LoRa mesh nodes such as [SNAP v1.2](https://makerworld.com/en/models/3360988-snap-v1-2-solar-node-adaptable-platform-2x200ma). Up to four 5V panels feed a CN3791 MPPT buck charger. A switched output powers the node, and an INA219 reports voltage and current over I2C.

Designed in KiCad 10.

> **Status:** the schematic is complete and passes ERC. The PCB (56.5 × 29 mm, 2mm corner chamfers, four M3 mounting holes, two layers) is **placed and auto-routed** with a clean DRC, but hasn't had a manual layout review. A first board has been wired up and tested with a XIAO + Wio-SX1262 on a custom Meshtastic build, and everything seems to work as expected so far, including the I2C sensor. A sunlight test in a real solar node is under way, with the expected voltage and charge current so far. See [Testing](#testing).

<p align="center">
  <img src="docs/images/pcb-iso.png" alt="3D render of the routed board" width="720">
</p>

## Built for solar mesh nodes

This controller is meant for solar mesh nodes like the [SNAP v1.2: Solar Node Adaptable Platform](https://makerworld.com/en/models/3360988-snap-v1-2-solar-node-adaptable-platform-2x200ma). It simplifies their build in three ways:

- **Easy, clean connections:** the panels, battery, node and switches each plug into their own connector.
- **Improved solar charging:** an MPPT charger tuned for 5V panels, with a diode for every panel built into the board.
- **I2C power sensing:** configurable for either the battery or the solar circuit.

I2C power sensors are supported natively by both [Meshtastic](https://meshtastic.org) and [MeshCore](https://github.com/meshcore-dev/MeshCore). In most cases the node recognizes the INA219 automatically once it's connected.

<p align="center">
  <img src="docs/images/snap/snap-node.jpg" alt="SNAP v1.2 solar node on its mount" width="300">
  <img src="docs/images/snap/snap-internals.jpg" alt="Inside SNAP v1.2: build grid with 18650 holder and XIAO node" width="300">
</p>

<p align="center">
  <img src="docs/images/wiring-diagram.png" alt="Wiring diagram: panels, 18650, switches and a XIAO nRF52840 + Wio-SX1262 node connected to the charge module" width="900">
</p>

In the SNAP v1.2 example build, shown below, the board replaces several separately wired parts:

<p align="center">
  <img src="docs/images/snap/snap-component-map.jpg" alt="SNAP v1.2 component map: enclosure, 2 × 200mA panels, CN3158 MPPT module, Schottky diodes, 18650, XIAO nRF52840 + Wio-SX1262" width="800">
</p>

| Example build part | With this board |
|---|---|
| CN3158 MPPT module (SDBK03TA) | CN3791 MPPT buck charger, tuned for 5V panels (VIN held at 4.42V) and charging at 0.8A |
| One 1N5819 per panel, soldered inline | A 1N5819WS per input on the board, for up to four panels |
| Hand-soldered panel, battery and node wiring | Plug-in connectors for every connection: Micro JST 1.25, with 2.54mm pin headers for the switches |
| Latching on/off switch wired into the battery lead | Two switch connectors: SW_BATT cuts the battery, SW_LOAD cuts only the node |
| (none) | INA219 power monitor on I2C, switchable between the panels and the battery |

### Example wiring

| Board connector | Connects to |
|---|---|
| J1, J2 (Solar_5V) | Two [FellDen 5V 200mA 110×60mm panels](https://www.amazon.com/dp/B0BND5NYGK), the ones SNAP v1.2 uses. J3 and J4 take up to two more |
| J5 (BATT) | An 18650 Li-ion cell (1S, 3.0–4.2V) in its holder |
| J8 (SW_LOAD) | The SNAP on/off switch cap's latching button. To cut the battery entirely, use J7 (SW_BATT) as well, or instead |
| J7 / J8 left unswitched | Both switch connectors are in series with the power path, so an unused one needs a 2.54mm jumper cap, or a wire bridging its pads on the back of the board. Otherwise the battery or the node stays disconnected |
| J6 (VOUT) | The XIAO nRF52840's BAT+ / BAT− pads, which is where SNAP powers it from the 18650 today |
| J9 (I2C) | XIAO 3V3 → VCC, D6 → SDA, D7 → SCL, GND → GND, on a 4-wire cable coloured red VCC, black GND, yellow SCL, white SDA. These pins need a Meshtastic build with I2C on D6/D7 (see the table below) |
| JP1 (LED) | Nothing. Bridge it with solder if you want the status LEDs. It's open as supplied, so the LEDs stay dark |

Set SW3 to BATT to see the battery's charge and discharge current, or to SOLAR to see what the panels deliver.

The XIAO's I2C pins depend on the firmware build. D4 and D5 can't be used with the Wio-SX1262, because the radio uses them.

| Firmware build | SDA | SCL | Status |
|---|---|---|---|
| Meshtastic `seeed_xiao_nrf52840_kit`, custom build with I2C on D6/D7 | D6 | D7 | Tested on this board |
| Meshtastic `seeed_xiao_nrf52840_kit_i2c` | D6 | D7 | From the firmware source, not tested |
| Meshtastic `seeed_xiao_nrf52840_kit`, unmodified (D6/D7 are reserved for the GNSS module) | NFC1 pad (underside) | NFC2 pad (underside) | From the firmware source, not tested |
| MeshCore `Xiao_nrf52` | D7 | D6 | From the firmware source, not tested |

The INA219 uses address 0x40, which some other I2C sensors also use (for example the SHT21/HTU21D and HDC1080). If your node already has one of those, the two will clash.

In Meshtastic, enable power metrics in the telemetry settings so the readings are sent to the mesh.

## Features

- **Solar input:** up to four 5V panels in parallel (Micro JST 1.25), each isolated by its own 1N5819WS Schottky (SOD-323) so a shaded or unplugged panel doesn't drag the others down.
- **MPPT charging:** [CN3791](https://naylampmechatronics.com/img/cms/001216/CN3791.PDF) PWM buck charger with constant-voltage MPPT set to 4.42V input. Charges at 0.8A to 4.2V (CC/CV, trickle charge for deeply discharged cells, automatic recharge).
- **Battery and load switching:** connectors for two panel-mount switches. **SW_BATT** disconnects the battery from everything. **SW_LOAD** cuts only the output, so the battery keeps charging.
- **Output:** VOUT connector (Micro JST 1.25) that powers the module from the battery.
- **Reverse-battery protection:** Q2, a P-channel MOSFET between the battery connector and the rest of the board. A cell plugged in backwards is blocked instead of shorting through the charger. With the cell the right way round, Q2 is fully on in both directions, adding about 60mV of drop at 0.8A.
- **Power monitoring:** [INA219](https://www.ti.com/lit/ds/symlink/ina219.pdf) at I2C address 0x40. A slide switch selects whether it measures the solar input or the battery (bidirectional current plus voltage).
- **Status LEDs:** red while charging, green when charging is done. They're powered through JP1, an open solder jumper next to R1 on the top of the board: bridge its two pads with solder to turn them on. Left open, the LEDs are disconnected and draw nothing.

## Schematic

[![Schematic](docs/images/schematic.svg)](docs/images/schematic.svg)

The schematic follows the CN3791 datasheet's typical application circuit (Figure 1), with these changes:

| Item | Value | Why |
|---|---|---|
| Charge current | 0.8A (R5 = 0.15Ω) | I<sub>CH</sub> = 120mV / R5. Leaves margin on the 1.0A-rated connectors; use 0.24Ω for 0.5A with small cells. |
| MPPT setpoint | 4.42V at VIN (R3/R4 = 26.7k/10k) | V<sub>MPPT</sub> = 1.205V × (1 + R3/R4). The panels sit one diode drop higher (~4.7–4.9V), a little under a cool 5V panel's max-power voltage of about 5.0V. That voltage falls about 0.4% per °C, to about 4.2V at a 65°C cell temperature, and a fixed set point above it cuts the panel's output. Modeled for a 10-cell panel, 4.42V gives 99% of maximum power at 25°C and 84% at 65°C. v1.0's 4.58V (28.0k) gives 100% and 71%. |
| Blocking diode D1 | omitted | The input diodes already stop the battery feeding back into the panels. Leaving D1 out saves ~0.4V of headroom; the trade-off is ~21µA of battery drain in the dark. |
| Inductor | 22µH, Bourns SRN6045TA | Meets the datasheet's L > 5 × (VCC − VBAT) µH, with ~0.2A ripple. |
| Input diodes | 1N5819WS, SOD-323 (40V/1A) | The panels peak at ~200–300mA each, so the SMD part has plenty of margin and saves ~12mm of board width over DO-41. |

## PCB

<p align="center">
  <img src="docs/images/pcb-top.png" alt="Top side of the routed board" width="720">
  <img src="docs/images/pcb-bottom.png" alt="Bottom side: GND plane with a few short jumps" width="720">
</p>

| Area | Parts |
|---|---|
| Left end | M3 mounting holes H1/H3 in the corners, with the SOLAR/BATT selector SW3 between them |
| Left column | Solar inputs J1–J4, each with its 1N5819WS (D5–D8) |
| Top middle | Buck power stage in current-flow order: R7, C1/C5, Q1, D2, L1, R5, C3 |
| Middle | CN3791 (U1) with its support parts and status LEDs, and JP1, the LED solder jumper, right of R1 |
| Right middle | INA219 (U2), I2C pull-ups, battery shunt R6, reverse-battery MOSFET Q2 |
| Right column | SW_BATT/SW_LOAD switch leads (J7/J8), battery J5, VOUT J6 |
| Right end | M3 mounting holes H2/H4 in the corners, with the 4-pin I2C connector J9 between them |

Every reference label sits next to its own part, clear of pads, other parts and the edge (DRC reports no silkscreen issues). The holes are plain non-plated 3.2mm M3 holes, 4mm in from each edge.

**Silkscreen labels:**

- **Connector functions:** vertical labels beside the right-hand connectors read `SW_BATT` (J7), `SW_LOAD` (J8), `BATT` (J5) and `VOUT` (J6).
- **Solar inputs:** one `Solar_5V` label, with a bracket along the four solar inputs (J1–J4).
- **Polarity:** `-` and `+` under the solar, battery and VOUT connectors (J1–J6), on the side of the matching pin.
- **I2C connector:** `I2C` under J9 on the front. The pin names (`VCC`, `GND`, `SCL`, `SDA`) are printed beside its pads on the back, since there's no room between the pads and the connectors on the front.
- **SOLAR/BATT selector:** `solar/batt` / `i2c power sensor` beside SW3 on the back, with "solar" at the end of the switch that has the PV pins and "batt" at the end with the battery pins.
- **Back:** the module ID, "Solar Charge Module v1.1 / by JaisorGadgets / Nov. 5, 2026".

**Routing** (by `tools/route-pcb.py`):

- **Ground:** the bottom layer is a solid GND plane. The top layer has a GND fill, and every surface-mount GND pad gets its own via down to the plane.
- **Track widths:** power paths are 0.8mm, necked to 0.4mm at small pads. Signals are 0.25mm.
- **Kelvin sensing:** the CN3791's current-sense pins and the INA219 selector's throws connect straight to the pads of their shunt resistors (R5, R6, R7).
- **Layer use:** about 80% of the copper length is on the top layer. The bottom-side tracks are short jumps, which keeps the ground plane mostly intact.
- **Size:** 216 track segments and 46 vias, 11 of which are GND stitching vias.
- **Checks:** DRC reports 0 violations and 0 unconnected items, and schematic parity is clean.

This is auto-routing, so review it before ordering, especially the buck converter's switching loop (C1 → Q1 → D2, which currently returns through the ground plane) and the few bottom-layer tracks that cut the plane.

Still to do: a manual layout review before ordering (see Fabrication).

## Connectors

| Ref | Connector | Pin 1 | Pin 2 | Notes |
|---|---|---|---|---|
| J1–J4 | Micro JST 1.25, 2-pin | Panel + | GND | 5V solar panels, any combination of 1–4 |
| J5 | Micro JST 1.25, 2-pin | Battery + | GND | 1S Li-ion/LiPo, 4.2V |
| J6 | Micro JST 1.25, 2-pin | VOUT | GND | Battery voltage out to the powered module, through SW_LOAD |
| J7 | 2.54mm pin header, 2-pin | VBAT (charger) | BATT+ (battery) | SW_BATT: panel-mount SPST switch, rated ≥1A or the module's peak current |
| J8 | 2.54mm pin header, 2-pin | VBAT | VOUT | SW_LOAD: panel-mount SPST switch, same rating |
| J9 | Micro JST 1.25, 4-pin | VCC (3.3–5V) | GND | Pin 3 = SCL, pin 4 = SDA, matching the common red/black/yellow/white 4-wire cable. VCC comes from the MCU and powers the INA219. v1.0 boards have SDA on pin 2 and GND on pin 4. |

J1–J6 and J9 are Micro JST 1.25 (Molex PicoBlade-compatible) vertical headers, Molex 53047-0210 (2-pin) and 53047-0410 (4-pin). They mate with standard female cable housings (Molex 51021). J7 and J8 are standard 2.54mm vertical pin headers, which take a 2.54mm female housing or a jumper cap. Notes:

- **Current:** PicoBlade contacts are rated 1.0A. The charge current is set to 0.8A to stay under that on the battery connector (J5). Keep the module's load current under 1A too, since it flows through J5 when the panels are dark.
- **No keying between functions:** J1–J6 are the same 2-pin type, so a battery lead fits a solar socket. Check the silkscreen before plugging in. The switch headers take a different plug, so they can't be mixed up with these.
- **Battery polarity:** "JST 1.25" LiPo pigtails have no standard polarity. Check that red goes to the pin marked `+` (pin 1 on J5) before connecting. Q2 blocks a reversed cell, but fit the cell with SW_BATT off anyway: with SW_BATT on in sunlight, the charger's output can partly turn Q2 on and push a limited current into a reversed cell, which heats Q2.
- **Reading the marks:** pin 1 is `+` on J1–J6. J1–J4 are rotated 180° from J5 and J6, so the marks read `- J1 +` on the solar inputs and `+ J5 -` on the right-hand connectors.

**Operating note:** if SW_BATT is off while the panels are in sun, the charger sees no battery and VBAT pulses around 4.2V. Keep SW_LOAD off in that state.

## Power monitor (INA219)

- **Address:** 0x40 (A0 = A1 = GND).
- **Shunts:** both are 0.1Ω, the same as common INA219 breakout boards, so the default 32V/2A calibration in the usual libraries (e.g. Adafruit_INA219) works unchanged: about ±3.2A full scale, 0.8mA resolution.
- **Pull-ups:** R8/R9 are 10k I2C pull-ups to the MCU's VCC. Leave them off if the MCU board already has pull-ups.

| SW3 position | Shunt | Current | Bus voltage |
|---|---|---|---|
| SOLAR | R7, between the PV bus and VIN | Panel current, always ≥ 0 | VIN (panel voltage minus the diode drop) |
| BATT | R6, between BATT+ and the cell | Positive while charging, negative while discharging | Cell voltage, readable even with SW_BATT off. It's measured after Q2, so it reads up to about 50mV off while current flows |

The MCU can't sense SW3's position. Firmware has to know which position is set, or infer it from the readings.

## Testing

| Test | Setup | Status |
|---|---|---|
| First power-up | Board wired to a XIAO + Wio-SX1262, running Meshtastic built from `seeed_xiao_nrf52840_kit` with I2C on D6/D7 | Done. Everything seems to work as expected, including the INA219 over I2C |
| INA219 battery current | Same setup, battery at about 4V | Done. Discharging: about −12 to −15mA. Charging from the XIAO's USB: +100mA |
| Sunlight | Board wired into a real solar node with 4 × 60mA panels, with metrics tracked in Grafana dashboards | In progress. Voltage and charge current rose as expected when exposed to sunlight. One reading in the Meshtastic app: 4.56V, 110.5mA |

The signs match the expected convention: positive while charging, negative while discharging. The USB reading comes from the XIAO's own charger, so it doesn't test the CN3791. The sunlight reading is from SW3's SOLAR position: 4.56V is above a Li-ion cell's 4.2V and close to the 4.58V MPPT set point of the board tested (v1.1 lowers it to 4.42V). It's a single reading, and longer-term results are still to come. These tests used a board with Micro JST 1.25 connectors on J7 and J8, so the pin-header version hasn't been built yet. In the sunlight test build, J7 and J8 are bridged with wire on the back of the board, so neither switch is fitted.

<p align="center">
  <img src="docs/images/testing/solar-node-build.jpg" alt="Test build: the board, a XIAO and an 18650 on a build grid, wired to four panels through the enclosure lid" width="420">
  <img src="docs/images/testing/power-metrics.webp" alt="Meshtastic app showing power metrics from the node: 4.56V and 110.5mA on channel 3" width="240">
</p>

## Safety

This is an experimental design for charging a lithium-ion cell. It's provided as is, with no warranty, and hasn't been certified to any safety standard. If you build it, you're responsible for:

- Assembling it correctly and checking connector polarity before connecting a cell. J1–J6 share one connector type, so a lead plugs into the wrong socket easily. Q2 protects against a reversed cell on J5, but not against every fault, such as a battery plugged into a solar input.
- Using a protected cell or a separate protection circuit. The CN3791 charges the cell but doesn't protect it from over-discharge or short circuits.
- Fusing, wiring and an enclosure suited to where the node is installed, including outdoor heat and moisture.
- Not using it where a failure could hurt someone or damage property.

## Fabrication

Download the package from the [latest release](https://github.com/jaisor/SolarNodeChargeController/releases/latest). That release is v1.0, which has Micro JST 1.25 connectors on J7 and J8, no polarity marks, and a 4.58V MPPT set point (R3 = 28.0k). The design in this repo is v1.1, still a work in progress, and it will be released with the next fabrication batch. The package is generated into `output/fab/`, which isn't tracked in git:

| File | Contents |
|---|---|
| `SolarChargeModule_v1.1_gerbers.zip` | Upload this to the board house. 9 Gerber X2 layers (copper, mask, paste and silkscreen on both sides, plus the outline), a Gerber job file, plated and non-plated Excellon drill files, and drill maps |
| `FAB_NOTES.txt` | Order settings: 2 layers, FR-4 1.6mm, 1oz copper, 56.5 × 29mm, 0.25mm/0.2mm minimum track/space, 0.3mm minimum drill, tented vias, four 3.2mm non-plated holes. Also assembly cautions |
| `SolarChargeModule_v1.1_BOM.csv` | BOM in JLCPCB format (Comment, Designator, Footprint, LCSC Part #), plus a Manufacturer Part column for the specific parts |
| `SolarChargeModule_v1.1_CPL.csv` | Pick-and-place file for top-side assembly, in the same coordinates as the Gerbers |

LCSC part numbers are only filled in where verified (D5–D8). Pick the rest in the assembler's part search, and check rotation and polarity in their preview. The PicoBlade headers, the J7 and J8 pin headers, and SW3 are through-hole parts. JP1 is a solder jumper made of bare pads, so it has no part to place.

Regenerating the package (after the board is final and DRC is clean):

```bash
OUT=output/fab
P=SolarNodeChargeController
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts --subtract-soldermask --check-zones -o $OUT/gerbers $P.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-zeros-format decimal --drill-origin absolute --excellon-separate-th --generate-map --map-format gerberx2 -o $OUT/gerbers/ $P.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --side both -o $OUT/pos-kicad.csv $P.kicad_pcb
kicad-cli sch export bom --fields 'Value,Reference,Footprint,${QUANTITY}' --labels 'Comment,Designator,Footprint,Qty' --group-by 'Value,Footprint' --ref-range-delimiter '' --exclude-dnp -o $OUT/bom-kicad.csv $P.kicad_sch
node tools/fab-package.js $OUT
```

## Repository layout

```
SolarNodeChargeController.kicad_pro / .kicad_sch / .kicad_pcb   KiCad project
SolarNode.kicad_sym             project symbol library (CN3791)
sym-lib-table
tools/
  gen-schematic.js              generates the schematic (Node)
  place-pcb.py                  places footprints, labels, holes, outline (KiCad Python / pcbnew)
  route-pcb.py                  routes tracks, GND stitching vias and pours (run after place-pcb.py)
  make-diagram.py               draws docs/images/wiring-diagram.png from the board render
  fab-package.js                JLCPCB-style BOM/CPL, fab notes and Gerber zip from the kicad-cli exports
docs/images/                    images used in this README (snap/: photos from the SNAP v1.2 MakerWorld post)
CLAUDE.md                       design decisions and working notes
LICENSE                         CERN-OHL-P-2.0 (hardware design and documentation)
tools/LICENSE                   MIT (scripts)
```

The schematic and the board layout are generated by scripts in `tools/`, and checked with `kicad-cli` ERC/DRC (including schematic parity). See [CLAUDE.md](CLAUDE.md) for the full design rationale and workflow. Generated outputs (`output/`: BOM, reports, fab files) are not tracked.

## Regenerating the design

The whole design can be rebuilt from the scripts. Run these from the repo root, with `kicad-cli` from KiCad 10:

```bash
# 1. Schematic (Node): rewrites the .kicad_sch, SolarNode.kicad_sym and sym-lib-table
node tools/gen-schematic.js
kicad-cli sch erc --format json --severity-all -o erc.json SolarNodeChargeController.kicad_sch
# 2. Netlist for the board scripts
kicad-cli sch export netlist --format kicadxml -o net.xml SolarNodeChargeController.kicad_sch
# 3. Board (KiCad's Python): placement + labels + holes + outline, then routing + GND pours (~5 min)
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/place-pcb.py net.xml
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/route-pcb.py
# 4. Check: expect 0 violations, 0 unconnected, 0 parity issues
kicad-cli pcb drc --schematic-parity --severity-all --format json -o drc.json SolarNodeChargeController.kicad_pcb
```

The scripts overwrite their output files. Once you edit the schematic or board in KiCad, stop regenerating that file (or port your edits into the scripts first).

Refreshing the images in `docs/images/`:

```bash
kicad-cli sch export svg -o docs/images SolarNodeChargeController.kicad_sch
kicad-cli pcb render --side top --width 1600 --height 900 --quality high --zoom 1.6 -o docs/images/pcb-top.png SolarNodeChargeController.kicad_pcb
kicad-cli pcb render --side bottom --width 1600 --height 900 --quality high --zoom 1.6 -o docs/images/pcb-bottom.png SolarNodeChargeController.kicad_pcb
kicad-cli pcb render --width 1600 --height 1000 --quality high --perspective --rotate "-40,0,-25" -o docs/images/pcb-iso.png SolarNodeChargeController.kicad_pcb
```

(The schematic export is named `SolarNodeChargeController.svg`; rename it to `schematic.svg`.)

After refreshing `pcb-top.png`, redraw the wiring diagram with KiCad's Python, which includes Pillow and NumPy:

```bash
"C:/Program Files/KiCad/10.0/bin/python.exe" tools/make-diagram.py
```

## License

Copyright 2026 Jordan Marinov (JaisorGadgets).

The hardware design (schematic, board, symbol library) and its documentation, including the images in `docs/images/`, are licensed under the [CERN Open Hardware Licence Version 2 – Permissive](LICENSE) (CERN-OHL-P-2.0). You may redistribute and modify them, and make and sell products from them, under the terms of the licence. They are distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE. See section 5 of the licence for the disclaimer and limitation of liability.

The scripts in `tools/` are licensed under the [MIT License](tools/LICENSE).

Source location: https://github.com/jaisor/SolarNodeChargeController
