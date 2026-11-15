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

NAME = "SNAP_Power_Controller"
ORIGIN = (100.0, 100.0)  # must match place-pcb.py
W, H, CHAMFER = 52.0, 29.0, 2.0
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


DX = 3.0  # the solar, charger and power-stage blocks sit 3 mm right of where they were first drawn


def X(pts):
    """Waypoints drawn for the 56.5 mm board, moved with their block."""
    return [(x + DX, y) for x, y in pts]


# ---------------------------------------------------------------- solar inputs
r10_1, r10_2 = P("R10", "1"), P("R10", "2")
j1_1, d5_2 = P("J1", "1"), P("D5", "2")
track("/PANEL1", [j1_1, (j1_1[0] + 0.45, 1.95), (r10_1[0], 1.95), r10_1], 0.4)
# down from R10, then 45 degrees into D5's anode pad
track("/PANEL1_D", [r10_2, (r10_2[0], d5_2[1] - (r10_2[0] - d5_2[0])), d5_2], 0.4)
for j, d in (("J2", "D6"), ("J3", "D7"), ("J4", "D8")):
    p, q = P(j, "1"), P(d, "2")
    jog = abs(q[1] - p[1])  # D6 and D7 are a little off their connector's row: finish with a 45-degree step
    track(f"Net-({d}-A)", [p, q] if jog < 1e-6 else [p, (q[0] - jog, p[1]), q], 0.6)
# PV bus down the diode cathodes, with a tee into the west edge of R7's PV pad
track("/PV", [P("D5", "1"), P("D8", "1")], 0.5)
track("/PV", [(P("D5", "1")[0], P("R7", "1")[1]), P("R7", "1")], 0.6)

# ---------------------------------------------------------------- limiter (U3) and charger (U1)
# VIN: R7 -> C1 -> U3's input pin, straight along the top
r7_2 = P("R7", "2")
track("/VIN", [r7_2, (P("C1", "1")[0], r7_2[1]), (P("U3", "3")[0], r7_2[1])], PWR)
# VCHG: U3's output pin to its tab under the body (both are pad 2), then round the west and south
# of U1 to C2 and up into U1's VIN pin. R2 and C2's ground sit inside that loop.
U3_OUT, U3_TAB = (30.3, 3.95), (30.3, 10.25)
track("/VCHG", [U3_OUT, U3_TAB], PWR)
c2_1, u1_4 = P("C2", "1"), P("U1", "4")
track("/VCHG", [U3_TAB, (26.6, 10.25), (26.6, 25.0), (c2_1[0], 25.0), c2_1], PWR)
track("/VCHG", [c2_1, u1_4], 0.5)
# VBAT: U1's BAT pin straight into C3, which carries on to the switch headers below
track("/VBAT", [P("U1", "5"), P("C3", "1")], PWR)
# FB senses VBAT. CHRG and DONE sit between FB and BAT, so FB takes one hop on B.Cu round the
# north of U1 to a via in the VBAT track.
fb = P("U1", "8")
track("/VBAT", [fb, (27.7, fb[1])])
via("/VBAT", (27.7, fb[1])); via("/VBAT", (33.7, fb[1]))
track("/VBAT", [(27.7, fb[1]), (27.7, 13.0), (28.2, 12.5), (33.2, 12.5), (33.7, 13.0), (33.7, fb[1])], layer=B)
# charge current: ISET to R2, R2's other end to U1's GND pin
track("Net-(U1-ISET)", [P("U1", "2"), (29.965, 21.01), P("R2", "1")])
track("GND", [P("R2", "2"), (31.425, 20.0), (31.235, 19.81), P("U1", "3")], 0.3)
# U1 ground: GND pin and TEMP (grounded: no NTC) into the exposed pad. Six 0.3 mm vias in the pad
# carry the heat to the bottom plane (the library's thermal-via footprint drills 0.2 mm, under
# this board's 0.3 mm minimum).
ep = P("U1", "9")
for dx in (-1.2, 0, 1.2):
    for dy in (-0.7, 0.7):
        via("GND", (ep[0] + dx, ep[1] + dy))
track("GND", [P("U1", "3"), (31.235, 17.2)], 0.3)
track("GND", [P("U1", "1"), (28.695, 17.9), (29.2, 17.395)], 0.3)
# status LEDs, along the top edge: VCHG -> R1 -> JP1 -> both anodes; cathodes come up from U1
track("/VCHG", [U3_OUT, P("R1", "1")], 0.4)
track("Net-(JP1-B)", [P("R1", "2"), (34.65, 1.5), P("JP1", "2")])
d4a, d3a = P("D4", "2"), P("D3", "2")
track("Net-(D3-A)", [P("JP1", "1"), (d4a[0] - (d4a[1] - 1.9), 1.9), d4a])
track("Net-(D3-A)", [(d4a[0] - (d4a[1] - 1.9), 1.9), (d3a[0] - (d3a[1] - 1.9), 1.9), d3a])
track("/~{CHRG}", [P("U1", "7"), (29.965, 11.8), (34.4, 11.8), (34.4, 6.2), (P("D4", "1")[0], 6.2), P("D4", "1")])
track("/~{DONE}", [P("U1", "6"), (31.235, 12.3), (34.85, 12.3), (34.85, 6.65), (P("D3", "1")[0], 6.65), P("D3", "1")])

# ---------------------------------------------------------------- battery, load, switches
# VBAT from C3 up and over J7 to the two headers' right-hand pins
track("/VBAT", [P("C3", "1"), (44.75, 13.875), (44.75, 9.4), (45.15, 9.0), (49.54, 9.0), P("J7", "1"), P("J8", "1")], PWR)
# BATT+ from J7 down between the headers and west, over J6, into the top of R6
track("/BATT+", [P("J7", "2"), (47.0, 14.0), (45.8, 15.2), (37.4, 15.2), (36.6, 16.0), P("R6", "1")], PWR)
track("/VOUT", [P("J8", "2"), (46.6, 17.3), P("J6", "1")], PWR)
# R6 -> Q2 (reverse-battery FET) -> under J5 into its pin 1
track("/BAT_CELL", [P("R6", "2"), (36.6, 19.64), (35.05, 21.19), P("Q2", "2")], PWR)
track("Net-(J5-Pin_1)", [P("Q2", "3"), (36.0, 24.3), (36.65, 24.95), (41.75, 24.95), (42.4, 24.3), P("J5", "1")], PWR)

# ---------------------------------------------------------------- INA3221 and J9, left band
U = {n: P("U2", n) for n in map(str, range(1, 18))}
# ground: pin 3 into the exposed pad, one via in the middle of the pad
track("GND", [U["3"], (U["3"][0], 14.6)])
via("GND", U["17"])
# supply: C6 to VS; the VCC via beside C6 collects J9 pin 1 (B.Cu) and VPU (B.Cu, under U2)
VCC = (5.75, 12.7)
via("/VCC_MCU", VCC)
track("/VCC_MCU", [VCC, (6.25, 12.2), (6.9, 12.2)])
track("/VCC_MCU", [P("C6", "1"), (6.9, 12.6), (7.025, 12.725), U["4"]])
track("/VCC_MCU", [P("J9", "1"), (5.0, 17.375), (5.75, 16.625), VCC], layer=B)
track("/VCC_MCU", [U["16"], (10.075, 14.525), (10.7, 13.9)])
via("/VCC_MCU", (10.7, 13.9))
track("/VCC_MCU", [(10.7, 13.9), (6.95, 13.9), VCC], layer=B)
# pull-ups: VCC pads joined above the resistors and down to the VCC via
track("/VCC_MCU", [P("R9", "1"), (3.025, 8.0), (3.275, 7.75), (5.875, 7.75), (6.125, 8.0), P("R8", "1"),
                   (6.125, 9.3), (5.6, 9.825), (5.6, 12.55), VCC])
# I2C: A0 and SCL straight across to J9; SDA (pin 7) reaches J9 pin 4 with a hop on B.Cu
j9_3, j9_4 = P("J9", "3"), P("J9", "4")
track("/SDA", [U["5"], (4.6, 14.525), (3.7, 13.625), j9_4])
track("/SCL", [U["6"], (4.3, 15.175), (4.0, 14.875), j9_3])
track("/SDA", [U["7"], (4.9, 15.825)])
via("/SDA", (4.9, 15.825))
track("/SDA", [(4.9, 15.825), (4.9, 14.0), (4.525, 13.625), j9_4], layer=B)
track("/SDA", [j9_4, (3.305, 11.5), (4.475, 10.33), P("R8", "2")])
track("/SCL", [j9_3, (2.0, 14.875), (1.6, 14.475), (1.6, 9.3), (1.375, 9.075), P("R9", "2")])
# channel 3 (R10, panel 1): PANEL1 over the top of J1, PANEL1_D under it, both down into U2
track("/PANEL1", [r10_1, (19.9, r10_1[1]), (20.15, r10_1[1] - 0.25), (20.15, 1.05), (19.9, 0.8), (8.575, 0.8),
                  (8.325, 1.05), U["2"]])
track("/PANEL1_D", [r10_2, (16.75, r10_2[1]), (16.1, r10_2[1] + 0.65), (9.2, r10_2[1] + 0.65),
                    (8.975, r10_2[1] + 0.875), U["1"]])
# channel 2 (R7, all panels): one hop each on B.Cu under the PV bus, then between J2 and J3
r7_1 = P("R7", "1")
track("/PV", [(21.3, r7_1[1]), (21.3, 9.95), (20.75, 10.5)])
track("/VIN", [(22.2, 4.2), (22.2, 4.6), (22.55, 4.95), (23.75, 4.95), (23.9, 5.1), (23.9, 10.2), (22.7, 11.4),
               (20.75, 11.4)])
for n, y in (("/PV", 10.5), ("/VIN", 11.4)):
    via(n, (20.75, y)); via(n, (19.05, y))  # either side of the PV bus at x = 19.9
    track(n, [(20.75, y), (19.05, y)], layer=B)
track("/PV", [(19.05, 10.5), (15.045, 10.5), (10.37, 15.175), U["15"]])
track("/VIN", [(19.05, 11.4), (14.795, 11.4), (10.37, 15.825), U["14"]])
# channel 1 (R6, battery): the pair runs down from U2, along the bottom edge, up west of R6
track("/BATT+", [U["12"], (8.975, 26.85), (9.425, 27.3), (33.45, 27.3), (33.9, 26.85), (33.9, 16.338),
                 (34.1, 16.138), P("R6", "1")])
track("/BAT_CELL", [U["11"], (8.325, 27.3), (8.775, 27.75), (33.9, 27.75), (34.35, 27.3), (34.35, 19.262),
                    (34.55, 19.062), P("R6", "2")])

# ---------------------------------------------------------------- GND vias for surface-mount pads
gnd_via(P("C1", "2"), (25.3, 8.15))
track("GND", [P("U3", "1"), (32.6, 4.9), (33.5, 5.8)], 0.4); via("GND", (33.5, 5.8))
gnd_via(P("C2", "2"), (28.2, P("C2", "2")[1]))
gnd_via(P("C3", "2"), (37.0, 9.5))
gnd_via(P("C6", "2"), (7.65, P("C6", "2")[1]))
gnd_via(P("Q2", "1"), (37.9, P("Q2", "1")[1]))

# ---------------------------------------------------------------- pours
gnd = net("GND")
for fp in board.GetFootprints():
    if fp.GetReference() in {f"J{i}" for i in range(1, 10)}:
        for p in fp.Pads():
            if p.GetNetname() == "GND":  # connector GND pins: solid, they carry panel/battery current
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    if fp.GetReference() == "U1":
        for p in fp.Pads():
            if p.GetNumber() == "9":  # exposed pad: solid into the top pour, it is the heat path
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
