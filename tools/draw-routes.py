# SPDX-License-Identifier: MIT
# Draws the board's copper by hand: every track and via below is a fixed coordinate, so the
# result is the same on every run. Needs the unrouted board from tools/place-pcb.py (it refuses
# a board that already has tracks or zones). Coordinates are mm from the board's top-left corner.
#   "C:\Program Files\KiCad\10.0\bin\python.exe" tools/draw-routes.py [project dir, default: repo root]
# Then: kicad-cli pcb drc --schematic-parity --severity-all ...
# If the placement changes, the pad look-ups still follow the parts, but the waypoints do not:
# re-check every route near the moved part.
import math
import os
import sys

import pcbnew

NAME = "SolarNodeChargeController"
ORIGIN = (100.0, 100.0)  # must match place-pcb.py
W, H, CHAMFER = 56.5, 29.0, 2.0
F, B = pcbnew.F_Cu, pcbnew.B_Cu
SIG, PWR = 0.25, 0.8
VIA, PVIA = (0.6, 0.3), (0.8, 0.4)  # (diameter, drill)
HOLES = [(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4)]
STITCH_PITCH = 3.0  # GND stitching via grid, mm
ZONE_CLEARANCE = 0.25

path = os.path.join(sys.argv[1] if len(sys.argv) > 1 else ".", NAME + ".kicad_pcb")
board = pcbnew.LoadBoard(path)
if len(board.GetTracks()) or len(board.Zones()):
    sys.exit("board already has tracks or zones: run tools/place-pcb.py first")
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
PADS = {(fp.GetReference(), p.GetNumber()): p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNumber()}
count = {"track": 0, "via": 0}


def P(ref, num):
    """Pad centre, board mm."""
    c = PADS[(ref, num)].GetPosition()
    return (pcbnew.ToMM(c.x) - ORIGIN[0], pcbnew.ToMM(c.y) - ORIGIN[1])


def net(name):
    n = board.FindNet(name)
    if n is None:
        sys.exit(f"no net {name}")
    return n


def track(name, pts, w=SIG, layer=F):
    """Polyline on one layer. Every segment must be horizontal, vertical or 45 degrees."""
    n = net(name)
    for a, b in zip(pts, pts[1:]):
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        if min(dx, dy) > 0.02 and abs(dx - dy) > 0.02:
            sys.exit(f"{name}: segment {a} -> {b} is not on a 45-degree direction")
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a)); t.SetEnd(V(*b)); t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(n)
        board.Add(t)
        count["track"] += 1


def via(name, c, size=VIA):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(*c)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(F, B)
    v.SetWidth(mm(size[0])); v.SetDrill(mm(size[1])); v.SetNet(net(name))
    board.Add(v)
    count["via"] += 1


def gnd_via(pad, c, w=0.4):
    """Short stub from a GND pad to its own via down to the plane."""
    track("GND", [pad, c], w)
    via("GND", c)


# ---------------------------------------------------------------- solar inputs
track("/PANEL1", [P("J1", "1"), (13.9, 2.4), (14.35, 2.85), P("R10", "1")], 0.4)
track("/PANEL1_D", [P("R10", "2"), (16.275, 3.5), (15.9, 3.875), (14.775, 3.875), (14.4, 4.25), P("D5", "2")], 0.4)
for j, d in (("J2", "D6"), ("J3", "D7"), ("J4", "D8")):
    track(f"Net-({d}-A)", [P(j, "1"), P(d, "2")], 0.4)
# PV bus down the diode cathodes, with a tee into the west edge of R7's PV pad
track("/PV", [P("D5", "1"), P("D8", "1")], 0.5)
track("/PV", [(16.5, P("R7", "1")[1]), P("R7", "1")], 0.6)

# ---------------------------------------------------------------- buck power stage
# VIN: R7 -> C1 -> C5 in a straight line along the top, then down to Q1's source
track("/VIN", [P("R7", "2"), (22.3, 3.938), (24.3, 3.938), (24.987, 4.625), P("C5", "1"), (25.835, 4.625),
               (27.56, 6.35), P("Q1", "2")], PWR)
# switch node: Q1 drain to L1, and down to D2's cathode
track("Net-(D2-K)", [P("Q1", "3"), (33.225, 5.4), P("L1", "1")], PWR)
track("Net-(D2-K)", [P("Q1", "3"), (29.738, 6.6), (27.3, 9.038), (27.3, 10.9), P("D2", "1")], PWR)
# L1 -> R5 (charge-current shunt) -> C3 -> the two switch headers
track("/CSP", [P("L1", "2"), (38.375, 9.163), P("R5", "1")], PWR)
track("/VBAT", [P("R5", "2"), (38.925, 12.7), P("C3", "1"), (43.96, 10.015), P("J8", "1"), P("J7", "1")], PWR)
# gate drive: up the west side of D2, one hop on B.Cu under the VIN track into Q1's gate
track("/DRV", [P("U1", "10"), (25.6, 14.15), (25.15, 13.7), (25.15, 9.0), (26.3, 7.85), (26.3, 6.9)])
via("/DRV", (26.3, 6.9))
track("/DRV", [(26.3, 6.9), (26.3, 4.2), (26.6, 3.9)], layer=B)
via("/DRV", (26.6, 3.9))
track("/DRV", [(26.6, 3.9), (27.15, 4.45), P("Q1", "1")])

# ---------------------------------------------------------------- CN3791 and its parts
# VIN to C2 and, under the IC between its pin rows, to pin 9
track("/VIN", [(24.0, 3.938), (24.0, 10.6), (23.075, 11.525), P("C2", "1")], 0.4)
track("/VIN", [P("C2", "1"), (23.075, 12.7), (23.9, 13.525), (23.9, 15.1), (24.7, 15.9), P("U1", "9")])
# ...on to R3 (MPPT divider) with a hop on B.Cu under the charge-current sense pair
track("/VIN", [P("U1", "9"), (26.95, 15.9), (27.25, 15.6)])
via("/VIN", (27.25, 15.6))
track("/VIN", [(27.25, 15.6), (28.225, 16.575), (30.45, 16.575)], layer=B)
via("/VIN", (30.45, 16.575))
track("/VIN", [(30.45, 16.575), P("R3", "1")])
# ...and out under the IC, round the LEDs and JP1, to R1 (LED supply)
track("/VIN", [(23.9, 15.1), (23.9, 19.9), (26.45, 22.45), (26.45, 26.45), (26.25, 26.65), (20.6, 26.65),
               (20.175, 26.225), P("R1", "1")])
track("Net-(U1-VG)", [P("C2", "2"), (21.525, 12.4), (21.25, 12.675), P("U1", "1")])
# charge-current sense: Kelvin pair from R5's pads straight into pins 8 and 7
# (0.2 mm wide: the pair squeezes between pin 8 and R3)
track("/CSP", [P("R5", "1"), (34.838, 13.7), (34.538, 14.0), (29.894, 14.0), (26.994, 16.9), P("U1", "8")], 0.2)
track("/VBAT", [P("R5", "2"), (37.762, 14.15), (37.462, 14.45), (30.08, 14.45), (26.63, 17.9), P("U1", "7")], 0.2)
# MPPT node: pin 6 and the R3/R4 junction, kept short
track("/MPPT", [P("R3", "2"), P("R4", "1")])
track("/MPPT", [P("U1", "6"), (28.6, 18.9), (28.85, 19.15), (29.3, 19.15)])
# compensation network
track("Net-(U1-COM)", [P("U1", "5"), (20.2, 18.9), (19.65, 18.35), (19.65, 17.25), (18.975, 16.575), P("R2", "1")])
track("Net-(C4-Pad1)", [P("R2", "2"), P("C4", "1")])
# status LEDs: cathodes out under the IC, anodes joined below the LEDs and down to JP1
track("/~{DONE}", [P("U1", "4"), (22.2, 17.9), (22.2, 19.9), (20.513, 21.587), P("D3", "1")])
track("/~{CHRG}", [P("U1", "3"), (22.65, 16.9), (22.65, 20.3), (24.013, 21.663), P("D4", "1")])
track("Net-(D3-A)", [P("D3", "2"), (22.088, 23.6), (22.388, 23.9), (25.288, 23.9), (25.588, 23.6), P("D4", "2")])
track("Net-(D3-A)", [(24.9, 23.9), P("JP1", "1")])
track("Net-(JP1-B)", [P("R1", "2"), (22.225, 25.4), P("JP1", "2")])

# ---------------------------------------------------------------- battery, load, switches
track("/BATT+", [P("J7", "2"), (48.0, 4.8), (48.0, 10.3), (43.15, 15.15), (41.4, 16.9), (41.4, 23.65),
                 (40.5, 24.55), (39.9, 24.55)], PWR)
# VOUT crosses BATT+ on B.Cu, straight down from J8's pin
track("/VOUT", [P("J8", "2"), (46.5, 13.3)], PWR, B)
via("/VOUT", (46.5, 13.3), PVIA)
track("/VOUT", [(46.5, 13.3), (47.5, 14.3), (47.5, 18.2), (45.14, 20.56), P("J6", "1")], PWR)
track("Net-(J5-Pin_1)", [P("J5", "1"), (45.14, 17.2), (43.238, 19.102), P("Q2", "3")], PWR)
track("/BAT_CELL", [P("Q2", "2"), (37.5, 27.55), (36.488, 26.538), P("R6", "2")], PWR)

# ---------------------------------------------------------------- INA3221
U = {n: P("U2", n) for n in map(str, range(1, 18))}
# channel 1 (R6): IN+1 outside into the top of R6's BATT+ pad, IN-1 inside and under U2
track("/BATT+", [U["12"], (40.6, 17.925), (40.6, 23.3), (39.412, 24.488), P("R6", "1")])
track("/BAT_CELL", [U["11"], (40.1, 18.575), (40.1, 22.7), (39.6, 23.2), (37.2, 23.2), (36.488, 23.912), P("R6", "2")])
# ground: pin 3 into the exposed pad and out to a via
track("GND", [U["3"], (U["17"][0] - 0.6, U["3"][1])])
track("GND", [U["3"], (34.375, U["3"][1]), (34.0, 19.6)])
via("GND", (34.0, 19.6))
# supply: VS to C6; VPU from a via above pin 16, down under U2 on B.Cu, onto VS's track
track("/VCC_MCU", [U["4"], (34.52, 20.8), P("C6", "1")])
track("/VCC_MCU", [U["16"], (36.325, 16.775), (35.75, 16.2)])
via("/VCC_MCU", (35.75, 16.2))
track("/VCC_MCU", [(35.75, 16.2), (35.75, 21.6), (35.6, 21.75)], layer=B)
via("/VCC_MCU", (35.6, 21.75))
track("/VCC_MCU", [(35.6, 21.75), (34.65, 20.8), (34.52, 20.8)])
# ...and C6 to the pull-ups: via under C6, B.Cu to the R8-R9 track
track("/VCC_MCU", [P("C6", "1"), (33.825, 21.75)])
via("/VCC_MCU", (33.825, 21.75))
track("/VCC_MCU", [(33.825, 21.75), (32.05, 23.525), (32.05, 25.225)], layer=B)
via("/VCC_MCU", (32.05, 25.225))
track("/VCC_MCU", [P("R8", "1"), P("R9", "1"), (34.95, P("R9", "1")[1])])
via("/VCC_MCU", (34.95, P("R9", "1")[1]))
# I2C: SCL drops to a via between the two SDA pins (A0 = SDA); SDA ties below it
track("/SCL", [U["6"], (36.975, 21.6)])
via("/SCL", (36.975, 21.6))
track("/SCL", [(36.975, 21.6), (34.35, 24.225)], layer=B)
via("/SCL", (34.35, 24.225))
track("/SCL", [(34.35, 24.225), (33.95, 24.225), P("R9", "2")])
track("/SDA", [U["5"], (36.325, 22.5)])
track("/SDA", [U["7"], (37.625, 22.5)])
track("/SDA", [P("R8", "2"), (30.8, 23.3), (31.6, 22.5), (38.8, 22.5)])
via("/SDA", (38.8, 22.5))
# the bundle to J9 on B.Cu, between J5 and J6: SDA, SCL, VCC side by side
track("/SDA", [(38.8, 22.5), (41.7, 22.5), (44.9, 19.3), (48.5, 19.3), (49.6, 18.2), (49.6, 14.0),
               (50.975, 12.625), P("J9", "4")], layer=B)
track("/SCL", [(36.975, 21.6), (36.975, 23.15), (41.69, 23.15), (45.09, 19.75), (49.0, 19.75), (50.05, 18.7),
               (50.05, 15.0), (51.175, 13.875), P("J9", "3")], layer=B)
track("/VCC_MCU", [(34.95, P("R9", "1")[1]), (36.575, 23.6), (41.88, 23.6), (45.28, 20.2), (50.05, 20.2),
                   (50.5, 19.75), (50.5, 17.575), (51.7, 16.375), P("J9", "1")], layer=B)

# ---------------------------------------------------------------- INA3221 channels 2 and 3
# Kelvin lines from R10 (panel 1) and R7 (all panels). Top side: R10's pair goes through the gap
# under R7; all four run down east of R7 to a row of vias. Bottom side: one four-line bundle
# under the CN3791 to U2, clear of the switching parts. Order on B.Cu, north to south:
# PV, VIN, PANEL1, PANEL1_D, so nothing crosses at U2.
ROW = 13.4  # y of the via row
r7_1, r7_2 = P("R7", "1"), P("R7", "2")
track("/PANEL1", [P("R10", "1"), (14.625, 2.2), (14.875, 1.95), (17.33, 1.95), (17.58, 2.2), (17.58, 5.15),
                  (17.83, 5.4), (20.3, 5.4), (20.45, 5.55), (20.45, 7.89), (19.5, 8.84), (19.5, ROW)], 0.2)
track("/PANEL1_D", [P("R10", "2"), (16.92, 2.85), (17.12, 3.05), (17.12, 5.65), (17.32, 5.85), (19.85, 5.85),
                    (20.0, 6.0), (20.0, 7.7), (18.7, 9.0), (18.7, ROW)], 0.2)
track("/VIN", [(19.2, 4.2), (19.2, 4.6), (19.55, 4.95), (20.75, 4.95), (20.9, 5.1), (20.9, 8.08), (20.3, 8.68),
               (20.3, ROW)])
track("/PV", [(18.6, r7_1[1]), (18.6, 8.0), (17.9, 8.7), (17.9, ROW)])
for n, x in (("/PV", 17.9), ("/PANEL1_D", 18.7), ("/PANEL1", 19.5), ("/VIN", 20.3)):
    via(n, (x, ROW))
track("/PV", [(17.9, ROW), (17.9, 13.1), (18.25, 12.75), (20.9, 12.75), (21.1, 12.95), (35.1, 12.95),
              (36.975, 14.825), (36.975, 15.1)], layer=B)
track("/VIN", [(20.3, ROW), (34.39, ROW), (36.89, 15.9), (37.625, 15.9)], layer=B)
track("/PANEL1", [(19.5, ROW), (19.5, 13.7), (19.85, 14.05), (20.9, 14.05), (21.1, 13.85), (29.55, 13.85),
                  (34.275, 18.575), (34.4, 18.575)], layer=B)
track("/PANEL1_D", [(18.7, ROW), (18.7, 13.7), (19.5, 14.5), (21.5, 14.5), (21.7, 14.3), (29.1, 14.3),
                    (33.0, 18.2)], layer=B)
# vias and stubs at U2
via("/PV", (36.975, 15.1)); track("/PV", [U["15"], (36.975, 15.1)])
via("/VIN", (37.625, 15.9)); track("/VIN", [U["14"], (37.625, 15.9)])
via("/PANEL1", (34.4, 18.575)); track("/PANEL1", [U["2"], (34.4, 18.575)])
via("/PANEL1_D", (33.0, 18.2)); track("/PANEL1_D", [U["1"], (33.275, U["1"][1]), (33.0, 18.2)])

# ---------------------------------------------------------------- GND vias for surface-mount pads
gnd_via(P("C1", "2"), (22.3, 8.15))
gnd_via(P("C5", "2"), (25.3, 7.35))
gnd_via((30.3, 10.4), (30.3, 9.2)); gnd_via((31.3, 10.4), (31.3, 9.2))  # D2 anode
gnd_via(P("C3", "2"), (41.05, 10.925))
gnd_via(P("U1", "2"), (19.9, 15.9), SIG)
gnd_via(P("C4", "2"), (18.5, 23.3))
gnd_via(P("R4", "2"), (30.4, 21.725))
gnd_via(P("C6", "2"), (32.275, 19.65))
gnd_via(P("Q2", "1"), (40.5, 26.513))

# ---------------------------------------------------------------- pours
gnd = net("GND")
for fp in board.GetFootprints():
    if fp.GetReference() in {f"J{i}" for i in range(1, 10)}:
        for p in fp.Pads():
            if p.GetNetname() == "GND":  # connector GND pins: solid, they carry panel/battery current
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)


def add_zone(layer, connection):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(gnd)
    c = CHAMFER
    for x, y in [(c, 0), (W - c, 0), (W, c), (W, H - c), (W - c, H), (c, H), (0, H - c), (0, c)]:
        z.AppendCorner(V(x, y), -1)
    z.SetLocalClearance(mm(ZONE_CLEARANCE))
    z.SetMinThickness(mm(0.25))
    z.SetPadConnection(connection)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetAssignedPriority(0)
    board.Add(z)
    return z


zb = add_zone(B, pcbnew.ZONE_CONNECTION_THERMAL)
zf = add_zone(F, pcbnew.ZONE_CONNECTION_THT_THERMAL)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

# Stitching: a GND via wherever a grid point sits inside both pours with room for the via,
# so every piece of the top pour is tied to the bottom plane.
fills = [zf.GetFilledPolysList(F), zb.GetFilledPolysList(B)]
ring = [(0.55 * math.cos(a * math.pi / 8), 0.55 * math.sin(a * math.pi / 8)) for a in range(16)] + [(0, 0)]
drills = [(pcbnew.ToMM(t.GetPosition().x) - ORIGIN[0], pcbnew.ToMM(t.GetPosition().y) - ORIGIN[1])
          for t in board.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
drills += [P(*k) for k, p in PADS.items() if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
pad_boxes = []
for p in PADS.values():
    bb = p.GetBoundingBox()
    bb.Inflate(mm(0.45))
    pad_boxes.append(bb)
stitched = 0
y = 1.5
while y < H - 1:
    x = 1.5
    while x < W - 1:
        clear = all(math.hypot(x - hx, y - hy) > 3.4 for hx, hy in HOLES) and \
            all(math.hypot(x - hx, y - hy) > 1.2 for hx, hy in drills)
        clear = clear and not any(b.Contains(V(x, y)) for b in pad_boxes)  # no via-in-pad
        if clear and all(f.Contains(V(x + dx, y + dy)) for f in fills for dx, dy in ring):
            via("GND", (x, y))
            drills.append((x, y))
            stitched += 1
        x += STITCH_PITCH
    y += STITCH_PITCH
filler.Fill(board.Zones())

pcbnew.SaveBoard(path, board)
print(f"{count['track']} track segments, {count['via']} vias ({stitched} of them GND stitching), 2 GND pours")
