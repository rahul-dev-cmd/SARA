"""
SARA - Snake-Assisted Rescue Automaton
Parametric CAD generator (CadQuery).  All lengths in millimetres.
Axis convention: X = robot length (nose at x=0), Y = left/right, Z = up.

Run:  python sara_cad.py
Output: STEP/STL per part, full assembly, exploded assembly, report.
"""
import cadquery as cq
import math, os, sys, json, itertools

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/out"
os.makedirs(OUT + "/parts_step", exist_ok=True)
os.makedirs(OUT + "/parts_stl", exist_ok=True)

# ----------------------------------------------------------------- PARAMETERS
BODY_D = 84.0            # head / tail outer diameter
WALL = 2.5               # printed shell wall
HEAD_L, TAIL_L = 130.0, 130.0
MOD_L, JOINT_L = 95.0, 35.0
NOSE_D, TAPER_L = 56.0, 60.0
CORE_R, CORE_IN_R = 26.0, 22.0     # traction-module core tube
TRACK_Y = 38.5                      # track roller centre offset
DRUM_R, BELT_T, BELT_W = 10.0, 2.0, 24.0
TEND_R = 19.0                       # tendon hole circle radius
PIN_R = 1.5
ANCHOR_Z = -22.0                    # rear retrieval-line eyebolt: height below tail axis
EYE_R, EYE_T = 8.0, 2.5             # eye ring major radius / wire radius
DENS = {"petg": 1.27, "tpu": 1.21, "al": 2.70, "steel": 7.85}   # g/cm3
PRINT_FILL = {"petg": 0.5, "tpu": 0.6, "al": 1.0, "steel": 1.0}  # est. effective fill for mass estimate
MASS_G = {"camera": 3, "thermal": 4, "led": 0.2, "co2": 21, "mic": 1, "pi": 10.5,
          "servo": 13.4, "esp32": 10, "pca": 8, "tb6612": 2, "buck": 5,
          "battery": 110, "motor": 10.5, "mcp": 2}

X0 = {}
x = 0.0
for name, L in [("head", HEAD_L), ("J1", JOINT_L), ("M1", MOD_L), ("J2", JOINT_L), ("M2", MOD_L),
                ("J3", JOINT_L), ("M3", MOD_L), ("J4", JOINT_L), ("tail", TAIL_L)]:
    X0[name] = x
    x += L
TOTAL_L = x
SEG_IDX = {n: i for i, n in enumerate(X0)}

# ------------------------------------------------------------------- HELPERS
def W(solid):
    return cq.Workplane("XY").newObject([solid])

def cyl(r, p0, p1):
    p0 = cq.Vector(*p0); p1 = cq.Vector(*p1)
    d = p1 - p0
    return W(cq.Solid.makeCylinder(r, d.Length, p0, d.normalized()))

def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))

def revx(pts):
    return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0))

def r_out(xx):
    return NOSE_D / 2 + (BODY_D / 2 - NOSE_D / 2) * min(xx, TAPER_L) / TAPER_L

def ring_pts(r, n, a0=0.0):
    return [(r * math.cos(math.radians(a0 + 360.0 * i / n)),
             r * math.sin(math.radians(a0 + 360.0 * i / n))) for i in range(n)]

TEND_PTS = ring_pts(TEND_R, 16)
M3_PTS = ring_pts(11.0, 4, 45)

def plate_holes(x0, x1):
    """cut tool: wire hole + 16 tendon holes + 4 M3 holes through a plate x0..x1"""
    t = cyl(6.0, (x0 - 0.1, 0, 0), (x1 + 0.1, 0, 0))
    for (y, z) in TEND_PTS:
        t = t.union(cyl(1.1, (x0 - 0.1, y, z), (x1 + 0.1, y, z)))
    for (y, z) in M3_PTS:
        t = t.union(cyl(1.7, (x0 - 0.1, y, z), (x1 + 0.1, y, z)))
    return t

PARTS = []   # dicts: name, wp (global coords), mat, seg, role, color, kind

def add(name, wp, mat, seg, role="body", kind="printed", dx=0.0, key=None):
    wp = wp.translate((dx, 0, 0)) if dx else wp
    PARTS.append(dict(name=name, wp=wp, mat=mat, seg=seg, role=role, kind=kind, key=key))

# ---------------------------------------------------------------------- HEAD
def build_head():
    s = "head"
    # soft TPU nose cap with front plate (sensor windows + LED holes)
    cap = revx([(0, 0), (0, NOSE_D / 2), (10, r_out(10)), (10, 0)]).cut(
        revx([(2, 0), (2, r_out(2) - WALL), (10, r_out(10) - WALL), (10, 0)]))
    cap = cap.cut(cyl(4.0, (-1, -10, 0), (3, -10, 0)))          # camera lens window
    cap = cap.cut(cyl(4.5, (-1, 13, 0), (3, 13, 0)))            # thermal window
    LED = [(-7.5, 21.5), (10.5, 20.0), (-7.5, -21.5), (10.5, -20.0)]
    for (y, z) in LED:
        cap = cap.cut(cyl(2.5, (-1, y, z), (3, y, z)))
    add("head_nose_cap_TPU", cap, "tpu", s, "cap")

    outer = revx([(10, 0), (10, r_out(10)), (60, 42), (130, 42), (130, 0)])
    inner = revx([(10, 0), (10, r_out(10) - WALL), (60, 42 - WALL), (127, 42 - WALL), (127, 0)])
    shell = outer.cut(inner)
    shelf = box(62, 127, -41, 41, -9, -7).intersect(cyl(40.5, (62, 0, 0), (127, 0, 0)))
    shell = shell.union(shelf)
    for px in (64.5, 122.5):
        for py in (-11.5, 11.5):
            shell = shell.union(cyl(2.2, (px, py, -7.5), (px, py, -4)))
    shell = shell.cut(plate_holes(127, 130))
    shell = shell.cut(box(66, 86, -4, 4, 38, 43))                     # CO2 air slot (top)
    shell = shell.cut(cyl(1.5, (87, 0, -45), (87, 0, -38)))           # mic port (bottom)
    up = shell.intersect(box(-1, 131, -50, 50, 0, 50))
    lo = shell.intersect(box(-1, 131, -50, 50, -50, 0))
    add("head_shell_upper_PETG", up, "petg", s, "shell_top")
    add("head_shell_lower_PETG", lo, "petg", s, "shell_bot")
    # components
    add("head_camera_OV5647", box(2, 14, -22, 2, -12, 12), "elec", s, "comp", "camera", key="camera")
    add("head_thermal_MLX90640", box(2, 10, 4, 22, -13, 13), "elec", s, "comp", "thermal", key="thermal")
    for i, (y, z) in enumerate(LED):
        add(f"head_LED_{i+1}", cyl(2.5, (2, y, z), (8, y, z)), "elec", s, "comp", "led", key="led")
    add("head_CO2_MHZ19B", box(60, 93, -10, 10, 28, 37), "elec", s, "comp", "co2", key="co2")
    add("head_mic_INMP441", box(80, 94, -7, 7, -37.5, -34.5), "elec", s, "comp", "mic", key="mic")
    add("head_RaspberryPi_Zero2W", box(61, 126, -15, 15, -4, 1), "elec", s, "comp", "pi", key="pi")

# --------------------------------------------------------------------- JOINTS
def build_joint(k):
    s = f"J{k}"; ox = X0[s]
    cxx = 17.5
    # yoke A (attached to segment ahead): base disc + two arms at z=+-12
    A = cyl(16, (0, 0, 0), (8, 0, 0))
    A = A.union(box(8, 24, -7, 7, 10, 14)).union(box(8, 24, -7, 7, -14, -10))
    A = A.cut(cyl(5, (cxx, 0, -15), (cxx, 0, 15)))
    A = A.cut(cyl(6, (-1, 0, 0), (9, 0, 0)))
    for (y, z) in M3_PTS:
        A = A.cut(cyl(1.7, (-1, y, z), (9, y, z)))
    # yoke B (attached to segment behind): base disc + two arms at y=+-12
    B = cyl(16, (27, 0, 0), (35, 0, 0))
    B = B.union(box(11, 27, 10, 14, -7, 7)).union(box(11, 27, -14, -10, -7, 7))
    B = B.cut(cyl(5, (cxx, -15, 0), (cxx, 15, 0)))
    B = B.cut(cyl(6, (26, 0, 0), (36, 0, 0)))
    for (y, z) in M3_PTS:
        B = B.cut(cyl(1.7, (26, y, z), (36, y, z)))
    cross = cyl(PIN_R, (cxx, 0, -15), (cxx, 0, 15)).union(
        cyl(PIN_R, (cxx, -15, 0), (cxx, 15, 0))).union(W(cq.Solid.makeSphere(4, cq.Vector(cxx, 0, 0))))
    sleeve = cyl(30, (0, 0, 0), (JOINT_L, 0, 0)).cut(cyl(28, (-1, 0, 0), (JOINT_L + 1, 0, 0)))
    add(f"{s}_yoke_A_Al6061", A, "al", s, "yokeA", dx=ox)
    add(f"{s}_yoke_B_Al6061", B, "al", s, "yokeB", dx=ox)
    add(f"{s}_cross_spider_steel", cross, "steel", s, "cross", dx=ox)
    add(f"{s}_sleeve_TPU", sleeve, "tpu", s, "sleeve", dx=ox)
    for i, (z0, z1) in enumerate([(10, 14), (-14, -10)]):
        b = cyl(5, (cxx, 0, z0), (cxx, 0, z1)).cut(cyl(PIN_R, (cxx, 0, z0 - 1), (cxx, 0, z1 + 1)))
        add(f"{s}_bearing623_A{i+1}", b, "steel", s, "bearing", dx=ox)
    for i, (y0, y1) in enumerate([(10, 14), (-14, -10)]):
        b = cyl(5, (cxx, y0, 0), (cxx, y1, 0)).cut(cyl(PIN_R, (cxx, y0 - 1, 0), (cxx, y1 + 1, 0)))
        add(f"{s}_bearing623_B{i+1}", b, "steel", s, "bearing", dx=ox)

# -------------------------------------------------------------------- MODULES
def build_module(m):
    s = f"M{m}"; ox = X0[s]
    core = cyl(CORE_R, (0, 0, 0), (MOD_L, 0, 0)).cut(cyl(CORE_IN_R, (4, 0, 0), (MOD_L - 4, 0, 0)))
    for ax in (14.0, 81.0):
        for sy in (-1, 1):
            for sz in (-1, 1):
                ya, yb = sorted((20.0 * sy, 38.0 * sy))
                za, zb = sorted((12.0 * sz, 15.0 * sz))
                core = core.union(box(ax - 4, ax + 4, ya, yb, za, zb))
    for ax in (14.0, 81.0):
        for sy in (-1, 1):
            for sz in (-1, 1):
                ya, yb = sorted((12.0 * sy, 15.0 * sy))
                za, zb = sorted((20.0 * sz, 38.0 * sz))
                core = core.union(box(ax - 4, ax + 4, ya, yb, za, zb))
    core = core.cut(plate_holes(0, 4)).cut(plate_holes(MOD_L - 4, MOD_L))
    add(f"{s}_core_PETG", core, "petg", s, "body", dx=ox)
    for sy, side in ((1, "L"), (-1, "R")):
        yc = TRACK_Y * sy
        drive = (cq.Workplane("XY").center(14, yc).circle(DRUM_R).circle(8.25).extrude(BELT_W / 2, both=True))
        idler = (cq.Workplane("XY").center(81, yc).circle(DRUM_R).extrude(BELT_W / 2, both=True))
        o = cq.Workplane("XY").center(47.5, yc).slot2D(67 + 2 * (DRUM_R + BELT_T), 2 * (DRUM_R + BELT_T), 0).extrude(BELT_W / 2, both=True)
        i_ = cq.Workplane("XY").center(47.5, yc).slot2D(67 + 2 * DRUM_R, 2 * DRUM_R, 0).extrude(BELT_W / 2, both=True)
        belt = o.cut(i_)
        motor = box(14 - 6, 14 + 6, yc - 5, yc + 5, -12, 12)
        add(f"{s}_{side}_drive_drum_PETG", drive, "petg", s, "drum", dx=ox)
        add(f"{s}_{side}_idler_drum_PETG", idler, "petg", s, "drum", dx=ox)
        add(f"{s}_{side}_track_belt_TPU", belt, "tpu", s, "belt", dx=ox)
        add(f"{s}_{side}_motor_N20", motor, "elec", s, "motor", "motor", dx=ox, key="motor")
    # top (T) and bottom (B) tracks: rollers with axes along Y, belt loop in the XZ plane
    for sz, side in ((1, "T"), (-1, "B")):
        zc = TRACK_Y * sz
        drive = cyl(DRUM_R, (14, -BELT_W / 2, zc), (14, BELT_W / 2, zc)).cut(
            cyl(8.25, (14, -BELT_W / 2 - 1, zc), (14, BELT_W / 2 + 1, zc)))
        idler = cyl(DRUM_R, (81, -BELT_W / 2, zc), (81, BELT_W / 2, zc))
        o = cq.Workplane("XZ").center(47.5, zc).slot2D(67 + 2 * (DRUM_R + BELT_T), 2 * (DRUM_R + BELT_T), 0).extrude(BELT_W / 2, both=True)
        i_ = cq.Workplane("XZ").center(47.5, zc).slot2D(67 + 2 * DRUM_R, 2 * DRUM_R, 0).extrude(BELT_W / 2, both=True)
        belt = o.cut(i_)
        motor = box(14 - 6, 14 + 6, -12, 12, zc - 5, zc + 5)
        add(f"{s}_{side}_drive_drum_PETG", drive, "petg", s, "drum", dx=ox)
        add(f"{s}_{side}_idler_drum_PETG", idler, "petg", s, "drum", dx=ox)
        add(f"{s}_{side}_track_belt_TPU", belt, "tpu", s, "belt", dx=ox)
        add(f"{s}_{side}_motor_N20", motor, "elec", s, "motor", "motor", dx=ox, key="motor")

# ----------------------------------------------------------------------- TAIL
def build_tail():
    s = "tail"; ox = X0[s]
    outer = cyl(42, (0, 0, 0), (TAIL_L, 0, 0))
    bore = cyl(42 - WALL, (4, 0, 0), (126, 0, 0))
    shell = (outer.cut(bore).cut(plate_holes(0, 4)).cut(cyl(6, (125, 0, 0), (131, 0, 0)))
             .cut(cyl(3.3, (125, 0, ANCHOR_Z), (131, 0, ANCHOR_Z))))   # M6 eyebolt hole
    up = shell.intersect(box(-1, 131, -50, 50, 0, 50))
    lo = shell.intersect(box(-1, 131, -50, 50, -50, 0))
    add("tail_shell_upper_PETG", up, "petg", s, "shell_top", dx=ox)
    add("tail_shell_lower_PETG", lo, "petg", s, "shell_bot", dx=ox)
    n = 0
    for row, (yc, xoff) in enumerate([(-7.5, 19.5), (7.5, 31.0)]):
        for k in range(4):
            cx = xoff + 23 * k
            n += 1
            add(f"tail_servo_MG90S_{n}", box(cx - 11.5, cx + 11.5, yc - 6, yc + 6, -11.25, 11.25),
                "elec", s, "comp", "servo", dx=ox, key="servo")
            add(f"tail_pulley_{n}", cyl(5, (cx + 6, yc, 11.25), (cx + 6, yc, 14.25)),
                "petg", s, "comp", dx=ox)
    add("tail_battery_2x18650", box(7.5, 72.5, -18.5, 18.5, -34, -15), "elec", s, "comp", "battery", dx=ox, key="battery")
    add("tail_ESP32_DevKit", box(8, 63, -14, 14, 16, 29), "elec", s, "comp", "esp32", dx=ox, key="esp32")
    add("tail_PCA9685", box(8, 70.5, -12.7, 12.7, 30, 33), "elec", s, "comp", "pca", dx=ox, key="pca")
    for i, (cx, z0) in enumerate([(81, 17), (81, 21), (81, 25), (103, 17), (103, 21), (103, 25)]):
        add(f"tail_TB6612_{i+1}", box(cx - 10.15, cx + 10.15, -10.15, 10.15, z0, z0 + 3), "elec", s, "comp", "tb6612", dx=ox, key="tb6612")
    for i, yc in enumerate((-9, 9)):
        add(f"tail_buck_{i+1}", box(74.5, 97.5, yc - 8.5, yc + 8.5, -30, -25), "elec", s, "comp", "buck", dx=ox, key="buck")

    for i, yc in enumerate((-11, 11)):   # I/O expanders: motor-driver direction lines (24 needed)
        add(f"tail_MCP23017_{i+1}", box(78, 103, yc - 10, yc + 10, -22, -19), "elec", s, "comp", "mcp", dx=ox, key="mcp")
    # --- rear retrieval-line anchor: Al backing plate + M6 eyebolt + steel nut ---
    plate = box(123, 126, -15, 15, ANCHOR_Z - 12, ANCHOR_Z + 12) \
            .cut(cyl(3.3, (121, 0, ANCHOR_Z), (127, 0, ANCHOR_Z)))
    add("tail_rear_anchor_plate_Al6061", plate, "al", s, "comp", dx=ox)
    shank = cyl(3.0, (117, 0, ANCHOR_Z), (133.5, 0, ANCHOR_Z))
    ring = W(cq.Solid.makeTorus(EYE_R, EYE_T, cq.Vector(131 + EYE_R + EYE_T, 0, ANCHOR_Z),
                                cq.Vector(0, 1, 0)))
    add("tail_rear_eyebolt_M6_Al", shank.union(ring), "al", s, "comp", dx=ox)
    nut = cyl(5.5, (119, 0, ANCHOR_Z), (123, 0, ANCHOR_Z)).cut(cyl(3.0, (117, 0, ANCHOR_Z), (124, 0, ANCHOR_Z)))
    add("tail_rear_anchor_nut_M6", nut, "steel", s, "comp", dx=ox)

# -------------------------------------------------------------------- TENDONS
def build_tendons():
    anchors = {1: X0["head"] + 128.5, 2: X0["M1"] + 93.5, 3: X0["M2"] + 93.5, 4: X0["M3"] + 93.5}
    end_x = X0["tail"] + 4.0
    for k in range(1, 5):
        for i in range(4):
            y, z = TEND_PTS[(k - 1) + 4 * i]
            add(f"tendon_J{k}_{i+1}_steel1.2mm", cyl(0.6, (anchors[k], y, z), (end_x, y, z)),
                "steel", f"J{k}", "tendon")

build_head()
for k in range(1, 5):
    build_joint(k)
for m in range(1, 4):
    build_module(m)
build_tail()
build_tendons()

# ------------------------------------------------------------------- ANALYSIS
def vol(wp):
    try:
        return sum(s.Volume() for s in wp.solids().vals())
    except Exception:
        return 0.0

rows = []
tot_full = tot_est = 0.0
seg_mass = {}
for p in PARTS:
    v = vol(p["wp"])
    p["vol"] = v
    if p["mat"] == "elec":
        m_full = m_est = MASS_G[p["key"]]
    else:
        m_full = v * DENS[p["mat"]] / 1000.0
        m_est = m_full * PRINT_FILL[p["mat"]]
    p["m_full"], p["m_est"] = m_full, m_est
    tot_full += m_full; tot_est += m_est
    seg_mass[p["seg"]] = seg_mass.get(p["seg"], 0) + m_est
    bb = p["wp"].val().BoundingBox()
    p["bb"] = bb
    rows.append((p["name"], p["mat"], round(v, 1), round(m_full, 1), round(m_est, 1)))

# interference check
overlaps = []
n = len(PARTS)
for i in range(n):
    for j in range(i + 1, n):
        a, b = PARTS[i], PARTS[j]
        A, B = a["bb"], b["bb"]
        if (A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin
                or A.zmax < B.zmin or B.zmax < A.zmin):
            continue
        try:
            c = a["wp"].intersect(b["wp"])
            v = vol(c)
        except Exception:
            v = -1
        if v > 0.5 or v < 0:
            overlaps.append((a["name"], b["name"], round(v, 2)))

xmin = min(p["bb"].xmin for p in PARTS); xmax = max(p["bb"].xmax for p in PARTS)
ymin = min(p["bb"].ymin for p in PARTS); ymax = max(p["bb"].ymax for p in PARTS)
zmin = min(p["bb"].zmin for p in PARTS); zmax = max(p["bb"].zmax for p in PARTS)

report = []
report.append("SARA CAD REPORT (auto-generated by sara_cad.py)")
report.append(f"Parts: {len(PARTS)}")
report.append(f"Overall length: {xmax - xmin:.1f} mm | width (Y): {ymax - ymin:.1f} mm | height (Z): {zmax - zmin:.1f} mm")
report.append(f"Head/tail body diameter: {BODY_D} mm | nose diameter: {NOSE_D} mm | track span: {2*(TRACK_Y+DRUM_R+BELT_T):.1f} mm")
report.append(f"Mass, solid-fill upper bound: {tot_full/1000:.3f} kg")
report.append(f"Mass, estimated printed (PETG 50% / TPU 60% effective fill): {tot_est/1000:.3f} kg")
report.append("Mass by segment (est, g): " + ", ".join(f"{k}={v:.0f}" for k, v in seg_mass.items()))
report.append(f"Interferences found (>0.5 mm3): {len(overlaps)}")
for o in overlaps:
    report.append("  OVERLAP: %s <-> %s  %s mm3" % o)
report.append("")
report.append("part, material, volume_mm3, mass_solid_g, mass_est_g")
for r in rows:
    report.append(", ".join(map(str, r)))
open(OUT + "/SARA_Report.txt", "w").write("\n".join(report))
print("\n".join(report[:12 + len(overlaps)]))

# -------------------------------------------------------------------- EXPORTS
COL = {"petg": (0.90, 0.90, 0.92), "tpu": (0.95, 0.55, 0.15), "al": (0.75, 0.77, 0.80),
       "steel": (0.35, 0.37, 0.42), "elec": (0.15, 0.55, 0.45)}
ECOL = {"camera": (0.1, 0.1, 0.1), "thermal": (0.1, 0.1, 0.1), "led": (0.95, 0.8, 0.2), "co2": (0.2, 0.6, 0.6),
        "mic": (0.2, 0.6, 0.6), "pi": (0.1, 0.5, 0.2), "servo": (0.2, 0.3, 0.7), "esp32": (0.1, 0.35, 0.2),
        "pca": (0.2, 0.35, 0.8), "tb6612": (0.7, 0.15, 0.15), "buck": (0.15, 0.3, 0.7), "battery": (0.2, 0.4, 0.8),
        "motor": (0.55, 0.55, 0.58), "mcp": (0.5, 0.2, 0.6)}
def color_of(p):
    return ECOL[p["key"]] if p["mat"] == "elec" else COL[p["mat"]]

for p in PARTS:
    base = p["name"]
    cq.exporters.export(p["wp"], f"{OUT}/parts_step/{base}.step")
    cq.exporters.export(p["wp"], f"{OUT}/parts_stl/{base}.stl", tolerance=0.2, angularTolerance=0.3)

def explode_vec(p):
    e = SEG_IDX[p["seg"]] * 45.0
    dy = dz = 0.0
    r = p["role"]
    if r == "shell_top": dz = 70
    elif r == "shell_bot": dz = -70
    elif r == "cap": e -= 35
    elif r == "belt":
        dy, dz = {"_L_": (28, 0), "_R_": (-28, 0), "_T_": (0, 28), "_B_": (0, -28)}[next(k for k in ("_L_", "_R_", "_T_", "_B_") if k in p["name"])]
    elif r == "drum":
        dy, dz = {"_L_": (14, 0), "_R_": (-14, 0), "_T_": (0, 14), "_B_": (0, -14)}[next(k for k in ("_L_", "_R_", "_T_", "_B_") if k in p["name"])]
    elif r == "sleeve": dz = 45
    elif r == "yokeA": e -= 12
    elif r == "yokeB": e += 12
    elif r == "tendon": dz = 0
    return (e, dy, dz)

def make_asm(exploded):
    asm = cq.Assembly(name="SARA_Exploded" if exploded else "SARA_Assembly")
    for p in PARTS:
        wp = p["wp"]
        if exploded:
            wp = wp.translate(explode_vec(p))
        c = color_of(p)
        asm.add(wp, name=p["name"], color=cq.Color(c[0], c[1], c[2], 1.0))
    return asm

make_asm(False).save(OUT + "/SARA_Assembly.step")
make_asm(True).save(OUT + "/SARA_Exploded.step")

# mesh cache for renderer
import pickle
meshes = []
for p in PARTS:
    sh = p["wp"].val()
    verts, tris = sh.tessellate(0.35, 0.3)
    meshes.append(dict(name=p["name"], seg=p["seg"], role=p["role"], mat=p["mat"], key=p["key"],
                       color=color_of(p), explode=explode_vec(p),
                       v=[(v.x, v.y, v.z) for v in verts], t=tris))
pickle.dump(meshes, open(OUT + "/meshes.pkl", "wb"))
print("DONE", len(PARTS), "parts")
