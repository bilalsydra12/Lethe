"""
Tileable cloth textures for Nysa, generated from code (no downloads). Runs in Blender's Python (numpy + image saving):
  blender -b --factory-startup -P C:/LETHE/Scripts/make_fabric_textures.py
Writes SourceArt/Nysa/coat/: T_NysaWool_N.png (twill weave + fibre fuzz normal), T_NysaWool_D.png (mottled greys,
around 1.0 so the material tint sets the colour), T_NysaLeather_N.png (pebbled grain + creases), T_NysaLeather_D.png
(worn, lighter at the high points).
"""
import numpy as np
import bpy

OUT = "C:/LETHE/SourceArt/Nysa/coat/"
N = 1024
rng = np.random.default_rng(7)
y, x = np.mgrid[0:N, 0:N].astype(np.float32) / N


def tile_noise(scale, octaves=4, persist=0.5):
    """Tileable value noise via random fourier bands."""
    out = np.zeros((N, N), np.float32)
    amp = 1.0
    for o in range(octaves):
        f = scale * (2 ** o)
        for _ in range(6):
            kx, ky = rng.integers(-f, f + 1, 2)
            ph = rng.uniform(0, 2 * np.pi)
            out += amp * np.cos(2 * np.pi * (kx * x + ky * y) + ph)
        amp *= persist
    out -= out.min()
    return out / max(out.max(), 1e-6)


def normal_from_height(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def save(name, rgb, srgb=True):
    img = bpy.data.images.new(name, N, N, alpha=False, float_buffer=False)
    if not srgb:
        img.colorspace_settings.name = "Non-Color"
    px = np.dstack([np.clip(rgb, 0, 1), np.ones((N, N, 1), np.float32)])
    img.pixels.foreach_set(px[::-1].astype(np.float32).ravel())
    img.filepath_raw = OUT + name + ".png"
    img.file_format = "PNG"
    img.save()
    print("FABRIC wrote", name)


# ---------------- wool twill: 2/2 diagonal ribs, ~64 threads across the tile (tile = 40 cm in the coat UVs -> ~6 mm ribs,
# coarse heavy wool), yarn wobble, fibre fuzz
T = 64
warp = np.sin(2 * np.pi * T * x + 0.6 * np.sin(2 * np.pi * 3 * y)) * 0.5 + 0.5
weft = np.sin(2 * np.pi * T * y) * 0.5 + 0.5
diag = np.sin(2 * np.pi * T / 2 * (x + y) + 1.2 * tile_noise(4, 3)) * 0.5 + 0.5
fuzz = tile_noise(60, 3, 0.6)
h_w = 0.55 * diag + 0.2 * warp * weft + 0.25 * fuzz
save("T_NysaWool_N", normal_from_height(h_w, 12.0), srgb=False)
mott = tile_noise(3, 4, 0.55)
d_w = 0.85 + 0.22 * mott + 0.035 * (diag - 0.5) + 0.06 * (fuzz - 0.5)
save("T_NysaWool_D", np.dstack([d_w] * 3))

# ---------------- leather: pebble grain (cellular-ish via abs noise) + a few long creases
cells = np.abs(tile_noise(40, 3, 0.6) - 0.5) * 2
cells = 1 - cells ** 0.6
creases = np.exp(-((tile_noise(2, 3, 0.5) - 0.5) * 30) ** 2)
h_l = 0.7 * cells - 0.5 * creases + 0.15 * tile_noise(90, 2)
save("T_NysaLeather_N", normal_from_height(h_l, 14.0), srgb=False)
wear = tile_noise(5, 4, 0.55)
d_l = 0.75 + 0.35 * wear + 0.15 * (cells - 0.5) + 0.25 * creases
save("T_NysaLeather_D", np.dstack([d_l] * 3))
