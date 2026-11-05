"""
Sculpted mud for the gate shot's foreground: a heightfield mesh (OBJ, world centimetres, Z up) with two cart ruts
running to the gate, churned old footprints, clods, and Nysa's own fresh prints leading up to where she stands.
It replaces the flat ground in view; its edges sink below the flat plane, which the build lowers to meet them.
Plain Python:  python -I Scripts/make_mud_patch.py      Out: SourceArt/Ground/MudPatch.obj
Numbers match Scripts/build_beauty_gate.py: camera (-214.8, 651.4) looking yaw -35, post (225, 465),
Nysa at (141, 436) facing yaw 27 (from the build log).
"""
import math
import os
import random

OUT = "C:/LETHE/SourceArt/Ground/MudPatch.obj"
rng = random.Random(1587)
CAM = (-214.8, 651.4)
YAW = math.radians(-35.0)
F = (math.cos(YAW), math.sin(YAW))                  # camera forward on the ground
R = (-math.sin(YAW), math.cos(YAW))                 # camera right (as the build's CR)
NYSA = (141.0, 436.0)
NYAW = math.radians(27.0)
STEP = 5.0
D0, D1 = 40.0, 1500.0                               # forward range from the camera
L0, L1 = -1000.0, 1000.0                            # lateral range


def hsh(i, j, s):
    h = (i * 374761393 + j * 668265263 + s * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / 16777215.0


def vn(x, y, s):
    i, j = math.floor(x), math.floor(y)
    fx, fy = x - i, y - j
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = hsh(i, j, s), hsh(i + 1, j, s), hsh(i, j + 1, s), hsh(i + 1, j + 1, s)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy - 0.5


def fbm(x, y):
    return 3.2 * vn(x / 190, y / 190, 1) + 1.6 * vn(x / 65, y / 65, 2) + 0.8 * vn(x / 22, y / 22, 3) + 0.35 * vn(x / 7, y / 7, 4)


# cart ruts: two lines 150 cm apart, from near the camera's left toward the gate gap (x ~ 700, y ~ 0)
RUT_A, RUT_B = (-260.0, 300.0), (700.0, -60.0)       # off to the left of the frame, into the gate
rd = (RUT_B[0] - RUT_A[0], RUT_B[1] - RUT_A[1])
rl = math.hypot(*rd)
ru = (rd[0] / rl, rd[1] / rl)
rn = (-ru[1], ru[0])


def rut_h(x, y):
    px, py = x - RUT_A[0], y - RUT_A[1]
    t = px * ru[0] + py * ru[1]
    if t < -50 or t > rl + 100:
        return 0.0
    s = px * rn[0] + py * rn[1] + 8.0 * math.sin(t / 160.0)          # the track wanders a little
    h = 0.0
    for off in (-75.0, 75.0):
        d = s - off
        h += -3.6 * math.exp(-(d / 10.0) ** 2) + 1.1 * math.exp(-((abs(d) - 15.0) / 6.0) ** 2)   # groove and its squeezed-up lip
    fade = min(1.0, (t + 50) / 120.0)
    return h * fade


# footprints: (x, y, heading, depth)
PRINTS = []
# hers: a fresh trail from the camera side up to where she stands, last two prints side by side
tx, ty = NYSA
back = (math.cos(NYAW + math.pi + 0.35), math.sin(NYAW + math.pi + 0.35))
head = NYAW
for k in range(9):
    side = 1 if k % 2 else -1
    bx = tx + back[0] * (k * 62.0 + 40.0) + math.cos(head + math.pi / 2) * 10 * side
    by = ty + back[1] * (k * 62.0 + 40.0) + math.sin(head + math.pi / 2) * 10 * side
    PRINTS.append((bx, by, head + rng.gauss(0, 0.08), 2.4))
# old, trodden in: everywhere, but most on the approach to the gate
for _ in range(320):
    t = rng.uniform(0, 1)
    x = RUT_A[0] + rd[0] * t + rng.gauss(0, 240)
    y = RUT_A[1] + rd[1] * t + rng.gauss(0, 240)
    PRINTS.append((x, y, rng.uniform(0, 6.28), rng.uniform(0.8, 2.4)))
CLODS = [(rng.uniform(-300, 900), rng.uniform(-200, 800), rng.uniform(3, 11), rng.uniform(0.8, 2.6)) for _ in range(260)]


def print_h(x, y):
    h = 0.0
    for (px, py, a, dep) in PRINTS:
        dx, dy = x - px, y - py
        if dx * dx + dy * dy > 900:
            continue
        u = dx * math.cos(a) + dy * math.sin(a)          # along the foot
        v = -dx * math.sin(a) + dy * math.cos(a)
        e = (u / 13.0) ** 2 + (v / (5.0 if u > -3 else 4.2)) ** 2
        if e < 1.0:
            h -= dep * (1 - e) ** 0.6
        elif e < 1.6:
            h += 0.5 * dep * (1 - abs(e - 1.3) / 0.3) if abs(e - 1.3) < 0.3 else 0.0   # pushed-up rim
    return h


def clod_h(x, y):
    h = 0.0
    for (cx, cy, r, hh) in CLODS:
        d2 = (x - cx) ** 2 + (y - cy) ** 2
        if d2 < r * r:
            h += hh * (1 - d2 / (r * r)) ** 1.5
    return h


def height(x, y, d, l):
    h = fbm(x, y) * 0.9 + rut_h(x, y) + print_h(x, y) + clod_h(x, y)
    edge = min(d - D0, D1 - d, l - L0, L1 - l)
    if edge < 60:
        h = h * max(0.0, edge / 60.0) - 12.0 * (1 - max(0.0, edge / 60.0))
    return h


nd = int((D1 - D0) / STEP) + 1
nl = int((L1 - L0) / STEP) + 1
V, T = [], []
for i in range(nd):
    d = D0 + i * STEP
    for j in range(nl):
        l = L0 + j * STEP
        x = CAM[0] + F[0] * d + R[0] * l
        y = CAM[1] + F[1] * d + R[1] * l
        V.append((x, y, height(x, y, d, l)))
        T.append((x / 8000.0, y / 8000.0))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write("# LETHE gate foreground mud (Scripts/make_mud_patch.py), world cm, Z up\n")
    for p in V:
        f.write("v %.2f %.2f %.2f\n" % p)
    for t in T:
        f.write("vt %.5f %.5f\n" % t)
    f.write("usemtl Mud\n")
    for i in range(nd - 1):
        for j in range(nl - 1):
            a = i * nl + j + 1
            b, c, e = a + 1, a + nl + 1, a + nl
            f.write("f %d/%d %d/%d %d/%d\nf %d/%d %d/%d %d/%d\n" % (a, a, c, c, b, b, a, a, e, e, c, c))
print("wrote %s: %d x %d vertices, %d prints" % (OUT, nd, nl, len(PRINTS)))
