# Solar Node Charge Controller

KiCad 10 project for a solar-powered 1S LiPo charger board that powers a separate module and reports power data over I2C. Target use: solar LoRa mesh nodes, specifically the user's own SNAP v1.2 enclosure (https://makerworld.com/en/models/3360988-snap-v1-2-solar-node-adaptable-platform-2x200ma) — 2 × FellDen 5V 200 mA 110×60 mm panels (https://www.amazon.com/dp/B0BND5NYGK), 18650 cell, XIAO nRF52840 + Wio-SX1262 running Meshtastic/MeshCore. The board replaces SNAP's CN3158 (SDBK03TA) MPPT module, inline 1N5819s and hand wiring, and adds the INA219 (auto-detected by Meshtastic and MeshCore).

- KiCad project: `SolarNodeChargeController.kicad_pro` at the repo root (flattened from KiCad's nested `<name>/<name>/` template layout; the folder name still matches the project name, which the MCP server relies on)
- Schematic: single A3 sheet, `SolarNodeChargeController.kicad_sch`
- PCB: `SolarNodeChargeController.kicad_pcb` — placed and auto-routed, 56.5 × 29 mm, 2 mm chamfers, 4× M3 holes, GND pours both layers
- Images: `docs/images/` (tracked, used by the README): `schematic.svg`, `pcb-top.png`, `pcb-bottom.png`, `pcb-iso.png`, `wiring-diagram.png` (drawn by `tools/make-diagram.py` from `pcb-top.png`), and `snap/` — three photos from the user's own SNAP v1.2 MakerWorld post (node, internals, component map), downloaded as WebP and converted to JPEG. The Amazon panel photos were deliberately not copied (seller's images); the diagram draws panels, the 18650 and the node instead and the README links the listing. `output/` holds regenerable outputs (schematic PDF, BOM, ERC/DRC reports) and is gitignored.

## Status

Schematic complete and reviewed; ERC is clean (0 items at all severities) and the netlist has been checked net-by-net.

PCB placed and auto-routed: 42 footprints (incl. H1–H4 and the JP1 solder jumper), 216 track segments, 46 vias, GND pours on both layers. DRC: 0 violations, 0 unconnected, schematic parity 0. Silkscreen has connector function labels, +/- polarity marks, I2C pin names and the module ID on the back. v1.1 is work in progress on `main`: v1.0's pinout and copper, plus polarity marks, a new back label and revision, 2.54 mm pin headers on J7 and J8, R3 = 26.7k (4.42 V MPPT set point, was 28.0k / 4.58 V), JP1, an open solder jumper in the LED supply, Q2, a reverse-battery P-FET at J5, and J9 reordered to 1 VCC, 2 GND, 3 SCL, 4 SDA (was 2 SDA, 4 GND) to match the user's red/black/yellow/white cable. The first v1.1 tag and release were withdrawn; the user will mint v1.1 again when ordering the next fabrication batch. v1.0 is the only release, with its fab package attached. Commit 0093163 swapped J5 and J6 by mistake, so don't use it. Commit 948465d is the JST board with v1.1's silkscreen that was briefly tagged v1.1. Fabrication package generated (Gerbers, drill, BOM, CPL, fab notes) — see **Fabrication**. Next: manual layout review before ordering (buck hot loop, B.Cu plane cuts), pick LCSC parts for the assembly BOM.

## PCB placement

2-layer, 56.5 × 29 mm with 2 mm 45° corner chamfers (`W`, `H`, `CHAMFER` in the script; outline is 8 Edge.Cuts segments). Board top-left at (100, 100) mm in the editor. Grew from 42 × 26 mm to fit four M3 holes and readable reference labels. Layout, left to right:
- **Left end band (7.5 mm):** M3 holes H1 (top) / H3 (bottom), 4 mm from each edge, with SW3 (SOLAR/BATT selector, rotated 90°) between them.
- **Left column:** solar inputs J1–J4 stacked (rotated so pin 1 faces its diode), each with its 1N5819WS (D5–D8, SOD-323) in the same row, anode toward the connector and cathodes lined up for the PV bus. Row pitch 6.3 mm leaves room for each label underneath.
- **Middle top:** buck power stage in flow order — R7 (solar shunt), C1/C5, Q1, D2 under it, L1, R5, C3 — keeping the C1 → Q1 → D2 hot loop short.
- **Middle:** U1 CN3791 with C2 (VG), R2/C4 (COM), R3/R4 (MPPT), status LEDs D4/D3 with R1 below them. JP1 (LED supply solder jumper) is right of R1, rotated 180° so pad 2 faces R1 and pad 1 runs up to the LED anode track. It was on the back at first; the user moved it to the top because the back is hard to reach once the board is mounted.
- **Right middle:** C3 between R5 and the function-label strip; U2 INA219 with C6 below it; bottom row R8/R9 (vertical I2C pull-ups), R6 (battery shunt) and Q2 (reverse-battery P-FET, SOT-23, right of R6, its label to the east).
- **Right column:** J7 SW_BATT, J8 SW_LOAD, J5 battery, J6 VOUT (6.3 mm pitch), each with its function label on the left.
- **Right end band (7.5 mm):** M3 holes H2 / H4 with J9 (4-pin I2C, rotated 90°) between them.

Mounting holes are schematic symbols H1–H4 (`Mechanical:MountingHole`, footprint `MountingHole_3.2mm_M3`, non-plated, excluded from the BOM; their references are hidden on the board). Reference labels are placed by the script: 1 mm text, horizontal, on the first side in `LABEL_SIDES` order (default N, S, E, W, nudged in 0.25 mm steps up to ±2.5 mm) where the text outline clears every courtyard, other labels (0.6 mm) and the edge; it reports any part it can't label (last resort: the library's own label position if it only overlaps its own courtyard).

Board silkscreen (`board_silk()` in place-pcb.py, added before reference labels so those avoid it): `FUNCTION_LABELS` (`FUNCTION_LABEL_RIGHT` sets J7/J8's position, clear of C3) — 0.8 mm vertical text left of J7 `SW_BATT`, J8 `SW_LOAD`, J5 `BATT`, J6 `VOUT` (C3 moved left and the right column right to open that strip); one `Solar_5V` label with a bracket line at x = 7.75 mm along J1–J4 (user wanted a single label for all solar inputs); `POLARITY_REFS` — `-` and `+` either side of the reference under J1–J6, on the side of the matching pad (`-` for the GND pad, read from the net), so J1–J4 (rotated 180°) read `- Jn +` and J5/J6 read `+ Jn -`; `BACK_TEXT` — "Solar Charge Module v1.1 / by JaisorGadgets / Nov. 5, 2026", mirrored on B.Silkscreen at the board centre (no B-side pads there); `I2C_LABEL` — `I2C` under J9 on the front; `I2C_PINS` — `VCC`/`GND`/`SCL`/`SDA` in 0.8 mm text beside each J9 pad on B.Silkscreen (the front strip between J9 and the right column is too narrow); `SW3_LABEL` — `solar/batt` / `i2c power sensor`, two vertical 0.8 mm lines on B.Silkscreen between SW3's pads and the J1–J4 pads, rotated 270° so "solar" sits at the PV/VIN throws (pins 1/6, the bottom end) and "batt" at BATT+/BAT_CELL (pins 3/4), as the user asked; the list order puts "i2c power sensor" nearest the pads so the lines read "solar/batt" first. That assumes the usual slide-switch behaviour (sliding toward an end connects that end's throws) — confirm against the JS202011 datasheet. `BACK_LABELS` — for back-side parts placed with the `"b"` flag (none now; JP1 used it before moving to the top): the reference beside the upper pad and a label beside the lower pad, 0.8 mm text on B.Silkscreen right of the courtyard. The front label placer skips back-side parts and ignores their courtyards, and the courtyard-overlap check only compares parts on the same side.

Generated by `tools/place-pcb.py` (KiCad's Python + `pcbnew`), which rebuilds the whole board from the schematic netlist and the `PLACEMENT` table (board-relative x, y, rotation per reference; a trailing `"c"` places by courtyard centre, `"b"` flips the part to the back after it is added to the board, since flipping first crashes pcbnew). It sets each footprint's symbol path, so a later "Update PCB from Schematic" matches footprints instead of duplicating them. Run commands are under **Regenerating the design** below.

## PCB routing

`tools/route-pcb.py` routes the freshly placed board. It refuses a board that already has tracks or zones (removing zones through SWIG crashes KiCad 10), so re-route by running place-pcb.py then route-pcb.py (~5 min). Current board: 216 track segments, 46 vias (11 of them GND stitching), 79% of copper length on F.Cu (0.8 mm: 97 mm, 0.4 mm: 250 mm, 0.25 mm: 226 mm). This is v1.0's copper with pcbnew patches: the VBAT, BATT+ and VOUT tracks at J7/J8 re-drawn for the pin headers, JP1 added (then moved to the top), Q2 added, and J9's pins 2/4 swapped. For Q2, J5 pin 1 runs down the old BAT_CELL corridor (0.8 mm, x = 43.24) to Q2's drain; Q2's source goes to R6 pad 2 on its own 0.8 mm track, so the Kelvin track from R6 pad 2 to SW3 still carries no load current; the gate has a stub and GND via at (41.36, 24.95); and SCL between x = 41.9 and 45.85 moved to B.Cu (via at 45.85, 24.25) to let the battery track through. For JP1, VIN keeps v1.0's F.Cu route into R1 pad 1; R1 pad 2 runs right to JP1 pad 2, and JP1 pad 1 goes up to the D4–D3 anode track at (24.75, 23.75); R1 pad 2's old track up to D4 is gone. For J9, SDA now runs on B.Cu along y = 14.65 to x = 50.6, then 45° up to pad 4, clear of the SCL pad; pad 2 (GND) has a solid zone connection, since a thermal relief starved there (route-pcb.py now applies that to J9 as well as J1–J8). The router's result shifts between runs, so the committed board is the source of truth for routing, and running place-pcb.py + route-pcb.py again will not reproduce it. Re-route only when pads, nets or placement change.

- **Router:** grid A* written for this board (no FreeRouting/Java on this machine): 0.05 mm grid, two layers, 45° moves with a turn penalty (clean straight/45° runs), B.Cu costs 4× and a via 10 mm of track so routing stays on F.Cu. Clearances from the board defaults (0.2 mm copper, 0.5 mm edge) plus a 3 mm track keep-out around the M3 holes. Each connection retries with narrower tracks if the wide one doesn't fit.
- **Order:** GND fan-out first (every SMD GND pad gets an F.Cu stub to its own via, falling back to the nearest stitched GND pad), then the power-stage nets (`NET_ORDER`), then the rest by length. Stitching GND last left U2 pin 6 (between IN− and VS) unreachable.
- **Widths:** power nets (`POWER_NETS`) 0.8 mm between large pads, 0.4 mm into small pads; signals 0.25 mm. Vias 0.8/0.4 power, 0.6/0.3 signal.
- **Topology:** per net, an MST over the large pads, then small pads attach to the nearest connected pad; fine-pitch ICs (U1, U2) never sit mid-path on a power net. `KELVIN` ties sense pins straight to their shunt pads (U1 CSP/BAT → R5; SW3 throws → R7/R6).
- **Pours:** GND on B.Cu (thermal reliefs) and F.Cu (solid to SMD, thermal to THT); power-connector GND pins (J1–J6, and J9's) are solid on both, which also avoids starved thermals on the small PicoBlade pads.
- **Result:** B.Cu has short jumps plus a couple of longer runs. It is an auto-route: review the C1 → Q1 → D2 loop (its GND return goes through the plane) before fabrication.

## Regenerating the design

The whole design is reproducible from `tools/`. Full pipeline, from the repo root:

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

Then refresh the README images (commands in README.md, "Regenerating the design"), and redraw the wiring diagram: `"C:/Program Files/KiCad/10.0/bin/python.exe" tools/make-diagram.py` (KiCad's Python has Pillow + NumPy; the system Python has Pillow only). The diagram's connector positions come from the `CONN` table in the script — update it if the placement changes.

- Each step overwrites its output. **Once anyone edits the schematic or board in KiCad, stop regenerating that file**: port the edits into the scripts first, or switch to editing in KiCad (Update PCB from Schematic carries schematic changes to the board).
- Before writing, check the editor for that file is closed (`~*.kicad_sch.lck` / `~*.kicad_pcb.lck`) or that the file is unchanged since the last commit; afterwards the user must close the editor **without saving** and reopen.
- Commit before regenerating, so the previous version is recoverable from history.

## Fabrication

Package in `output/fab/` (gitignored; attach to a release tag): `SolarChargeModule_v1.1_gerbers.zip` (9 Gerber X2 layers + job file + PTH/NPTH Excellon + drill maps), `FAB_NOTES.txt` (order settings and assembly cautions), `SolarChargeModule_v1.1_BOM.csv` / `_CPL.csv` (JLCPCB-style; H1–H4 excluded; MPNs for the specific parts, LCSC only for D5–D8 = C191023). Checked: job file lists all 9 layers, 2 layers / 1.6 mm / 56.5 × 29 mm; PTH drill 72 hits (46 vias + 26 pads), NPTH 4 × 3.2 mm; vias tented. Regenerate with the commands in README "Fabrication"; `tools/fab-package.js` does the BOM/CPL conversion, notes and zip.

Silkscreen-only changes go on the routed board with a pcbnew patch (no re-route), with place-pcb.py updated to match, so a full regenerate gives the same labels. The SW3 back label flip and v1.1's marks, back label and revision were done this way. To check a patch, export Gerbers and drill from both boards and compare them with comment and date lines removed: everything except the silkscreen layers and the job file should match.

## Circuit summary

Datasheets: CN3791 https://naylampmechatronics.com/img/cms/001216/CN3791.PDF · INA219 https://www.ti.com/lit/ds/symlink/ina219.pdf

```
J1..J4 (5V panels) -> D5..D8 1N5819WS -> PV -> R7 0.1R -> VIN -> Q1 AO3401A -> SW node -> L1 22uH -> CSP -> R5 0.15R -> VBAT
                                                                     D2 SS34 to GND                                   |
VBAT -> J7 SW_BATT (panel switch) -> BATT+ -> R6 0.1R -> BAT_CELL -> Q2 (rev-batt P-FET) -> J5 LiPo                   |
VBAT -> J8 SW_LOAD (panel switch) -> VOUT -> J6                                                                        |
U2 INA219 IN+/IN- <- SW3 DPDT: SOLAR = (PV, VIN) across R7 | BATT = (BATT+, BAT_CELL) across R6 ; I2C on J9 ------------+
```

### Charger (CN3791, datasheet Figure 1)
| Ref | Value | Notes |
|---|---|---|
| U1 | CN3791, SSOP-10 1.0mm pitch | Custom symbol in `SolarNode.kicad_sym` (project lib). Footprint `Package_SO:SSOP-10_3.9x4.9mm_P1.00mm` |
| Q1 | AO3401A (SOT-23) | P-FET pass switch; gate = DRV net (U1 pin 10). Logic-level, fine at ~5V Vgs |
| D2 | SS34 (SMA) | Catch diode |
| D1 | — (intentionally unused) | Datasheet blocking diode omitted for ~0.4V headroom; D5–D8 already keep the battery out of the panels. Cost: ~21µA battery drain in the dark via L1 + Q1 body diode |
| L1 | 22µH, Bourns SRN6045TA | Datasheet: L > 5×(VCC−VBAT) µH ≈ 16µH; ~0.2A ripple at 6V in / 3.7V batt |
| R5 | 0.15Ω 1% 1206 | Charge current = 120mV / R5 = **0.8A**. Lowered from 1.0A (0.12Ω) when the connectors became 1.0A-rated PicoBlade, for margin on J5/J7. Termination at 16% ≈ 130mA. 0.24Ω would give 0.5A |
| R3/R4 | 26.7k / 10k 1% | MPPT setpoint VIN = 1.205 × (1 + R3/R4) = **4.42V**. History: 5.0 V originally, then 4.58 V (28.0k; v1.0 and the first test boards), lowered to 4.42 V in v1.1 after review feedback about hot panels. Vmp falls ~0.4 %/°C, so a 5V panel's ~5.0 V Vmp is ~4.2 V at 65 °C cell temperature; a set point that holds the panel above its Vmp loses power fast. The reviewer suggested raising it, which is backwards. Single-diode model (10-cell panel, Voc 6.0 V / Vmp 5.0 V / Isc 0.22 A assumed, no datasheet): 4.42 V gives 99 % of max power at 25 °C and 84 % at 65 °C, vs 100 % / 71 % for 4.58 V; 4.35 V (26.1k) was the other candidate (98.5 % / 88 %), and the user chose 26.7k. Panels sit ~0.3–0.45 V higher (diode drop). Headroom over a full 4.2 V cell is 0.22 V. Charging starts when VIN > ~4.51 V (MPPT > 1.23 V) |
| C1, C5 | 10µF/25V 1206, 100nF/25V | Input caps on VIN |
| C2 | 100nF | VG–VCC |
| C3 | 22µF/10V 1206 | Output cap on VBAT |
| R2 + C4 | 120Ω + 220nF | COM compensation (datasheet-mandated) |
| R1, D4, D3 | 1k, red LED, green LED | D4 red on ~CHRG = charging; D3 green on ~DONE = done. ~2.4 mA from VIN while lit |
| JP1 | SolderJumper_2_Open (`LED_EN`), top, right of R1 | In series between R1 and the LED anodes (VIN → R1 → JP1 → D4/D3): open as supplied, so the LEDs are off and draw nothing; bridge with solder to enable. User asked for it; it started on the back and moved to the top so it can be reached with the board mounted. `Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm`; symbol in_bom no, footprint excluded from BOM and pos files |

### Solar inputs
- **Connectors:** J7 and J8 are 2.54 mm vertical pin headers (user's choice, after JST on the first boards). The rest are Micro JST 1.25 / Molex PicoBlade-compatible vertical THT headers — 53047-0210 (2-pin) for J1–J6, 53047-0410 (4-pin) for J9 — mating with Molex 51021 female housings (user's choice; switched from JST-PH/XH and a 2.54 mm header to save space). Rated 1.0 A per contact; the charge current was lowered to 0.8 A for margin on J5, and the module's load current (through J5 when dark) should stay under 1 A too. J1–J6 share one type, so there is no mechanical keying between functions; LiPo "JST 1.25" pigtails have no standard polarity. KiCad has no 3D model for these footprints.
- J1–J4: 2-pin, value `Solar_5V`, up to four 5V panels in parallel.
- D5–D8: 1N5819WS (SOD-323, 40V/1A; KiCad `Diode:1N5819WS`, LCSC C191023), one per panel, OR-ed onto the PV bus. Switched from the DO-41 1N5819 to save ~12 mm of board width: the panels peak at ~200–300 mA each, well inside the rating.
- MPPT divider senses VIN (after the diodes and R7), not the raw panel voltage. Constant-voltage MPPT: one setpoint for all panels, set a little under a cool panel's Vmp so hot panels lose less (see R3/R4). Going as low as 4.2V was discussed and rejected: it drags sunny panels off their MPP and leaves no headroom above the battery.

### Battery, load and switches
- J5: battery (`LiPo_1S_4.2V`), pin 1 = cell + (net `Net-(J5-Pin_1)`), pin 2 = GND.
- Q2: AO3401A reverse-battery P-FET (same part as Q1): drain to J5 pin 1, source to BAT_CELL, gate straight to GND (Vgs max ±12 V, so no resistor or zener is needed at 4.2 V). Correct cell: the body diode lifts the source, Vgs = −Vcell turns Q2 fully on, and it conducts both ways (charge and discharge); ~60–90 mΩ at 3–4 V, so ~60 mV and ~50 mW at 0.8 A. Reversed cell: Vgs ≈ 0 and the body diode blocks, so the CN3791, INA219 and the node never see the negative voltage. Added after the user asked what a reversed cell would do: without Q2, SW_BATT closed shorts the cell through the CN3791's BAT-pin diode and D2/L1/R5 (several amps; R5/R6 burn open), and SW3 on BATT drives the INA219 inputs below −0.3 V. Residual case: a reversed cell with SW_BATT closed in sun, where the charger lifts Q2's source and turns it partly on; Q2 then passes a limited current into the reversed cell and dissipates it. The INA219 BATT bus voltage (BAT_CELL) now reads the cell minus Q2's drop (±~50 mV with current).
- J7 `SW_BATT`, J8 `SW_LOAD`: 2-pin 2.54 mm headers for **off-board panel-mount SPST switches** (user's choice over on-board slide switches; KiCad's stock slide switches such as EG1271 are only rated ~0.3A).
  - SW_BATT: VBAT ↔ BATT+. Isolates the cell from charger and load.
  - SW_LOAD: VBAT ↔ VOUT. Cuts only the load; the cell keeps charging.
  - Switch rating: ≥1A or the module's peak current, whichever is higher. The battery switch carries the battery's net current (charge OR discharge), not the sum.
  - With SW_BATT off in sun, the CN3791 sees no battery and VBAT pulses near 4.2V (datasheet "battery not present") — keep SW_LOAD off then.
- J6 `VOUT`: 2-pin output to the powered module, pin 1 = VOUT (+), pin 2 = GND.

### INA219 power monitor
- U2: INA219AID (SOIC-8, `Sensor_Energy:INA219AxD`). A0 = A1 = GND → I2C address **0x40**. C6 100nF bypass.
- Shunts: R7 0.1Ω (solar, PV→VIN) and R6 0.1Ω (battery, BATT+→BAT_CELL), both 1% 1206, always in circuit. 0.1Ω matches the common INA219 breakout, so stock library calibration (32V/2A, PGA /8, ±320mV ≈ ±3.2A, ~0.8mA LSB) works unchanged. Each drops ~0.1V at 1A.
- SW3: on-board DPDT slide switch (C&K JS202011CQN), signal-level only. Pole 1 common (pin 2) → SENSE+ → U2 IN+; pole 2 common (pin 5) → SENSE− → U2 IN−.
  - SOLAR (pins 1/6): IN+ = PV, IN− = VIN → panel current (≥ 0); bus voltage = VIN.
  - BATT (pins 3/4): IN+ = BATT+, IN− = BAT_CELL → battery current, + charging / − discharging; bus voltage = cell voltage (readable even with SW_BATT open, since R6 is on the cell side).
  - User chose one INA219 + switch over two INA219s (0x40/0x41). The MCU cannot sense SW3's position.
- J9 `I2C_MCU` (4-pin Micro JST 1.25): 1 VCC_MCU (3.3–5V from the MCU; powers U2 and pull-ups), 2 GND, 3 SCL, 4 SDA — the order of the user's red/black/yellow/white cable. v1.0 boards (and the first test build) have 2 SDA, 4 GND. R8/R9 10k pull-ups to VCC_MCU — omit if the MCU board has its own. INA219 inputs tolerate 0–26V with VS unpowered.

## Tooling and workflow

### Version control
Git repo at this folder (branch `main`), remote `origin` = https://github.com/jaisor/SolarNodeChargeController (public since 2026-11-08). Tracked: `.kicad_pro/.kicad_sch/.kicad_pcb`, `SolarNode.kicad_sym`, `sym-lib-table`, `tools/` (schematic generator, PCB placement and routing scripts, fab packager, wiring-diagram drawer), `CLAUDE.md`, `README.md` with images in `docs/images/` (schematic SVG; top, bottom and angled 3D renders — regenerate them when the design changes; commands are in the README). Ignored (see `.gitignore`): `*.kicad_prl` (per-user view state), `*.lck`, KiCad autosaves/backups, `.history/` (KiCad's local history, its own git repo), `*.bak*`, and `output/` (regenerable reports, BOM, PDFs, fab files — attach fab packages to a release tag instead). `.gitattributes` pins KiCad files to LF because `core.autocrlf=true` on this machine.

### License
`LICENSE` is CERN-OHL-P-2.0 (verbatim SPDX text) for the hardware design and documentation; `tools/LICENSE` is MIT for the scripts, and each script starts with an `SPDX-License-Identifier: MIT` line. The user chose a permissive licence for its warranty and liability disclaimer (section 5 covers products made from the design, including product liability). Copyright holder: Jordan Marinov (JaisorGadgets), 2026. The README has the notice and a Safety section. Keep the SPDX line on new scripts.

### MCP server
User-scope `kicad` MCP server (PyPI `kicad-mcp-server` 3.5.0, run with KiCad's Python), configured in `~/.claude.json` with env vars:
- `KICAD_MCP_PROJECTS_BASE` = `C:\Users\jaiso\Projects\Claude\KiCad`, this repo's parent: projects are its direct subfolders, so the project name is `SolarNodeChargeController` (the repo folder). Updated when the project was flattened.
- `KICAD_MCP_TASKS_DIR` = `C:\Users\jaiso\Documents\KiCad\10.0\mcp-tasks`
- `KICAD_MCP_KICAD_CLI` = `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`

It is **read/export only** (ERC, DRC, board info, BOM, netlist, Gerbers, PDF/SVG, STEP, JLCPCB package) — it cannot add parts or wires. Known issues:
- `run_erc` reports `violations: 0` even when the report has errors. Read `output/reports/erc_report.json` or use `kicad-cli sch erc --severity-all`.
- Autorouting (FreeRouting/nohup) and 3D render (xvfb-run) do not work on Windows.

### Editing the schematic
The schematic is generated by `tools/gen-schematic.js` (Node), which writes the whole `.kicad_sch` plus `SolarNode.kicad_sym` and `sym-lib-table`:

```
node tools/gen-schematic.js
```

- UUIDs are deterministic (SHA-1 of the item's key: `sym/<ref>`, `pin/<ref>/<n>`, wire endpoints, label name + position). Regenerating an unchanged design is byte-identical, and symbol UUIDs — which the PCB footprints link to — stay put across edits as long as references don't change.
- **The generator is the source of truth only while no one edits the schematic in KiCad.** If the user saves changes from the Schematic Editor, port them into the generator (or switch to surgical edits) before regenerating, or they are lost.
- Editor-open and commit-first rules: see **Regenerating the design**. Pre-git schematic backups (`*.kicad_sch.bak-*`) were kept in `output/backups/` (gitignored) when the project was flattened; they can be deleted.
- Verify every change:
  1. `kicad-cli sch export netlist --format kicadxml` and check each net's pins
  2. `kicad-cli sch erc --format json --severity-all` → expect 0 items
  3. `kicad-cli sch export pdf -o output/docs/schematic.pdf` and look at it for overlapping text

### KiCad 10 file and API gotchas
- kicad-cli only says "Failed to load schematic" on parse errors; bisect by stripping elements. A seen cause was an unescaped `\"` copied from a library property (power:GND Description).
- Derived library symbols (`extends`, e.g. Diode:SS34, Diode:1N5819WS, Transistor_FET:AO3401A) must be flattened when embedded in `lib_symbols`. Some libraries use CRLF line endings.
- Placed-symbol angle rotates counter-clockwise on screen; library Y is up, schematic Y is down. Field angles are relative to the symbol: use 360−rot for 90/270 to keep text horizontal, 0 for 180.
- Multi-line text grows upward from its anchor (justify bottom).
- pcbnew Python (KiCad 10): footprint fields are set with `fp.SetField(name, text)` (no `GetFieldByName`); `pcbnew.NewBoard(path)` gives a default 2-layer board; `SaveBoard` writes CRLF on Windows (git normalizes to LF). A text field's `GetBoundingBox()` includes a full line height (1.7 mm for 1 mm text); use `GetEffectiveTextShape().BBox()` for the ink outline that DRC checks. The schematic generator copies a symbol's `in_bom` flag from its library (mounting holes are `in_bom no`), otherwise parity flags a BOM-attribute mismatch. Check the PCB Editor is closed (no `~*.kicad_pcb.lck`) before writing.
- pcbnew zones: `board.Remove(zone)` on a loaded board crashes in SWIG (hence route-pcb.py needs a freshly placed board). `ZONE` has no Python setter for the minimum thermal spoke count; starved thermals were fixed per pad with `SetLocalZoneConnection(ZONE_CONNECTION_FULL)`.
- KiCad rewrites `.kicad_pro` with its default settings when the project is opened; commit that along with the next change.
- `kicad-cli pcb render --zoom` is relative to the fit-to-board view, and the framing depends on the image aspect ratio; the README lists the settings that frame this board.
- `kicad-cli` is at `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` (not on PATH); `claude` CLI is not on PATH either; `pdftotext` is available for reading datasheets.

## Open items / reminders
- Manual layout review before fabrication: the C1 → Q1 → D2 switching loop currently returns through vias and the B.Cu plane (ideally tie C1's and D2's GND pads directly on F.Cu); two longer B.Cu runs cut the GND plane; check the COM network (R2/C4) returns close to U1 GND (datasheet p.9–10). Kelvin sensing to R5/R6/R7 is already in place.
- Before ordering: pick LCSC parts for the remaining BOM lines and check rotations/polarity in the assembler's preview; regenerate the fab package if the board changes. Attach the package to a release (`gh release create`) rather than committing it; bump the version in `BACK_TEXT`, the title-block revisions, `tools/fab-package.js` and `tools/make-diagram.py`.
- Choose and buy the two panel-mount switches (≥1A).
- Reference designators have a gap at D1 by design; re-annotate after layout if desired.
- Optional: INA219 input RC filter (datasheet §9.2) only if readings are noisy; firmware averaging is usually enough.
