import pickle, math, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/out"
meshes = pickle.load(open(OUT + "/meshes.pkl", "rb"))

def render(sel, fname, exploded=False, az=-35, el=28, size=(16, 6.2), title=None, dpi=170, pad=0.04):
    a, e = math.radians(az), math.radians(el)
    ca, sa, ce, se = math.cos(a), math.sin(a), math.cos(e), math.sin(e)
    L = np.array([-0.45, -0.55, 0.7]); L /= np.linalg.norm(L)
    polys, cols, depth = [], [], []
    for m in meshes:
        if not sel(m):
            continue
        V = np.array(m["v"], dtype=float)
        T = np.array(m["t"], dtype=int)
        if len(V) == 0 or len(T) == 0:
            continue
        if exploded:
            V = V + np.array(m["explode"])
        xp = V[:, 0] * ca - V[:, 1] * sa
        yp = V[:, 0] * sa + V[:, 1] * ca
        zp = V[:, 2]
        sx = xp
        sy = zp * ce + yp * se
        dp = yp * ce - zp * se
        P = np.stack([xp, yp, zp], 1)
        tri = P[T]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nl = np.linalg.norm(n, axis=1); nl[nl == 0] = 1
        n = n / nl[:, None]
        # rotate normal into view frame: components (xp, yp, zp) already in that frame
        shade = 0.38 + 0.62 * np.abs(n @ L)
        base = np.array(m["color"])
        c = np.clip(base[None, :] * shade[:, None], 0, 1)
        S = np.stack([sx, sy], 1)[T]
        polys.append(S); cols.append(c); depth.append(dp[T].mean(1))
    polys = np.concatenate(polys); cols = np.concatenate(cols); depth = np.concatenate(depth)
    order = np.argsort(-depth)
    fig, ax = plt.subplots(figsize=size)
    pc = PolyCollection(polys[order], facecolors=cols[order], edgecolors=cols[order], linewidths=0.25)
    ax.add_collection(pc)
    allp = polys.reshape(-1, 2)
    xm, xM = allp[:, 0].min(), allp[:, 0].max(); ym, yM = allp[:, 1].min(), allp[:, 1].max()
    dx, dy = (xM - xm) * pad, (yM - ym) * pad
    ax.set_xlim(xm - dx, xM + dx); ax.set_ylim(ym - dy, yM + dy)
    ax.set_aspect("equal"); ax.axis("off")
    if title:
        ax.set_title(title, fontsize=12, color="#222")
    fig.patch.set_facecolor("white")
    fig.savefig(fname, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", fname, len(polys), "triangles")

allsel = lambda m: True
render(lambda m: m["role"] != "tendon", OUT + "/01_SARA_Assembly_Isometric.png", size=(17, 6.5))
render(allsel, OUT + "/02_SARA_Exploded_Isometric.png", exploded=True, size=(18, 7.5), az=-30, el=24)
render(lambda m: m["seg"] == "head" and m["role"] != "shell_top", OUT + "/03_Head_Cutaway.png",
       size=(10, 6.5), az=-38, el=22)
render(lambda m: m["seg"] == "tail" and m["role"] != "shell_top", OUT + "/04_Tail_Cutaway.png",
       size=(10, 6.5), az=-38, el=26)
render(lambda m: m["seg"] in ("M1", "J1", "J2"), OUT + "/05_Module_and_Joints.png",
       size=(11, 6.5), az=-35, el=24)

render(allsel, OUT + "/06_SARA_Front_View.png", size=(8, 8), az=90, el=0)
