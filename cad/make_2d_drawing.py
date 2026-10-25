import pickle, sys, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle
import shapely
from shapely.ops import unary_union

OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
meshes = pickle.load(open(OUT + "/meshes.pkl", "rb"))

def keep(m):
    n = m["name"]
    if m["mat"] not in ("petg", "tpu", "al"): return False
    if "drum" in n or "pulley" in n or "anchor_plate" in n: return False
    return True
parts = [m for m in meshes if keep(m) and len(m["v"])]

SC = 2.5                       # main views 1:2.5
fig = plt.figure(figsize=(16.54, 11.69), dpi=110)   # A3 landscape
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 420); ax.set_ylim(0, 297); ax.axis("off")
LW_O, LW_T = 1.1, 0.45

def project(m, view):
    V = np.array(m["v"], float); T = np.array(m["t"], int)
    if view == "side":  P = V[:, [0, 2]]; d = V[:, 1]       # x,z ; depth y
    elif view == "top": P = V[:, [0, 1]]; d = V[:, 2]       # x,y ; depth z
    else:               P = V[:, [1, 2]]; d = V[:, 0]       # y,z ; depth x
    return P, T, d

def silhouette(P, T, scale, ox, oy):
    pts = P[T] / scale + np.array([ox, oy])
    area = 0.5 * np.abs((lambda a, b: a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0]))
    pts = pts[area > 1e-7]
    polys = shapely.polygons(pts)
    return unary_union(polys.tolist()).buffer(0.02).buffer(-0.02)

def draw_geom(g, fc="white", lw=LW_T, z=2):
    geoms = g.geoms if hasattr(g, "geoms") else [g]
    for p in geoms:
        if p.is_empty: continue
        ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, fc=fc, ec="black", lw=lw, zorder=z, joinstyle="round"))
        for h in p.interiors:
            ax.add_patch(MPoly(np.array(h.coords), closed=True, fc="white", ec="black", lw=lw, zorder=z + 0.1))

def view(name, scale, ox, oy, order_far_first=True, fills=True):
    items = []
    for m in parts:
        P, T, d = project(m, name)
        items.append((np.mean(d), m, P, T))
    items.sort(key=lambda t: -t[0] if order_far_first else t[0])
    allg = []
    for z, (dm, m, P, T) in enumerate(items):
        g = silhouette(P, T, scale, ox, oy)
        if g.is_empty: continue
        draw_geom(g, fc="#f4f4f4" if m["mat"] != "tpu" else "#dcdcdc", z=2 + z * 0.01)
        allg.append(g)
    sil = unary_union(allg)
    geoms = sil.geoms if hasattr(sil, "geoms") else [sil]
    for p in geoms:
        ax.plot(*p.exterior.xy, color="black", lw=LW_O, zorder=9)
    return sil

def ln(x1, y1, x2, y2, lw=0.5, ls="-", c="black", z=8):
    ax.plot([x1, x2], [y1, y2], color=c, lw=lw, ls=ls, zorder=z)

def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color="black", lw=0.6, mutation_scale=7, shrinkA=0, shrinkB=0), zorder=10)

def dim_h(x1, x2, y, text, ext_from=None, fs=7.2, above=True, ext_to=None):
    if ext_from is not None:
        ln(x1, ext_from, x1, y + (1.5 if y > ext_from else -1.5), 0.35); ln(x2, ext_from, x2, y + (1.5 if y > ext_from else -1.5), 0.35)
    arrow((x1 + x2) / 2, y, x1, y); arrow((x1 + x2) / 2, y, x2, y)
    ax.text((x1 + x2) / 2, y + (1.3 if above else -3.2), text, ha="center", va="bottom", fontsize=fs, zorder=11,
            bbox=dict(fc="white", ec="none", pad=0.4))

def dim_v(y1, y2, x, text, ext_from=None, fs=7.2, left=True):
    if ext_from is not None:
        s = 1.5 if x > ext_from else -1.5
        ln(ext_from, y1, x + s, y1, 0.35); ln(ext_from, y2, x + s, y2, 0.35)
    arrow(x, (y1 + y2) / 2, x, y1); arrow(x, (y1 + y2) / 2, x, y2)
    ax.text(x - 1.2 if left else x + 1.2, (y1 + y2) / 2, text, ha="right" if left else "left", va="center", fontsize=fs,
            rotation=90, zorder=11, bbox=dict(fc="white", ec="none", pad=0.4))

# ---- sheet frame
ax.add_patch(Rectangle((5, 5), 410, 287, fc="none", ec="black", lw=1.6, zorder=1))
ax.add_patch(Rectangle((2, 2), 416, 293, fc="none", ec="black", lw=0.5, zorder=1))

# ================= SIDE VIEW =================
SX, SY = 22, 238
sil_s = view("side", SC, SX, SY)
ln(SX - 6, SY, SX + 707 / SC + 6, SY, 0.35, "-.", z=9)                       # centre line
ax.text(SX, SY + 42, "SIDE VIEW   (scale 1 : 2.5)", fontsize=9.5, fontweight="bold")
# chain dimensions above
segs = [(0, 130, "Head\n130"), (130, 165, "J1\n35"), (165, 260, "M1\n95"), (260, 295, "J2\n35"), (295, 390, "M2\n95"),
        (390, 425, "J3\n35"), (425, 520, "M3\n95"), (520, 555, "J4\n35"), (555, 685, "Tail\n130")]
yd = SY + 28
for a, b, t in segs:
    xa, xb = SX + a / SC, SX + b / SC
    ln(xa, SY + 21, xa, yd + 1.5, 0.3)
    arrow((xa + xb) / 2, yd, xa, yd); arrow((xa + xb) / 2, yd, xb, yd)
    ax.text((xa + xb) / 2, yd + 1.2, t, ha="center", va="bottom", fontsize=6.2, linespacing=1.0, zorder=11,
            bbox=dict(fc="white", ec="none", pad=0.2))
ln(SX + 685 / SC, SY + 21, SX + 685 / SC, yd + 1.5, 0.3)
# overall length below
yl = SY - 29
ln(SX, SY - 21, SX, yl - 1.5, 0.35); ln(SX + 707 / SC, SY - 24, SX + 707 / SC, yl - 1.5, 0.35)
dim_h(SX, SX + 707 / SC, yl, "707  overall (incl. rear eyebolt)", above=True)
# height dims
dim_v(SY - 50.5 / SC, SY + 50.5 / SC, SX - 7, "101  track span", ext_from=SX)
dim_v(SY - 42 / SC, SY + 42 / SC, SX + 722 / SC, "Ø84  body", ext_from=SX + 707 / SC - 14, left=False)

# ================= TOP VIEW =================
TX, TY = 22, 170
view("top", SC, TX, TY)
ln(TX - 6, TY, TX + 707 / SC + 6, TY, 0.35, "-.", z=9)
ax.text(TX, TY + 29, "TOP VIEW   (scale 1 : 2.5)", fontsize=9.5, fontweight="bold")
dim_v(TY - 50.5 / SC, TY + 50.5 / SC, TX - 7, "101", ext_from=TX)
dim_v(TY - 28 / SC, TY + 28 / SC, TX + 14, "Ø56 nose", ext_from=TX + 2, left=False)
yl2 = TY - 27
dim_h(TX + 165 / SC, TX + 520 / SC, yl2, "355  traction section (M1 - M3 with joints)", ext_from=TY - 20)

# ================= NOSE VIEW =================
NX, NY = 372, 238
view("nose", SC, NX, NY, order_far_first=True)
ln(NX - 24, NY, NX + 24, NY, 0.35, "-.", z=9); ln(NX, NY - 24, NX, NY + 24, 0.35, "-.", z=9)
ax.text(NX - 24, NY + 42, "NOSE VIEW   (1 : 2.5)", fontsize=9.5, fontweight="bold")
dim_h(NX - 50.5 / SC, NX + 50.5 / SC, NY - 29, "101", ext_from=NY - 22, above=True)
dim_v(NY - 50.5 / SC, NY + 50.5 / SC, NX + 30, "101", ext_from=NX + 22, left=False)

# ================= DETAIL A : tail at 1:1 =================
DS = 1.0
DX0, DY = 22, 82
tail_parts = [m for m in parts if m["seg"] == "tail" or m["name"].startswith("tail_")]
# show tail region only
sel = [m for m in parts if m["seg"] in ("tail",) or "J4_" in m["name"] and False]
items = []
for m in sel:
    P, T, d = project(m, "side")
    items.append((np.mean(d), m, P, T))
items.sort(key=lambda t: -t[0])
x_off = DX0 - 555 / DS
allg = []
for z, (dm, m, P, T) in enumerate(items):
    g = silhouette(P, T, DS, x_off, DY)
    if g.is_empty: continue
    draw_geom(g, fc="#f4f4f4", z=2 + z * 0.01); allg.append(g)
sil = unary_union(allg)
for p in (sil.geoms if hasattr(sil, "geoms") else [sil]): ax.plot(*p.exterior.xy, color="black", lw=LW_O, zorder=9)
ln(DX0 - 4, DY, DX0 + 160, DY, 0.35, "-.", z=9)
ax.text(DX0, DY + 52, "DETAIL A - TAIL & REAR ANCHOR   (scale 1 : 1)", fontsize=9.5, fontweight="bold")
ex, ez = x_off + 696.5, DY - 22
ax.annotate("M6 eyebolt (Al) - retrieval-line anchor", xy=(ex + 6, ez - 2), xytext=(DX0 + 95, DY - 52),
            fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6), zorder=12, ha="center")
ax.annotate("rear tether / cable exit  Ø12", xy=(x_off + 685, DY + 1), xytext=(DX0 + 118, DY + 52 - 14),
            fontsize=7.5, arrowprops=dict(arrowstyle="-", lw=0.6), zorder=12, ha="center")
dim_h(x_off + 555, x_off + 685, DY - 47, "130  tail body", ext_from=DY - 42)
dim_h(x_off + 685, x_off + 707, DY - 47, "22", ext_from=DY - 42)
dim_v(DY - 42, DY + 42, DX0 - 6, "Ø84", ext_from=DX0)

# ================= NOTES =================
nx0, ny0 = 235, 62
notes = [
    "GENERAL NOTES",
    "1. All dimensions in millimetres.",
    "2. Views are projections of the parametric 3D model",
    "    (sara_cad.py, CadQuery); not hand-drawn.",
    "3. Internal electronics, bearings, tendons and",
    "    fasteners are omitted for clarity.",
    "4. Materials: PETG shells, TPU belts / nose / sleeves,",
    "    Al 6061 joint yokes + rear eyebolt, steel pins.",
    "5. Segment order (nose to tail): Head, J1, M1, J2, M2,",
    "    J3, M3, J4, Tail. 3 traction modules, 4 belts each.",
    "6. Estimated mass 1.15 kg (printed). Not yet fabricated.",
]
ax.add_patch(Rectangle((nx0 - 3, ny0 - 3), 183, 77, fc="none", ec="black", lw=0.6))
for i, t in enumerate(notes):
    ax.text(nx0, ny0 + 68 - i * 6.3, t, fontsize=7.6 if i else 8.5, fontweight="bold" if i == 0 else "normal", va="center")

# ================= TITLE BLOCK =================
bx, by, bw, bh = 235, 8, 177, 44
ax.add_patch(Rectangle((bx, by), bw, bh, fc="white", ec="black", lw=1.2, zorder=3))
ln(bx, by + 26, bx + bw, by + 26, 0.8); ln(bx + 110, by, bx + 110, by + 26, 0.8)
ln(bx, by + 13, bx + 110, by + 13, 0.5); ln(bx + 140, by, bx + 140, by + 26, 0.5)
ax.text(bx + 4, by + 38, "SARA - Snake-Assisted Rescue Automaton", fontsize=13, fontweight="bold", va="center")
ax.text(bx + 4, by + 30, "General assembly - orthographic views and tail detail", fontsize=8.5, va="center")
ax.text(bx + 4, by + 20.5, "Vishwakarma Awards 2026-27, Stage 2", fontsize=7.8, va="center")
ax.text(bx + 4, by + 16, "Application ID: VK26-AU-PAI-0062", fontsize=7.8, va="center", fontweight="bold")
ax.text(bx + 4, by + 7, "Team: Rahul Dev, Ankush Kumar, Rahul Agrawal, Anjil Ghosh", fontsize=7, va="center")
ax.text(bx + 4, by + 2.7, "Source: sara_cad.py (AI-assisted parametric model)", fontsize=6.6, va="center", color="#444")
ax.text(bx + 114, by + 20, "SCALE", fontsize=6, va="center", color="#444"); ax.text(bx + 114, by + 14.5, "1 : 2.5  /  1 : 1", fontsize=8, va="center")
ax.text(bx + 114, by + 9, "UNITS", fontsize=6, va="center", color="#444"); ax.text(bx + 114, by + 4, "mm", fontsize=8, va="center")
ax.text(bx + 143, by + 20, "DATE", fontsize=6, va="center", color="#444"); ax.text(bx + 143, by + 14.5, "25-Oct-2026", fontsize=8, va="center")
ax.text(bx + 143, by + 9, "SHEET", fontsize=6, va="center", color="#444"); ax.text(bx + 143, by + 4, "1 of 1", fontsize=8, va="center")

fig.savefig("SARA_2D_Drawing.png", dpi=150)
fig.savefig("SARA_2D_Drawing.pdf")
print("done")
