"""
Builds Nysa's long dark coat (with sleeves), belt, shoulder bag and its strap as one static OBJ, shaped around her
MetaHuman body in the lamp pose. Reads the pose landmarks from Saved/nysa_mh_pose.json (component space of the
MetaHuman: feet at the origin, she faces +Y, her right is -X, centimetres) and writes
SourceArt/Nysa/coat/NysaCoat.obj with material groups Coat, Leather.
Plain Python, no Unreal needed:  python -I Scripts/make_nysa_coat.py
"""
import json
import math
import os
import random

POSE = "C:/LETHE/Saved/nysa_mh_pose.json"
OUT = "C:/LETHE/SourceArt/Nysa/coat/NysaCoat.obj"
rng = random.Random(5)
pose = json.load(open(POSE))
B, ARMS = pose["bones"], pose["arms"]

V, F = [], {"Coat": [], "Leather": []}


def vert(p):
    V.append(p)
    return len(V)


def quad(mat, a, b, c, d):
    F[mat].append((a, b, c))
    F[mat].append((a, c, d))


# ---------------------------------------------------------------- the coat body: rings of ellipses up the spine
# (z, half-width x, depth to the front, depth to the back), smoothed between keys
PROFILE = [(2, 29.5, 21, 22), (20, 27.5, 19.5, 20.5), (45, 24.5, 17, 18), (70, 21.5, 14.5, 15.5), (86, 19.0, 12.5, 13.0),
           (96, 16.0, 11.5, 10.8), (104, 15.0, 11.0, 10.3), (116, 16.5, 12.8, 10.3), (126, 18.5, 13.0, 10.8),
           (133, 21.0, 12.0, 11.5), (138, 21.0, 11.5, 11.5), (142, 18.5, 11.5, 12.8), (146, 14.0, 10.0, 11.5), (150, 10.8, 9.0, 10.2),
           (156, 10.2, 9.0, 9.8)]


def lerp_profile(z):
    for (z0, *a), (z1, *b) in zip(PROFILE, PROFILE[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            t = t * t * (3 - 2 * t)
            return [x + (y - x) * t for x, y in zip(a, b)]
    return PROFILE[0][1:] if z < PROFILE[0][0] else PROFILE[-1][1:]


SP = sorted((B[k][2], B[k][1]) for k in ("pelvis", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02"))


def center_y(z):
    if z <= SP[0][0]:
        return SP[0][1]
    for (z0, y0), (z1, y1) in zip(SP, SP[1:]):
        if z0 <= z <= z1:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
    return SP[-1][1]


NA = 144
PH = [rng.uniform(0, 6.28) for _ in range(6)]


def fold(z, th):
    """Radial fold factor: deep soft folds below the belt, a few creases above."""
    below = max(0.0, min(1.0, (96.0 - z) / 70.0))
    a = 0.015 + 0.10 * below
    back = 0.5 + 0.5 * max(0.0, -math.sin(th))          # fuller folds at the back
    # soft rolling folds plus sharper ridges (|sin|), which catch the light the way heavy wool does
    ridge = abs(math.sin(5 * th + PH[4] + z * 0.006)) - 0.62
    k = 1.0 + a * back * (0.50 * math.sin(7 * th + PH[0] + z * 0.01) + 0.28 * math.sin(12 * th + PH[1] - z * 0.02)
                          + 0.22 * math.sin(4 * th + PH[2]) + 0.55 * ridge) + 0.006 * math.sin(23 * th + PH[3] + z * 0.2)
    # the centre-back seam: a shallow line down the back, with a vent opening below the hips
    db = abs(((th + math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi)
    if db < 0.07 and z < 140:
        k -= (0.022 if z > 60 else 0.045) * (1 - db / 0.07)
    return k


def ring_point(z, th, grow=0.0):
    rx, yf, yb = lerp_profile(z)
    s, c = math.sin(th), math.cos(th)
    ry = yf if s > 0 else yb
    k = fold(z, th)
    return ((rx + grow) * c * k, center_y(z) + (ry + grow) * s * k, z)


ZS = [2.0 + i * 2.5 for i in range(int((156 - 2) / 2.5) + 1)]
rings = []
for zi, z in enumerate(ZS):
    zz = z + (0.8 * math.sin(3 * PH[4] + 5.0) if zi == 0 else 0.0)
    row = []
    for a in range(NA):
        th = 2 * math.pi * a / NA
        p = list(ring_point(z, th))
        if zi == 0:
            p[2] = 1.5 + 1.2 * math.sin(3 * th + PH[4]) + 0.8 * math.sin(7 * th + PH[5])   # uneven hem
        row.append(vert(tuple(p)))
    rings.append(row)
for r0, r1 in zip(rings, rings[1:]):
    for a in range(NA):
        quad("Coat", r0[a], r0[(a + 1) % NA], r1[(a + 1) % NA], r1[a])
# hem turned up inside (so the edge has thickness)
inner = []
for a in range(NA):
    x, y, z = V[rings[0][a] - 1]
    cy = center_y(z)
    inner.append(vert((x * 0.94, cy + (y - cy) * 0.94, z + 3.0)))
for a in range(NA):
    quad("Coat", inner[a], inner[(a + 1) % NA], rings[0][(a + 1) % NA], rings[0][a])


# ---------------------------------------------------------------- sleeves: tubes along shoulder -> elbow -> wrist
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l_ = math.sqrt(dot(a, a)) or 1.0
    return mul(a, 1.0 / l_)


def catmull(pts, n):
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(pts[-1])
    return out


def tube(path, radii, mat="Coat", seg=24, cap=False, wrinkle=0.0):
    up = (0.0, 0.0, 1.0)
    prev_n = None
    rows = []
    for i, p in enumerate(path):
        t = norm(sub(path[min(i + 1, len(path) - 1)], path[max(i - 1, 0)]))
        n = prev_n if prev_n is not None else norm(cross(t, up if abs(dot(t, up)) < 0.9 else (1, 0, 0)))
        n = norm(sub(n, mul(t, dot(n, t))))
        b = cross(t, n)
        prev_n = n
        r = radii(i / (len(path) - 1))
        row = []
        for a in range(seg):
            th = 2 * math.pi * a / seg
            w = 1.0 + wrinkle * math.sin(5 * th + i * 0.9) * math.sin(i * 0.7)
            row.append(vert(add(p, add(mul(n, r * w * math.cos(th)), mul(b, r * w * math.sin(th))))))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for a in range(seg):
            quad(mat, r0[a], r0[(a + 1) % seg], r1[(a + 1) % seg], r1[a])
    return rows


for sd in ("r", "l"):
    S, E, H = (tuple(ARMS[sd][k]) for k in ("shoulder", "elbow", "hand"))
    inward = norm((-S[0], 0.0, 0.0))
    S0 = add(add(S, mul(inward, 5.0)), (0, 0, 1.5))          # start inside the shoulder of the coat
    W = add(H, mul(norm(sub(E, H)), 1.5))                    # cuff just short of the wrist bone
    path = catmull([S0, add(S, (0, 0, 1.0)), E, W], 8)
    tube(path, lambda t: 9.4 - 3.6 * t + 0.8 * math.sin(math.pi * t), wrinkle=0.06)      # loose coat sleeves, narrower at the wrist
    # cuff: a slightly wider short band
    d_ = norm(sub(W, E))
    tube([add(W, mul(d_, -4.0)), W], lambda t: 5.5, seg=24)


# ---------------------------------------------------------------- belt at the waist
def surf(z, th, grow):
    return ring_point(z, th, grow)


belt = []
for z in (97.0, 101.5):
    row = []
    for a in range(NA):
        th = 2 * math.pi * a / NA
        x, y, zz = surf(z, th, 0.9)
        row.append(vert((x, y, zz)))
    belt.append(row)
for a in range(NA):
    quad("Leather", belt[0][a], belt[0][(a + 1) % NA], belt[1][(a + 1) % NA], belt[1][a])


# ---------------------------------------------------------------- the bag: on her right hip, toward the back
def box(c, size, yaw_deg, mat="Leather", sag=0.0):
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    cy_, sy_ = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    pts = {}
    for i in (-1, 1):
        for j in (-1, 1):
            for k in (-1, 1):
                lx, ly, lz = i * hx * (1 + (sag if k < 0 else 0)), j * hy, k * hz
                pts[(i, j, k)] = vert((c[0] + lx * cy_ - ly * sy_, c[1] + lx * sy_ + ly * cy_, c[2] + lz))
    P = pts
    quad(mat, P[(-1, -1, -1)], P[(1, -1, -1)], P[(1, -1, 1)], P[(-1, -1, 1)])
    quad(mat, P[(1, 1, -1)], P[(-1, 1, -1)], P[(-1, 1, 1)], P[(1, 1, 1)])
    quad(mat, P[(-1, 1, -1)], P[(-1, -1, -1)], P[(-1, -1, 1)], P[(-1, 1, 1)])
    quad(mat, P[(1, -1, -1)], P[(1, 1, -1)], P[(1, 1, 1)], P[(1, -1, 1)])
    quad(mat, P[(-1, -1, 1)], P[(1, -1, 1)], P[(1, 1, 1)], P[(-1, 1, 1)])
    quad(mat, P[(-1, 1, -1)], P[(1, 1, -1)], P[(1, -1, -1)], P[(-1, -1, -1)])


bx, bz = -14.0, 84.0
th_b = math.atan2(-1.0, bx / 16.0)                    # where on the hip ellipse it hangs
hip = surf(bz, -math.pi / 2 - 0.55, 0.0)
bag_c = (hip[0] - 1.0, hip[1] - 5.0, bz)
box(bag_c, (23.0, 8.0, 19.0), 18.0, sag=0.06)                     # body
box((bag_c[0] + 0.3, bag_c[1] - 4.3, bag_c[2] + 4.5), (24.0, 1.2, 11.0), 18.0)   # flap
box((bag_c[0] + 0.3, bag_c[1] - 5.0, bag_c[2] + 0.5), (3.0, 0.8, 3.5), 18.0)     # buckle tab

# strap: from the left shoulder, diagonally across the back, to the bag's top
top_l = (10.0, -4.0, 141.5)
end_ = (bag_c[0] + 8.0, bag_c[1] + 1.0, bag_c[2] + 9.5)
NS = 40
rows = []
for i in range(NS + 1):
    t = i / NS
    x = top_l[0] + (end_[0] - top_l[0]) * t
    z = top_l[2] + (end_[2] - top_l[2]) * t
    rx, yf, yb = lerp_profile(z)
    q = max(-0.98, min(0.98, x / rx))
    yb_s = center_y(z) - yb * math.sqrt(1 - q * q) * fold(z, -math.pi / 2) - 0.9
    if t > 0.85:                                         # drop onto the bag
        yb_s = yb_s + (end_[1] - yb_s) * (t - 0.85) / 0.15
    if t < 0.06:                                         # over the shoulder top
        yb_s += 2.5 * (0.06 - t) / 0.06
    d = (end_[0] - top_l[0], end_[2] - top_l[2])
    l_ = math.hypot(*d)
    px, pz = -d[1] / l_ * 1.9, d[0] / l_ * 1.9
    rows.append((vert((x - px, yb_s, z - pz)), vert((x + px, yb_s, z + pz))))
for (a0, b0), (a1, b1) in zip(rows, rows[1:]):
    quad("Leather", a0, b0, b1, a1)

# ---------------------------------------------------------------- write
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write("# Nysa's coat, belt, bag (Scripts/make_nysa_coat.py), MetaHuman component space, cm, Z up\n")
    for p in V:
        f.write("v %.3f %.3f %.3f\n" % p)
    for mat, tris in F.items():
        f.write("usemtl %s\n" % mat)                  # one object, two materials (no groups: one static mesh)
        for a, b, c in tris:
            f.write("f %d %d %d\n" % (a, b, c))
print("wrote %s: %d verts, %s" % (OUT, len(V), {k: len(v) for k, v in F.items()}))
