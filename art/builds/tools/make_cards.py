"""
Writes two flat cards for silhouettes and sky layers (OBJ, read by UE as X -> X, Y -> -Y, Z -> Z):
  C:/LETHE/SourceArt/Cards/Card_Base.obj    100 wide x 200 tall, standing on its base (trees)
  C:/LETHE/SourceArt/Cards/Card_Center.obj  100 x 100, centred (cloud layer)
Both lie in the UE local Y-Z plane facing local +X; texture v = 0 at the top. Used with two-sided materials.
Run with any Python 3:  python -I make_cards.py
"""
import os

OUT = "C:/LETHE/SourceArt/Cards"


def card(path, z0, z1, w):
    # UE-local corners (x, y, z) -> OBJ (x, -y, z); uv u left-to-right as seen from +X, v from the top
    corners = [(-w / 2, z0), (w / 2, z0), (w / 2, z1), (-w / 2, z1)]
    with open(path, "w", encoding="ascii", newline="\n") as f:
        for (y, z) in corners:
            f.write("v 0 %.3f %.3f\n" % (-y, z))
        for (y, z) in corners:
            # seen from +X, local -Y is on the viewer's right
            f.write("vt %.4f %.4f\n" % (1.0 - (y + w / 2) / w, (z1 - z) / (z1 - z0)))
        f.write("f 1/1 2/2 3/3\nf 1/1 3/3 4/4\n")


os.makedirs(OUT, exist_ok=True)
card(OUT + "/Card_Base.obj", 0.0, 200.0, 100.0)
card(OUT + "/Card_Center.obj", -50.0, 50.0, 100.0)
print("cards written to " + OUT)
