"""
Writes the UV Lantern's beam profile: C:/LETHE/SourceArt/Light/UVLantern.ies (IES LM-63-2002, type C).
Vertical angle 0 = the beam axis. The edge wanders with azimuth (a hand torch, not a stage spot), one side is
a little brighter (the side Nysa holds it from), with a faint reflector ring inside the hot spot.
Run with any Python 3:  python -I make_uv_ies.py
"""
import math
import os
import random

OUT = "C:/LETHE/SourceArt/Light"
r = random.Random(1587)
V = [i * 0.5 for i in range(0, 121)]        # 0..60 deg
H = [i * 5.0 for i in range(0, 73)]         # 0..360 deg
lobes = [(k, r.uniform(0.4, 1.0) / k, r.uniform(0, 2 * math.pi)) for k in (2, 3, 5, 7, 11)]


def edge(h):
    a = math.radians(h)
    n = sum(amp * math.sin(k * a + ph) for k, amp, ph in lobes)
    return 13.0 + 2.2 * n                    # degrees, about 11-15


def cd(v, h):
    e = edge(h)
    soft = 5.0
    t = min(1.0, max(0.0, (v - (e - soft)) / (2 * soft)))
    fall = 1.0 - t * t * (3 - 2 * t)          # smoothstep falloff
    core = 0.75 + 0.25 * math.exp(-(v / 6.0) ** 2)
    ring = 1.0 + 0.08 * math.exp(-((v - 5.0) / 1.2) ** 2)
    side = 1.0 + 0.22 * math.cos(math.radians(h - 180.0))
    spill = 0.03 * math.exp(-v / 18.0)        # a faint wide halo beyond the edge
    return 1000.0 * (fall * core * ring * side + spill)


os.makedirs(OUT, exist_ok=True)
lines = ["IESNA:LM-63-2002", "[TEST] LETHE", "[MANUFAC] LETHE", "[LUMINAIRE] UV Lantern, hand held", "TILT=NONE",
         "1 1000 1 %d %d 1 2 0.05 0.05 0.0" % (len(V), len(H)), "1.0 1.0 10"]


def chunk(vals):
    return [" ".join(vals[i:i + 10]) for i in range(0, len(vals), 10)]


lines += chunk(["%.1f" % v for v in V])
lines += chunk(["%.1f" % h for h in H])
for h in H:
    lines += chunk(["%.2f" % cd(v, h) for v in V])
open(OUT + "/UVLantern.ies", "w", encoding="ascii", newline="").write("\r\n".join(lines) + "\r\n")
print("wrote %s/UVLantern.ies" % OUT)
