"""
Writes axe-hewn stake points as OBJ meshes: C:/LETHE/SourceArt/Hewn/HewnTip_<n>.obj
A point is what is left of the log's round after 3-4 axe cuts: the lower envelope of 3-4 tilted planes, each at its
own angle and steepness, so every facet is one true flat plane and no two points are alike. The round of the log
(diameter 100 units) runs up the side until it meets the cuts. OBJ is Y-up; the base sits at y = 0.
Winding and normals follow what the UE OBJ importer expects (see Scripts/test_obj_axes.py): written inward in OBJ space.
Run with any Python 3:  python -I make_hewn_tips.py
"""
import math
import os
import random

OUT = "C:/LETHE/SourceArt/Hewn"
RING = 48
RADII = 10
RAD = 50.0


def planes(r):
    n = r.choice((3, 3, 4, 4, 4))
    base = r.uniform(0, 2 * math.pi)
    apex = (r.uniform(-12, 12), r.uniform(-12, 12))
    height = r.uniform(85, 150)
    ps = []
    for i in range(n):
        a = base + 2 * math.pi * i / n + r.uniform(-0.35, 0.35)
        slope = height / (RAD * r.uniform(0.8, 1.25))      # how steep this axe stroke is
        ps.append((math.cos(a), math.sin(a), slope))
    return apex, height, ps


def surf(x, z, apex, height, ps):
    """Height of the hewn point above (x, z): the lowest of the cut planes."""
    return max(0.0, min(height - s * ((x - apex[0]) * c + (z - apex[1]) * d) for c, d, s in ps))


def tip(seed):
    r = random.Random(seed)
    apex, height, ps = planes(r)
    v, f = [], []

    def add(p):
        v.append(p)
        return len(v)

    ang = [2 * math.pi * i / RING for i in range(RING)]
    base_ring = [add((RAD * math.cos(a), 0.0, RAD * math.sin(a))) for a in ang]
    rings = []
    for k in range(RADII, 0, -1):                          # from the rim inward
        rr = RAD * k / RADII
        rings.append([add((rr * math.cos(a), surf(rr * math.cos(a), rr * math.sin(a), apex, height, ps), rr * math.sin(a)))
                      for a in ang])
    top = add((apex[0], height, apex[1]))
    for i in range(RING):                                  # the round of the log, up to the cuts
        j = (i + 1) % RING
        f.append((base_ring[i], base_ring[j], rings[0][j]))
        f.append((base_ring[i], rings[0][j], rings[0][i]))
    for k in range(len(rings) - 1):                        # the cut faces
        a_, b_ = rings[k], rings[k + 1]
        for i in range(RING):
            j = (i + 1) % RING
            f.append((a_[i], a_[j], b_[j]))
            f.append((a_[i], b_[j], b_[i]))
    for i in range(RING):
        f.append((rings[-1][i], rings[-1][(i + 1) % RING], top))
    return v, f


def write(path, data):
    v, f = data
    with open(path, "w", encoding="ascii", newline="\n") as fh:
        fh.write("# LETHE axe-hewn stake point\n")
        for p in v:
            fh.write("v %.3f %.3f %.3f\n" % p)
        for p in v:
            fh.write("vt %.4f %.4f\n" % (p[0] / 100 + 0.5, p[2] / 100 + 0.5))
        # one flat normal per face (each axe cut reads as a plane), along the written winding as in round 2
        for a, b, c in f:
            pa, pb, pc = v[a - 1], v[b - 1], v[c - 1]
            e1 = [pb[k] - pa[k] for k in range(3)]
            e2 = [pc[k] - pa[k] for k in range(3)]
            n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            ln = math.sqrt(sum(x * x for x in n)) or 1.0
            fh.write("vn %.4f %.4f %.4f\n" % (n[0] / ln, n[1] / ln, n[2] / ln))
        fh.write("s off\n")
        for i, (a, b, c) in enumerate(f):
            fh.write(FACE(a, b, c, i + 1))


# (a, b, c) above wind inward in OBJ (right-handed, Y-up) space. That is what renders outward after the
# importer's change of handedness (confirmed in the round 2 render), so they are written as they are.
def FACE(a, b, c, n):
    return "f %d/%d/%d %d/%d/%d %d/%d/%d\n" % (a, a, n, b, b, n, c, c, n)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for i in range(6):
        write("%s/HewnTip_%d.obj" % (OUT, i), tip(1590 + i * 17))
    print("wrote 6 hewn tips to " + OUT)
