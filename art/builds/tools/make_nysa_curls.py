"""
Generates Nysa's long dark ringlets as hair strands (a USD groom: BasisCurves under a GroomAPI prim), in her MetaHuman's
component space (feet at the origin, facing +Y, her right is -X, cm). Roots cover the top, sides and back of the head;
the hair flows over the skull, then hangs down her back over the coat in clumped ringlets to mid-back.
Reads the head position from Saved/nysa_mh_pose.json and the coat profile from Scripts/make_nysa_coat.py's numbers.
Plain Python:  python -I Scripts/make_nysa_curls.py [strands]
Out: SourceArt/Nysa/curls/NysaCurls.usda  (Y is written negated: Unreal flips Y when it reads USD)
"""
import json
import math
import os
import random
import sys

N_STRANDS = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("LETHE_CURL_STRANDS", "16000"))
OUT = "C:/LETHE/SourceArt/Nysa/curls/NysaCurls.usda"
rng = random.Random(21)
pose = json.load(open("C:/LETHE/Saved/nysa_mh_pose.json"))
HEAD = pose["bones"]["head"]                         # (0, 0.85, 154.7)

# skull: an ellipsoid round the head (cm), a little behind and above the head joint
C = (0.0, HEAD[1] - 0.6, HEAD[2] + 7.2)
AX, AY, AZ = 8.9, 11.0, 11.8                         # the whole skull, crown to the hairline over the forehead


def surf(u, v, grow=0.0):
    """Point on the skull ellipsoid. u: around (0 = her front, pi = back), v: from the top (0) down (pi)."""
    sx, sy, sz = math.sin(v) * math.sin(u), math.sin(v) * math.cos(u), math.cos(v)
    return (C[0] + (AX + grow) * sx, C[1] + (AY + grow) * sy, C[2] + (AZ + grow) * sz)


# the head is turned toward the post in the pose (make_nysa_pose_anim.py): the hair on it turns with it
_TURN = math.radians(pose.get("head_turn", 0.0)) * (pose.get("head_axis", [0, 0, 1])[2] or 1.0)
_PIV = pose.get("head_pivot", HEAD)


def turned(p):
    c_, s_ = math.cos(_TURN), math.sin(_TURN)
    dx, dy = p[0] - _PIV[0], p[1] - _PIV[1]
    return (_PIV[0] + dx * c_ - dy * s_, _PIV[1] + dx * s_ + dy * c_, p[2])


def surf_t(u, v, grow=0.0):
    return turned(surf(u, v, grow))


def on_scalp(p):
    x, y, z = p
    if z < 146.5:
        return False
    face = y > C[1] + 6.0 and z < C[2] + 3.2         # no hair over the forehead and face (hairline low on the brow)
    ear = abs(x) > 6.5 and z < C[2] - 2.0 and y > C[1] - 2.0
    return not face and not ear


# the back of her coat (from make_nysa_coat.py's profile), so the hair lies on it rather than inside it
PROFILE = [(86, 19.0, 12.5, 13.0), (96, 16.0, 11.5, 10.8), (104, 15.0, 11.0, 10.3), (116, 16.5, 12.8, 10.3), (126, 18.5, 13.0, 10.8),
           (133, 21.0, 12.0, 11.5), (138, 21.0, 11.5, 11.5), (142, 18.5, 11.5, 12.8), (146, 14.0, 10.0, 11.5), (150, 10.8, 9.0, 10.2),
           (156, 10.2, 9.0, 9.8)]
SPINE = sorted((pose["bones"][k][2], pose["bones"][k][1]) for k in ("pelvis", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02"))


def lerp_tab(tab, z):
    for (z0, *a), (z1, *b) in zip(tab, tab[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return [x + (y - x) * t for x, y in zip(a, b)]
    return tab[0][1:] if z < tab[0][0] else tab[-1][1:]


def center_y(z):
    if z <= SPINE[0][0]:
        return SPINE[0][1]
    for (z0, y0), (z1, y1) in zip(SPINE, SPINE[1:]):
        if z0 <= z <= z1:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
    return SPINE[-1][1]


def back_y(x, z):
    """Y of the coat's back surface at (x, z); nothing behind her below the head."""
    rx, yf, yb = lerp_tab(PROFILE, z)
    q = min(0.98, abs(x) / rx)
    return center_y(z) - yb * math.sqrt(1 - q * q)


# ------------------------------------------------------------------ roots, grouped into clumps (one ringlet each)
roots = []
while len(roots) < N_STRANDS:
    u = rng.uniform(0, 2 * math.pi)
    v = math.acos(rng.uniform(-0.25, 1.0))
    p = surf(u, v)
    if on_scalp(p):
        roots.append((u, v))
N_CLUMPS = max(60, N_STRANDS // 90)
clumps = [roots[rng.randrange(len(roots))] for _ in range(N_CLUMPS)]


def nearest_clump(r):
    pr = surf(*r)
    best, bd = 0, 1e9
    for i, c in enumerate(clumps):
        pc = surf(*c)
        d = sum((a - b) ** 2 for a, b in zip(pr, pc))
        if d < bd:
            best, bd = i, d
    return best


CL = []
for c in clumps:
    CL.append({"len": rng.uniform(36, 58), "rad": rng.uniform(1.6, 3.3), "pitch": rng.uniform(4.2, 7.0),
               "phase": rng.uniform(0, 6.28), "spin": rng.choice((-1, 1)), "drift": rng.uniform(-0.22, 0.22),
               "lift": rng.uniform(1.4, 3.6), "stand": rng.uniform(0.0, 5.5) ** 1.2, "wob": rng.uniform(0, 6.28),
               "wobf": rng.uniform(0.04, 0.10), "wa": rng.uniform(1.2, 3.4)})     # ringlets sway, none hangs plumb


def clump_path(ci):
    """The clump's centre line: over the skull, then hanging down the back. List of (x, y, z)."""
    u0, v0 = clumps[ci]
    c = CL[ci]
    pts = []
    # 1. over the skull: walk the surface downward (v increases) and toward the back, a little off the scalp
    u, v = u0, v0
    back_u = math.pi if u0 >= 0 else -math.pi
    while True:
        p = surf_t(u, v, c["lift"] * (0.4 + 0.6 * min(1.0, v / 1.6)))
        pts.append(p)
        if v > 1.9 or p[2] < 150.0:
            break
        v += 0.07
        # sweep toward the back of the head as it goes down (hair behind the ears)
        du = ((math.pi if (u % (2 * math.pi)) > 0 else 0.0) - (u % (2 * math.pi)))
        side = 1.0 if math.sin(u) >= 0 else -1.0
        target = math.pi - side * 0.55
        u += (target - (u % (2 * math.pi))) * 0.06
    # 2. hang: straight down from the release point, kept just behind the back of the coat, spreading slightly
    x0, y0, z0 = pts[-1]
    length = c["len"]
    s = 0.0
    step = 0.6
    z = z0
    while s < length:
        z -= step
        s += step
        # meander a little (no two ringlets hang the same), spread out lower down, and stand off the back by
        # different amounts so the curls pile up in depth instead of lying in one flat sheet
        # the mass falls a little toward her left (+X), as painted, leaving the strap on her right shoulder in view;
        # strands on her right side draw in toward the middle
        x = x0 * (1.0 + 0.007 * s) * (0.82 if x0 < 0 else 1.0) + c["drift"] * s + c["wa"] * math.sin(c["wob"] + s * c["wobf"]) \
            + 3.5 * min(1.0, s / 18.0)
        y = min(y0 - 0.02 * s, back_y(x, z) - 1.2 - c["stand"] * min(1.0, s / 15.0) - 0.03 * s) \
            + 0.8 * math.sin(c["wob"] * 1.7 + s * c["wobf"] * 0.8)
        pts.append((x, y, z))
    return pts


def tangent_frame(path, i):
    a, b = path[max(0, i - 1)], path[min(len(path) - 1, i + 1)]
    t = [b[k] - a[k] for k in range(3)]
    ln = math.sqrt(sum(x * x for x in t)) or 1
    t = [x / ln for x in t]
    up = (0.0, -1.0, 0.0) if abs(t[1]) < 0.9 else (1.0, 0.0, 0.0)
    n = [t[1] * up[2] - t[2] * up[1], t[2] * up[0] - t[0] * up[2], t[0] * up[1] - t[1] * up[0]]
    ln = math.sqrt(sum(x * x for x in n)) or 1
    n = [x / ln for x in n]
    b2 = [t[1] * n[2] - t[2] * n[1], t[2] * n[0] - t[0] * n[2], t[0] * n[1] - t[1] * n[0]]
    return t, n, b2


paths = [clump_path(i) for i in range(N_CLUMPS)]
frames = [[tangent_frame(p, i) for i in range(len(p))] for p in paths]

curves = []
for r in roots:
    ci = nearest_clump(r)
    c, path, fr = CL[ci], paths[ci], frames[ci]
    pr, pc = surf_t(*r), path[0]
    off0 = [pr[k] - pc[k] for k in range(3)]                 # where this strand starts relative to its clump
    jitter = rng.uniform(0.82, 1.18)
    ph_off = rng.gauss(0, 0.55)
    stray = rng.random() < 0.05                              # one in twenty works loose of its ringlet
    # each strand: its own place inside the ringlet, its own fine crimp, and a slow wander (smooth, no per-point noise)
    spread = [rng.gauss(0, 0.2), rng.gauss(0, 0.2)]
    crimp_r, crimp_p, crimp_ph = rng.uniform(0.02, 0.08), rng.uniform(0.7, 1.2), rng.uniform(0, 6.28)
    wand = [(rng.uniform(0.02, 0.09), rng.uniform(0, 6.28), rng.uniform(0.04, 0.16) * (14.0 if stray else 1.0)) for _ in range(2)]
    my_len = len(path) * rng.uniform(0.74, 1.0)
    n_over = next((i for i, p in enumerate(path) if p[2] < 150.0), len(path) // 4)
    pts = []
    for i, p in enumerate(path):
        if i > my_len:
            break
        t, n, b = fr[i]
        k = i / max(1, len(path) - 1)
        # blend from the root offset (on the scalp) into the ringlet (round the clump's centre line)
        w = min(1.0, max(0.0, (i - n_over) / 10.0))
        hang = max(0.0, i - n_over) * 0.6
        # waves start above the ears, open into ringlets as the hair hangs; the curl size breathes along the length
        # loose waves already over the crown (the painting's hair is curly right from the top), full ringlets once it hangs
        sc_ = i * 0.65
        ring = c["rad"] * jitter * max(0.38, min(1.0, (hang + 3.0) / 10.0)) * (0.85 + 0.35 * k) * (0.8 + 0.35 * math.sin(sc_ * 0.21 + c["wob"]))     # ringlets loosen toward the ends
        ang = c["phase"] + ph_off + c["spin"] * 2 * math.pi * sc_ / (c["pitch"] * (1.0 + 0.15 * math.sin(sc_ * 0.13)))
        roff = [ring * (math.cos(ang) * n[j] + math.sin(ang) * b[j]) for j in range(3)]
        # spread inside the ringlet once it hangs, a fine crimp round the strand's own path, and a slow wander
        sp_ = w * (1.0 + 0.6 * k)
        ca_ = crimp_ph + 2 * math.pi * sc_ / crimp_p
        wx_ = sum(a_ * math.sin(f_ * sc_ + p_) for (f_, p_, a_) in wand[:1]) * w
        wy_ = sum(a_ * math.sin(f_ * sc_ + p_) for (f_, p_, a_) in wand[1:]) * w
        q = [p[j] + off0[j] * (1 - w) * (1 - 0.6 * min(1.0, i / max(1, n_over))) + roff[j]
             + (spread[0] * sp_ + crimp_r * math.cos(ca_) + wx_) * n[j] + (spread[1] * sp_ + crimp_r * math.sin(ca_) + wy_) * b[j]
             for j in range(3)]
        pts.append(q)
    if len(pts) > 4:
        curves.append(pts)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
nv = sum(len(c) for c in curves)
with open(OUT, "w") as f:
    f.write('#usda 1.0\n(\n    defaultPrim = "NysaCurls"\n    metersPerUnit = 0.01\n    upAxis = "Z"\n)\n\n')
    f.write('def Xform "NysaCurls" (\n    prepend apiSchemas = ["GroomAPI"]\n)\n{\n')
    f.write('    def BasisCurves "Hair"\n    {\n        uniform token type = "linear"\n        uniform token wrap = "nonperiodic"\n')
    f.write("        int[] curveVertexCounts = [%s]\n" % ", ".join(str(len(c)) for c in curves))
    f.write("        point3f[] points = [")
    f.write(", ".join("(%.3f, %.3f, %.3f)" % (p[0], -p[1], p[2]) for c in curves for p in c))
    f.write("]\n")
    f.write("        float[] widths = [%s] (\n            interpolation = \"vertex\"\n        )\n" %
            ", ".join("%.4f" % (0.013 * (1.0 - 0.7 * i / max(1, len(c) - 1))) for c in curves for i in range(len(c))))
    f.write("    }\n}\n")
print("wrote %s: %d strands, %d clumps, %d points" % (OUT, len(curves), N_CLUMPS, nv))
