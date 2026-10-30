"""
Writes axe-hewn stake points as OBJ meshes: C:/LETHE/SourceArt/Hewn/HewnTip_<n>.obj
Each point is 4-6 uneven axe facets running from the round of the log (diameter 100 units) up to an
off-centre apex, flat-shaded per facet so each cut reads as one plane. OBJ is Y-up; the base sits at y = 0.
Run with any Python 3:  python -I make_hewn_tips.py
"""
import math
import os
import random

OUT = "C:/LETHE/SourceArt/Hewn"
RING = 24


def tip(seed):
    r = random.Random(seed)
    facets = r.randint(4, 6)
    height = r.uniform(110, 175)
    apex = (r.uniform(-14, 14), height, r.uniform(-14, 14))
    # Split the ring into facets of uneven width.
    cuts = sorted(r.uniform(0, RING) for _ in range(facets))
    ring = []
    for i in range(RING):
        a = 2 * math.pi * i / RING
        rad = 50 * r.uniform(0.98, 1.02)
        ring.append((rad * math.cos(a), 0.0, rad * math.sin(a)))
    group = []
    for i in range(RING):
        g = sum(1 for c in cuts if c <= i) % facets
        group.append(g)
    # Each facet's axe stroke starts a little higher on one side: lift the ring vertices per facet.
    lift = [r.uniform(0, 18) for _ in range(facets)]
    ring = [(x, y + lift[group[i]] * (0.4 + 0.6 * ((i % 3) / 2)), z) for i, (x, y, z) in enumerate(ring)]

    v, vt, vn, f = [], [], [], []

    def add_v(p):
        v.append(p)
        vt.append((p[0] / 100 + 0.5, p[1] / 100))
        return len(v)

    ia = add_v(apex)
    ids = [add_v(p) for p in ring]
    # Facet normals: average of its triangles' normals.
    tris = []
    for i in range(RING):
        a, b = ring[i], ring[(i + 1) % RING]
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (apex[0] - a[0], apex[1] - a[1], apex[2] - a[2])
        n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        tris.append((i, n))
    acc = {}
    for i, n in tris:
        g = group[i]
        s = acc.setdefault(g, [0.0, 0.0, 0.0])
        for k in range(3):
            s[k] += n[k]
    for g in range(facets):
        s = acc.get(g, [0, 1, 0])
        ln = math.sqrt(sum(c * c for c in s)) or 1
        # Written inward-wound with inward normals on purpose: the FBX/OBJ import mirrors the mesh along its
        # axis, which turns both outward. Placement in build_beauty_gate.py puts the base last to undo the flip.
        vn.append((s[0] / ln, s[1] / ln, s[2] / ln))
    # Outward normals point away from the axis; flip winding if needed.
    for i, _ in tris:
        a, b = ids[i], ids[(i + 1) % RING]
        ni = group[i] + 1
        f.append((a, b, ia, ni))
    return v, vt, vn, f


def write(path, data):
    v, vt, vn, f = data
    with open(path, "w", encoding="ascii") as fh:
        fh.write("# LETHE axe-hewn stake point\n")
        for p in v:
            fh.write("v %.3f %.3f %.3f\n" % p)
        for t in vt:
            fh.write("vt %.4f %.4f\n" % t)
        for n in vn:
            fh.write("vn %.4f %.4f %.4f\n" % n)
        fh.write("s off\n")
        for a, b, c, n in f:
            fh.write("f %d/%d/%d %d/%d/%d %d/%d/%d\n" % (a, a, n, b, b, n, c, c, n))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for i in range(6):
        write("%s/HewnTip_%d.obj" % (OUT, i), tip(1590 + i * 17))
    print("wrote 6 hewn tips to " + OUT)
