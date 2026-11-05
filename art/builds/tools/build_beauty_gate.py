"""
LETHE Â· Roanoke beauty corner: the CROATOAN gate at final quality (target: art/levels/roanoke/croatoan-gate.jpg).

Free Quixel Megascans from Fab (Standard License, $0 for Unreal), downloaded to C:/LETHE/SourceArt/Megascans:
  Old Wooden Log x2 (palisade trunks, gateposts; pale variant = the stripped CROATOAN post), Old Wooden Beam (rails),
  Soil Mud (ground), Wild Grass (8 clumps), Military Trenches Ground Mud (decal).
The inscription is our own texture (SourceArt/Carving): CROATOAN in Roman capitals, with later names scratched around it.

Builds /Game/Lethe/Maps/L_Beauty_CroatoanGate, then renders cinematic stills to C:/LETHE/Saved/Screenshots/Beauty and quits.
Run: launch the editor with env LETHE_AUTORUN=C:/LETHE/Scripts/build_beauty_gate.py
Env LETHE_BEAUTY_NOSHOOT=1 builds without rendering.  World: +X away from camera (toward the wall), +Y right, cm.
"""

import math
import os
import json
import random
import time
import unreal

ROOT = "/Game/Lethe/Beauty"
MAP = "/Game/Lethe/Maps/L_Beauty_CroatoanGate"
SRC = "C:/LETHE/SourceArt"
OUT = "C:/LETHE/Saved/Screenshots/Beauty"
TAG = "LetheBeauty"
rng = random.Random(1590)

assets = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
CONE = unreal.load_asset("/Engine/BasicShapes/Cone.Cone")
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane.Plane")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")


def log(msg):
    unreal.log("LETHE beauty: " + msg)


def safe_set(obj, name, value):
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception as e:  # noqa: BLE001
        unreal.log_warning("LETHE beauty: could not set %s: %s" % (name, e))
        return False


# ------------------------------------------------------------------ import

def import_file(path, dest):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", path)
    t.set_editor_property("destination_path", dest)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", True)
    t.set_editor_property("replace_existing", True)
    assets.import_asset_tasks([t])
    objs = [unreal.load_asset(p) for p in t.get_editor_property("imported_object_paths")]
    return [o for o in objs if o]


def tex(folder, filename, kind):
    """kind: color | normal | linear"""
    name = os.path.splitext(filename)[0]
    dest = ROOT + "/Textures"
    existing = dest + "/" + name
    if eal.does_asset_exist(existing):
        t = unreal.load_asset(existing)
    else:
        objs = import_file(SRC + "/" + folder + "/" + filename, dest)
        t = next((o for o in objs if isinstance(o, unreal.Texture2D)), None)
        if t is None:
            raise RuntimeError("texture import failed: " + filename)
    if kind == "normal":
        safe_set(t, "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        safe_set(t, "srgb", False)
    elif kind == "linear":
        safe_set(t, "compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        safe_set(t, "srgb", False)
    else:
        safe_set(t, "srgb", True)
    eal.save_loaded_asset(t)
    return t


def mesh(folder, filename, name):
    dest = ROOT + "/Meshes/" + name
    found = [a for a in (eal.list_assets(dest, recursive=True) if eal.does_directory_exist(dest) else [])]
    for p in found:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            return a
    objs = import_file(SRC + "/Megascans/" + folder + "/" + filename, dest)
    sm = next((o for o in objs if isinstance(o, unreal.StaticMesh)), None)
    if sm is None:
        for p in eal.list_assets(dest, recursive=True):
            a = unreal.load_asset(p)
            if isinstance(a, unreal.StaticMesh):
                sm = a
    if sm is None:
        raise RuntimeError("mesh import failed: " + filename)
    return sm


# ------------------------------------------------------------------ materials

def new_material(name):
    path = ROOT + "/Materials/" + name
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    return assets.create_asset(name, ROOT + "/Materials", unreal.Material, unreal.MaterialFactoryNew())


def E(m, cls, x, y, **props):
    e = mel.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        safe_set(e, k, v)
    return e


def link(a, a_out, b, b_in):
    if not mel.connect_material_expressions(a, a_out, b, b_in):
        unreal.log_warning("LETHE beauty: link failed %s.%s -> %s" % (a.get_name(), b_in, b.get_name()))


def to_prop(e, out, prop):
    mel.connect_material_property(e, out, prop)


def tparam(m, name, texture, sampler, x, y, uv=None):
    e = E(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y,
          parameter_name=name, texture=texture, sampler_type=sampler)
    if uv is not None:
        link(uv, "", e, "UVs")
    return e


def sparam(m, name, v, x, y):
    return E(m, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=v)


def vparam(m, name, rgb, x, y):
    return E(m, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
             default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))


def mul(m, a, b, x, y, a_out="", b_out=""):
    e = E(m, unreal.MaterialExpressionMultiply, x, y)
    link(a, a_out, e, "A")
    link(b, b_out, e, "B")
    return e


def lerp(m, a, b, alpha, x, y, a_out="", b_out="", al_out=""):
    e = E(m, unreal.MaterialExpressionLinearInterpolate, x, y)
    link(a, a_out, e, "A")
    link(b, b_out, e, "B")
    link(alpha, al_out, e, "Alpha")
    return e


SC = unreal.MaterialSamplerType
MP = unreal.MaterialProperty


def m_surface(d):
    """Scanned surface: colour, normal, roughness, AO. Tint, Pale (stripped wood) and Wet controls."""
    m = new_material("M_LetheScan")
    uv = mul(m, E(m, unreal.MaterialExpressionTextureCoordinate, -1600, 0), sparam(m, "UVScale", 1.0, -1600, 120), -1400, 0)
    bc = tparam(m, "BaseColor", d["bc"], SC.SAMPLERTYPE_COLOR, -1200, -300, uv)
    nm = tparam(m, "Normal", d["n"], SC.SAMPLERTYPE_NORMAL, -1200, 0, uv)
    ro = tparam(m, "Roughness", d["r"], SC.SAMPLERTYPE_MASKS, -1200, 250, uv)
    ao = tparam(m, "AO", d["ao"], SC.SAMPLERTYPE_MASKS, -1200, 500, uv)
    tinted = mul(m, bc, vparam(m, "Tint", (1, 1, 1), -900, -420), -800, -300, "RGB")
    # Pale: the bark taken off â€” luminance of the scan, lifted toward bare pale wood
    lum = E(m, unreal.MaterialExpressionDotProduct, -800, -150)
    link(tinted, "", lum, "A")
    link(E(m, unreal.MaterialExpressionConstant3Vector, -1000, -150, constant=unreal.LinearColor(0.3, 0.59, 0.11, 1)), "", lum, "B")
    lum_c = E(m, unreal.MaterialExpressionPower, -720, -200)       # PaleContrast > 1: pale wood, darker grain and cracks
    link(lum, "", lum_c, "Base")
    link(sparam(m, "PaleContrast", 1.0, -900, -230), "", lum_c, "Exp")
    pale_col = mul(m, mul(m, lum_c, vparam(m, "PaleColor", (0.86, 0.70, 0.50), -800, -60), -650, -150), sparam(m, "PaleBright", 2.4, -650, -60), -500, -150)
    base = lerp(m, tinted, pale_col, sparam(m, "Pale", 0.0, -500, -40), -350, -300)
    wet = sparam(m, "Wet", 0.35, -500, 120)
    darken = lerp(m, E(m, unreal.MaterialExpressionConstant, -350, 60, r=1.0), E(m, unreal.MaterialExpressionConstant, -350, 110, r=0.55), wet, -200, 60)
    to_prop(mul(m, base, darken, -100, -300), "", MP.MP_BASE_COLOR)
    rough = mul(m, ro, sparam(m, "RoughnessMult", 1.0, -900, 300), -800, 250, "R")
    rough_w = lerp(m, rough, mul(m, rough, E(m, unreal.MaterialExpressionConstant, -800, 400, r=0.45), -650, 380), wet, -400, 250)
    to_prop(rough_w, "", MP.MP_ROUGHNESS)
    to_prop(nm, "RGB", MP.MP_NORMAL)
    to_prop(ao, "R", MP.MP_AMBIENT_OCCLUSION)
    mel.recompile_material(m)
    return m


def m_ground(d):
    """Wet mud with puddles in the low spots. A second, much larger sample of the scan (at a non-repeating scale)
    moves the water line and the colour about, so the puddles do not repeat in a grid."""
    m = new_material("M_LetheMud")
    uv = mul(m, E(m, unreal.MaterialExpressionTextureCoordinate, -1800, 0), sparam(m, "UVScale", 16.0, -1800, 120), -1600, 0)
    uvm = mul(m, uv, E(m, unreal.MaterialExpressionConstant, -1800, 260, r=0.0917), -1600, 260)
    bc = tparam(m, "BaseColor", d["bc"], SC.SAMPLERTYPE_COLOR, -1200, -300, uv)
    nm = tparam(m, "Normal", d["n"], SC.SAMPLERTYPE_NORMAL, -1200, 0, uv)
    ro = tparam(m, "Roughness", d["r"], SC.SAMPLERTYPE_MASKS, -1200, 250, uv)
    ds = tparam(m, "Height", d["h"], SC.SAMPLERTYPE_MASKS, -1200, 500, uv)
    macro = tparam(m, "Height", d["h"], SC.SAMPLERTYPE_MASKS, -1200, 760, uvm)
    mc = E(m, unreal.MaterialExpressionSubtract, -1000, 760, const_b=0.5)
    link(macro, "R", mc, "A")
    lvl = E(m, unreal.MaterialExpressionAdd, -850, 650)
    link(sparam(m, "PuddleLevel", 0.38, -1000, 620), "", lvl, "A")
    link(mul(m, mc, sparam(m, "MacroAmp", 0.5, -1000, 880), -900, 800), "", lvl, "B")
    sub = E(m, unreal.MaterialExpressionSubtract, -750, 500)
    link(lvl, "", sub, "A")
    link(ds, "R", sub, "B")
    pud = E(m, unreal.MaterialExpressionSaturate, -500, 500)
    link(mul(m, sub, sparam(m, "PuddleSharpness", 14.0, -750, 650), -650, 500), "", pud, "")
    wetbase = mul(m, bc, sparam(m, "WetDarken", 0.55, -1000, -420), -900, -300, "RGB")
    patch = lerp(m, E(m, unreal.MaterialExpressionConstant, -900, -500, r=0.7), E(m, unreal.MaterialExpressionConstant, -900, -560, r=1.3),
                 macro, -750, -500, "", "", "R")
    wetbase = mul(m, wetbase, patch, -700, -380)
    base = lerp(m, wetbase, mul(m, wetbase, E(m, unreal.MaterialExpressionConstant, -700, -150, r=0.22), -600, -200), pud, -400, -300)
    ds_ = E(m, unreal.MaterialExpressionDesaturation, -250, -300)
    link(base, "", ds_, "")
    link(sparam(m, "Desat", 0.0, -400, -420), "", ds_, "Fraction")
    to_prop(mul(m, ds_, vparam(m, "MudTint", (1.0, 1.0, 1.0), -250, -420), -120, -300), "", MP.MP_BASE_COLOR)
    r = mul(m, ro, sparam(m, "RoughnessMult", 0.7, -1000, 300), -900, 250, "R")
    to_prop(lerp(m, r, E(m, unreal.MaterialExpressionConstant, -700, 380, r=0.03), pud, -400, 250), "", MP.MP_ROUGHNESS)
    flat = E(m, unreal.MaterialExpressionConstant3Vector, -900, 120, constant=unreal.LinearColor(0, 0, 1, 1))
    to_prop(lerp(m, nm, flat, pud, -400, 0, "RGB"), "", MP.MP_NORMAL)
    mel.recompile_material(m)
    return m


def m_puddle(name, h):
    """A standing puddle (deferred decal): near-black mirror water with a ragged edge."""
    m = new_material(name)
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    tc = E(m, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
    dist = E(m, unreal.MaterialExpressionDistance, -1000, 0)
    link(tc, "", dist, "A")
    link(E(m, unreal.MaterialExpressionConstant2Vector, -1200, 100, r=0.5, g=0.5), "", dist, "B")
    rad = E(m, unreal.MaterialExpressionSubtract, -850, 0, const_a=0.5)
    link(dist, "", rad, "B")
    hs = tparam(m, "Height", h, SC.SAMPLERTYPE_MASKS, -1000, 250, mul(m, tc, E(m, unreal.MaterialExpressionConstant, -1200, 300, r=1.7), -1100, 250))
    edge = E(m, unreal.MaterialExpressionSubtract, -700, 100)
    link(mul(m, rad, E(m, unreal.MaterialExpressionConstant, -850, 120, r=7.0), -800, 0), "", edge, "A")
    link(hs, "R", edge, "B")
    op = E(m, unreal.MaterialExpressionSaturate, -550, 100)
    link(mul(m, edge, E(m, unreal.MaterialExpressionConstant, -700, 200, r=3.0), -650, 100), "", op, "")
    to_prop(op, "", MP.MP_OPACITY)
    to_prop(E(m, unreal.MaterialExpressionConstant3Vector, -500, -200, constant=unreal.LinearColor(0.030, 0.031, 0.036, 1)), "", MP.MP_BASE_COLOR)
    to_prop(E(m, unreal.MaterialExpressionConstant, -500, -100, r=0.10), "", MP.MP_ROUGHNESS)
    to_prop(E(m, unreal.MaterialExpressionConstant3Vector, -500, 0, constant=unreal.LinearColor(0, 0, 1, 1)), "", MP.MP_NORMAL)
    mel.recompile_material(m)
    return m


def m_foliage(d):
    m = new_material("M_LetheGrass")
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    safe_set(m, "shading_model", unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    bc = tparam(m, "BaseColor", d["bc"], SC.SAMPLERTYPE_COLOR, -1000, -300)
    op = tparam(m, "Opacity", d["op"], SC.SAMPLERTYPE_MASKS, -1000, -50)
    nm = tparam(m, "Normal", d["n"], SC.SAMPLERTYPE_NORMAL, -1000, 200)
    tr = tparam(m, "Translucency", d["tr"], SC.SAMPLERTYPE_COLOR, -1000, 450)
    # Night grass: darker, a little desaturated toward olive-grey
    to_prop(mul(m, bc, vparam(m, "Tint", (0.55, 0.58, 0.5), -800, -400), -600, -300, "RGB"), "", MP.MP_BASE_COLOR)
    to_prop(op, "R", MP.MP_OPACITY_MASK)
    to_prop(nm, "RGB", MP.MP_NORMAL)
    to_prop(E(m, unreal.MaterialExpressionConstant, -600, 100, r=0.55), "", MP.MP_ROUGHNESS)
    to_prop(mul(m, tr, E(m, unreal.MaterialExpressionConstant, -800, 600, r=0.35), -600, 450, "RGB"), "", MP.MP_SUBSURFACE_COLOR)
    mel.recompile_material(m)
    return m


def m_decal(name, d, carving=False):
    m = new_material(name)
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    if carving:
        # Mask: R = depth of the knife cut, G = the stripped-bark panel (pale weathered wood).
        mask = tparam(m, "Mask", d["mask"], SC.SAMPLERTYPE_MASKS, -1000, 0)
        # Decal UVs span 100 x 400 cm; scale V four times as much so the grain is not stretched.
        guv0 = mul(m, E(m, unreal.MaterialExpressionTextureCoordinate, -1800, -400),
                   E(m, unreal.MaterialExpressionConstant2Vector, -1800, -320, r=0.32, g=0.92), -1650, -400)
        guv = E(m, unreal.MaterialExpressionAdd, -1500, -400)
        link(guv0, "", guv, "A")
        link(E(m, unreal.MaterialExpressionConstant2Vector, -1650, -320, r=0.06, g=0.04), "", guv, "B")
        grain = tparam(m, "Grain", d["grain"], SC.SAMPLERTYPE_COLOR, -1300, -400, guv)
        lum = E(m, unreal.MaterialExpressionDotProduct, -1100, -500)
        link(grain, "RGB", lum, "A")
        link(E(m, unreal.MaterialExpressionConstant3Vector, -1300, -560, constant=unreal.LinearColor(0.3, 0.59, 0.11, 1)), "", lum, "B")
        pale = mul(m, mul(m, lum, vparam(m, "PaleColor", (0.80, 0.77, 0.72), -1100, -640), -950, -560),
                   sparam(m, "PaleBright", 1.9, -950, -660), -800, -560)
        cut_col = mul(m, grain, vparam(m, "CutColor", (0.16, 0.11, 0.08), -1100, -250), -950, -300, "RGB")
        cut_a = E(m, unreal.MaterialExpressionSaturate, -700, 0)
        link(mul(m, mask, sparam(m, "Depth", 2.6, -900, 120), -800, 0, "R"), "", cut_a, "")
        carved = lerp(m, pale, cut_col, cut_a, -550, -400)
        # B = the torn bark rim round the panel: dark red-brown bark section, catching less light
        rim_col = mul(m, grain, vparam(m, "RimColor", (0.11, 0.07, 0.05), -1100, -150), -950, -150, "RGB")
        to_prop(lerp(m, carved, rim_col, mask, -400, -400, "", "", "B"), "", MP.MP_BASE_COLOR)
        to_prop(E(m, unreal.MaterialExpressionConstant, -700, -100, r=0.82), "", MP.MP_ROUGHNESS)
        op0 = E(m, unreal.MaterialExpressionMax, -600, 0)
        link(mask, "G", op0, "A")
        link(cut_a, "", op0, "B")
        op = E(m, unreal.MaterialExpressionMax, -500, 0)
        link(op0, "", op, "A")
        link(mask, "B", op, "B")
        to_prop(op, "", MP.MP_OPACITY)
        # Deep cut: a normal derived from the mask's slope, so the groove walls catch the light.
        uv0 = E(m, unreal.MaterialExpressionTextureCoordinate, -1600, 600)
        def shifted(du, dv, y):
            add = E(m, unreal.MaterialExpressionAdd, -1400, y)
            link(uv0, "", add, "A")
            link(E(m, unreal.MaterialExpressionConstant2Vector, -1600, y + 60, r=du, g=dv), "", add, "B")
            return tparam(m, "Mask", d["mask"], SC.SAMPLERTYPE_MASKS, -1200, y, add)
        m0 = tparam(m, "Mask", d["mask"], SC.SAMPLERTYPE_MASKS, -1200, 600, uv0)
        mx = shifted(1.0 / 2048, 0.0, 760)
        my = shifted(0.0, 1.0 / 8192, 920)
        # depth = cut (R) + the step up onto the bark at the panel edge (B)
        wts = E(m, unreal.MaterialExpressionConstant3Vector, -1100, 1100, constant=unreal.LinearColor(1.0, 0.0, 0.7, 1))
        def depth(s, y):
            d_ = E(m, unreal.MaterialExpressionDotProduct, -1050, y)
            link(s, "RGB", d_, "A")
            link(wts, "", d_, "B")
            return d_
        h0, hx, hy = depth(m0, 600), depth(mx, 760), depth(my, 920)
        dx = E(m, unreal.MaterialExpressionSubtract, -950, 700)
        link(hx, "", dx, "A")
        link(h0, "", dx, "B")
        dy = E(m, unreal.MaterialExpressionSubtract, -950, 850)
        link(hy, "", dy, "A")
        link(h0, "", dy, "B")
        k = sparam(m, "CutDepth", 6.0, -950, 1000)
        nx = mul(m, dx, k, -800, 700)
        ny = mul(m, dy, k, -800, 850)
        xy = E(m, unreal.MaterialExpressionAppendVector, -650, 760)
        link(nx, "", xy, "A")
        link(ny, "", xy, "B")
        xyz = E(m, unreal.MaterialExpressionAppendVector, -500, 760)
        link(xy, "", xyz, "A")
        link(E(m, unreal.MaterialExpressionConstant, -650, 900, r=1.0), "", xyz, "B")
        nrm = E(m, unreal.MaterialExpressionNormalize, -350, 760)
        link(xyz, "", nrm, "VectorInput")
        to_prop(nrm, "", MP.MP_NORMAL)
        # Under the UV lantern the cuts fluoresce faintly violet (the Lantern reveals what was carved).
        to_prop(mul(m, mul(m, mask, vparam(m, "UVGlow", (0.30, 0.12, 0.85), -800, 300), -600, 300, "R"),
                    sparam(m, "UVStrength", 0.0, -600, 420), -400, 300), "", MP.MP_EMISSIVE_COLOR)
    else:
        bc = tparam(m, "BaseColor", d["bc"], SC.SAMPLERTYPE_COLOR, -1000, -300)
        op = tparam(m, "Opacity", d["op"], SC.SAMPLERTYPE_MASKS, -1000, -50)
        nm = tparam(m, "Normal", d["n"], SC.SAMPLERTYPE_NORMAL, -1000, 200)
        to_prop(mul(m, bc, E(m, unreal.MaterialExpressionConstant, -800, -400, r=0.5), -600, -300, "RGB"), "", MP.MP_BASE_COLOR)
        to_prop(op, "R", MP.MP_OPACITY)
        to_prop(nm, "RGB", MP.MP_NORMAL)
        to_prop(E(m, unreal.MaterialExpressionConstant, -600, 100, r=0.12), "", MP.MP_ROUGHNESS)
    mel.recompile_material(m)
    return m


def m_pine(name, tx):
    """A distant pine: a two-sided masked silhouette, near-black, so the fog alone gives it depth."""
    m = new_material(name)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    t = tparam(m, "Silhouette", tx, SC.SAMPLERTYPE_COLOR, -800, 0)
    to_prop(E(m, unreal.MaterialExpressionConstant3Vector, -500, -200, constant=unreal.LinearColor(0.012, 0.014, 0.016, 1)), "", MP.MP_BASE_COLOR)
    # cut out by darkness: the tree is near-black, the empty card is white (robust even if the alpha is lost on import)
    om = E(m, unreal.MaterialExpressionOneMinus, -500, 0)
    link(t, "R", om, "")
    to_prop(om, "", MP.MP_OPACITY_MASK)
    to_prop(E(m, unreal.MaterialExpressionConstant, -500, 100, r=0.95), "", MP.MP_ROUGHNESS)
    mel.recompile_material(m)
    return m


def moon_glow(m, moon, radius, x, y):
    """saturate(1 - |world position - moon| / radius)^2, the soft halo round the moon."""
    wp = E(m, unreal.MaterialExpressionWorldPosition, x - 600, y)
    d = E(m, unreal.MaterialExpressionDistance, x - 400, y)
    link(wp, "", d, "A")
    link(E(m, unreal.MaterialExpressionConstant3Vector, x - 600, y + 80, constant=unreal.LinearColor(moon[0], moon[1], moon[2], 1)), "", d, "B")
    f = E(m, unreal.MaterialExpressionSubtract, x - 200, y, const_a=1.0)
    link(mul(m, d, E(m, unreal.MaterialExpressionConstant, x - 400, y + 120, r=1.0 / radius), x - 300, y), "", f, "B")
    s = E(m, unreal.MaterialExpressionSaturate, x - 100, y)
    link(f, "", s, "")
    return mul(m, s, s, x, y)


def m_night_sky(name, moon):
    """Night sky: cold blue-grey, brighter toward the moon."""
    m = new_material(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    g1 = moon_glow(m, moon, 9000.0, -300, 200)
    g2 = moon_glow(m, moon, 2600.0, -300, 500)
    base = E(m, unreal.MaterialExpressionConstant3Vector, -300, -200, constant=unreal.LinearColor(0.070, 0.085, 0.112, 1))
    add1 = E(m, unreal.MaterialExpressionAdd, -100, 0)
    link(base, "", add1, "A")
    link(mul(m, g1, E(m, unreal.MaterialExpressionConstant3Vector, -300, 350, constant=unreal.LinearColor(0.10, 0.11, 0.14, 1)), -150, 250), "", add1, "B")
    add2 = E(m, unreal.MaterialExpressionAdd, 0, 100)
    link(add1, "", add2, "A")
    link(mul(m, g2, E(m, unreal.MaterialExpressionConstant3Vector, -300, 650, constant=unreal.LinearColor(0.45, 0.48, 0.55, 1)), -150, 550), "", add2, "B")
    to_prop(add2, "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    return m


def m_cloud(name, moon):
    """A thin layer of night cloud drifting across the moon: noise opacity, edges lit silver near the moon."""
    m = new_material(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("two_sided", True)
    n1 = E(m, unreal.MaterialExpressionNoise, -700, 0, scale=0.00045, levels=6, output_min=-1.0, output_max=1.0, quality=2)
    n2 = E(m, unreal.MaterialExpressionNoise, -700, 200, scale=0.0016, levels=4, output_min=-0.3, output_max=0.3, quality=2)
    n = E(m, unreal.MaterialExpressionAdd, -500, 100)
    link(n1, "", n, "A")
    link(n2, "", n, "B")
    op = E(m, unreal.MaterialExpressionSaturate, -300, 100)
    thin = E(m, unreal.MaterialExpressionSubtract, -450, 100, const_b=0.25)    # gaps between the clouds
    link(n, "", thin, "A")
    link(thin, "", op, "")
    to_prop(mul(m, op, E(m, unreal.MaterialExpressionConstant, -300, 250, r=0.55), -200, 100), "", MP.MP_OPACITY)
    g = moon_glow(m, moon, 3200.0, -300, 500)
    col = E(m, unreal.MaterialExpressionAdd, -100, 300)
    link(E(m, unreal.MaterialExpressionConstant3Vector, -300, 350, constant=unreal.LinearColor(0.030, 0.036, 0.048, 1)), "", col, "A")
    link(mul(m, g, E(m, unreal.MaterialExpressionConstant3Vector, -300, 650, constant=unreal.LinearColor(0.55, 0.58, 0.66, 1)), -150, 550), "", col, "B")
    to_prop(col, "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    return m


def m_hdri_sky(name, hdri, moon_dir, yaw_offset, bright):
    """A photographed night sky on a huge sphere round the camera: lat-long lookup of the HDRI by view direction,
    a dark fog colour below the horizon, and the moon (disc + halo) drawn where moon_dir points."""
    m = new_material(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    d = E(m, unreal.MaterialExpressionSubtract, -1800, 0)
    link(E(m, unreal.MaterialExpressionWorldPosition, -2000, 0), "", d, "A")
    link(E(m, unreal.MaterialExpressionCameraPositionWS, -2000, 100), "", d, "B")
    dirv = E(m, unreal.MaterialExpressionNormalize, -1650, 0)
    link(d, "", dirv, "VectorInput")

    def comp(r, g, b, y):
        c = E(m, unreal.MaterialExpressionComponentMask, -1500, y, r=r, g=g, b=b, a=False)
        link(dirv, "", c, "")
        return c
    dx, dy, dz = comp(True, False, False, -200), comp(False, True, False, -100), comp(False, False, True, 0)
    az = E(m, unreal.MaterialExpressionArctangent2, -1300, -150)
    link(dy, "", az, "Y")
    link(dx, "", az, "X")
    u = E(m, unreal.MaterialExpressionAdd, -1000, -150, const_b=0.5 + yaw_offset)
    link(mul(m, az, E(m, unreal.MaterialExpressionConstant, -1300, -50, r=-0.15915494), -1150, -150), "", u, "A")
    el = E(m, unreal.MaterialExpressionArccosine, -1300, 50)
    link(dz, "", el, "")
    v = mul(m, el, E(m, unreal.MaterialExpressionConstant, -1300, 150, r=0.31830989), -1150, 50)
    uv = E(m, unreal.MaterialExpressionAppendVector, -900, 0)
    link(u, "", uv, "A")
    link(v, "", uv, "B")
    s = E(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0, parameter_name="HDRI", texture=hdri)
    safe_set(s, "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    link(uv, "", s, "UVs")
    skyc = mul(m, s, sparam(m, "SkyBright", bright, -700, 200), -500, 0, "RGB")
    below = E(m, unreal.MaterialExpressionSaturate, -700, 350)
    link(mul(m, dz, E(m, unreal.MaterialExpressionConstant, -900, 400, r=25.0), -800, 350), "", below, "")
    sky = lerp(m, vparam(m, "Horizon", (0.030, 0.036, 0.048), -500, 300), skyc, below, -300, 0)
    # the moon: a crisp disc and a soft double halo
    md = E(m, unreal.MaterialExpressionDotProduct, -1100, 500)
    link(dirv, "", md, "A")
    link(E(m, unreal.MaterialExpressionConstant3Vector, -1300, 550, constant=unreal.LinearColor(moon_dir[0], moon_dir[1], moon_dir[2], 1)), "", md, "B")
    mds = E(m, unreal.MaterialExpressionSaturate, -950, 500)
    link(md, "", mds, "")
    disc0 = E(m, unreal.MaterialExpressionSubtract, -800, 500, const_b=0.99988)
    link(mds, "", disc0, "A")
    disc = E(m, unreal.MaterialExpressionSaturate, -600, 500)
    link(mul(m, disc0, E(m, unreal.MaterialExpressionConstant, -800, 600, r=9000.0), -700, 500), "", disc, "")
    h1 = E(m, unreal.MaterialExpressionPower, -800, 700, const_exponent=700.0)
    link(mds, "", h1, "Base")
    h2 = E(m, unreal.MaterialExpressionPower, -800, 800, const_exponent=45.0)
    link(mds, "", h2, "Base")
    glow = E(m, unreal.MaterialExpressionAdd, -500, 600)
    link(mul(m, disc, E(m, unreal.MaterialExpressionConstant, -700, 650, r=40.0), -600, 600), "", glow, "A")
    hal = E(m, unreal.MaterialExpressionAdd, -600, 750)
    link(mul(m, h1, E(m, unreal.MaterialExpressionConstant, -800, 760, r=1.6), -700, 720), "", hal, "A")
    link(mul(m, h2, E(m, unreal.MaterialExpressionConstant, -800, 860, r=0.22), -700, 820), "", hal, "B")
    link(hal, "", glow, "B")
    mc = mul(m, glow, vparam(m, "MoonColor", (0.85, 0.90, 1.0), -500, 800), -400, 650)
    out = E(m, unreal.MaterialExpressionAdd, -200, 300)
    link(sky, "", out, "A")
    link(mc, "", out, "B")
    to_prop(out, "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    return m


def m_glass(name, rgb, strength, opacity):
    """Lantern glass: translucent and softly self-lit, so the flame inside shows through."""
    m = new_material(name)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    to_prop(vparam(m, "Color", (rgb[0] * strength, rgb[1] * strength, rgb[2] * strength), -400, 0), "", MP.MP_EMISSIVE_COLOR)
    to_prop(E(m, unreal.MaterialExpressionConstant, -400, 120, r=opacity), "", MP.MP_OPACITY)
    mel.recompile_material(m)
    return m


def import_parts(path, dest):
    """Imports every static mesh in an FBX (frame, glass, door...) into dest; returns them."""
    if not eal.does_directory_exist(dest) or not [p for p in eal.list_assets(dest, recursive=True)]:
        import_file(path, dest)
    out = []
    for p in eal.list_assets(dest, recursive=True):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            ns = a.get_editor_property("nanite_settings")         # translucent glass cannot draw through Nanite
            if ns.get_editor_property("enabled"):
                ns.set_editor_property("enabled", False)
                a.set_editor_property("nanite_settings", ns)
                eal.save_loaded_asset(a)
            out.append(a)
    return out


def m_unlit(name, rgb, strength):
    m = new_material(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    to_prop(vparam(m, "Color", (rgb[0] * strength, rgb[1] * strength, rgb[2] * strength), -400, 0), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    return m


def m_beam(name, rgb, strength):
    """A torch beam's visible shaft: unlit, additive, soft at the silhouette, fading with distance from the lamp."""
    m = new_material(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    fr = E(m, unreal.MaterialExpressionFresnel, -900, 100)
    safe_set(fr, "exponent", 1.2)
    soft = E(m, unreal.MaterialExpressionOneMinus, -750, 100)
    link(fr, "", soft, "")
    soft2 = mul(m, soft, soft, -620, 100)
    wp = E(m, unreal.MaterialExpressionWorldPosition, -1100, 300)
    d = E(m, unreal.MaterialExpressionDistance, -900, 300)
    link(wp, "", d, "A")
    link(vparam(m, "LampPos", (0.0, 0.0, 0.0), -1100, 400), "", d, "B")
    dv = E(m, unreal.MaterialExpressionDivide, -750, 300)
    link(d, "", dv, "A")
    link(sparam(m, "Length", 50.0, -900, 420), "", dv, "B")
    fade = E(m, unreal.MaterialExpressionOneMinus, -620, 300)
    link(dv, "", fade, "")
    fs = E(m, unreal.MaterialExpressionSaturate, -500, 300)
    link(fade, "", fs, "")
    k = mul(m, soft2, fs, -350, 200)
    to_prop(mul(m, vparam(m, "Color", (rgb[0] * strength, rgb[1] * strength, rgb[2] * strength), -400, 0), k, -200, 50), "", MP.MP_EMISSIVE_COLOR)
    mel.recompile_material(m)
    return m


def m_curlcard(name, tex_, tint):
    """Hair cards: the ringlet texture's alpha cuts the curls out; two-sided, a little sheen."""
    m = new_material(name)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", True)
    safe_set(m, "opacity_mask_clip_value", 0.4)
    t_ = E(m, unreal.MaterialExpressionTextureSample, -900, 0)
    t_.set_editor_property("texture", tex_)
    to_prop(mul(m, t_, vparam(m, "Tint", tint, -700, -150), -500, -50, "RGB"), "", MP.MP_BASE_COLOR)
    to_prop(t_, "A", MP.MP_OPACITY_MASK)
    to_prop(E(m, unreal.MaterialExpressionConstant, -400, 200, r=0.42), "", MP.MP_ROUGHNESS)
    to_prop(E(m, unreal.MaterialExpressionConstant, -400, 300, r=0.45), "", MP.MP_SPECULAR)
    mel.recompile_material(m)
    return m


def m_char(name, bc_t, n_t, orm_t, tint, rough_mult=1.0):
    """A character surface from a glTF texture set: base colour x tint, normal, ORM (AO in R, roughness in G)."""
    m = new_material(name)
    bc = E(m, unreal.MaterialExpressionTextureSample, -900, -200); bc.set_editor_property("texture", bc_t)
    nm = E(m, unreal.MaterialExpressionTextureSample, -900, 100); nm.set_editor_property("texture", n_t)
    nm.set_editor_property("sampler_type", SC.SAMPLERTYPE_NORMAL)
    orm = E(m, unreal.MaterialExpressionTextureSample, -900, 400); orm.set_editor_property("texture", orm_t)
    orm.set_editor_property("sampler_type", SC.SAMPLERTYPE_MASKS)
    to_prop(mul(m, bc, vparam(m, "Tint", tint, -700, -300), -500, -200, "RGB"), "", MP.MP_BASE_COLOR)
    to_prop(nm, "RGB", MP.MP_NORMAL)
    to_prop(mul(m, orm, E(m, unreal.MaterialExpressionConstant, -700, 500, r=rough_mult), -500, 400, "G"), "", MP.MP_ROUGHNESS)
    to_prop(orm, "R", MP.MP_AMBIENT_OCCLUSION)
    m.set_editor_property("two_sided", True)
    mel.recompile_material(m)
    return m


def m_hair_strands(name, rgb, rough=0.42, spec=0.35):
    """Strand hair (groom): the Hair shading model, dark brown, a soft highlight."""
    m = new_material(name)
    safe_set(m, "shading_model", unreal.MaterialShadingModel.MSM_HAIR)
    safe_set(m, "used_with_hair_strands", True)
    to_prop(vparam(m, "Tint", rgb, -600, -200), "", MP.MP_BASE_COLOR)
    to_prop(E(m, unreal.MaterialExpressionConstant, -400, 200, r=rough), "", MP.MP_ROUGHNESS)
    to_prop(E(m, unreal.MaterialExpressionConstant, -400, 300, r=spec), "", MP.MP_SPECULAR)
    mel.recompile_material(m)
    return m


def m_cloth(name, rgb, rough, tex=None, sheen=0.0):
    """Matte cloth or hair: base colour (optionally a texture multiplied by rgb), roughness; usable on skeletal meshes."""
    m = new_material(name)
    safe_set(m, "used_with_skeletal_mesh", True)
    col = vparam(m, "Tint", rgb, -600, -200)
    if tex is not None:
        t_ = E(m, unreal.MaterialExpressionTextureSample, -900, 0)
        t_.set_editor_property("texture", tex)
        uvs = mul(m, E(m, unreal.MaterialExpressionTextureCoordinate, -1300, 0), E(m, unreal.MaterialExpressionConstant, -1300, 120, r=4.0), -1100, 0)
        link(uvs, "", t_, "UVs")
        col = mul(m, t_, col, -400, -100, "RGB")
    to_prop(col, "", MP.MP_BASE_COLOR)
    to_prop(E(m, unreal.MaterialExpressionConstant, -400, 200, r=rough), "", MP.MP_ROUGHNESS)
    to_prop(E(m, unreal.MaterialExpressionConstant, -400, 300, r=sheen), "", MP.MP_SPECULAR)
    mel.recompile_material(m)
    return m


def mi(name, parent, scalars=None, vectors=None, textures=None):
    path = ROOT + "/Materials/" + name
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    inst = assets.create_asset(name, ROOT + "/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    inst.set_editor_property("parent", parent)
    for k, v in (scalars or {}).items():
        mel.set_material_instance_scalar_parameter_value(inst, k, v)
    for k, v in (vectors or {}).items():
        mel.set_material_instance_vector_parameter_value(inst, k, unreal.LinearColor(v[0], v[1], v[2], 1))
    for k, v in (textures or {}).items():
        mel.set_material_instance_texture_parameter_value(inst, k, v)
    eal.save_loaded_asset(inst)
    return inst


# ------------------------------------------------------------------ placement

def tag(a, label, folder):
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.tags = list(a.tags) + [TAG]
    return a


def V(x, y, z):
    return unreal.Vector(x, y, z)


INFO = {}
TIPS = []          # hewn stake-point meshes
HEWN = {}          # {"mat": material for the fresh axe cuts}
BASES = []         # (x, y, diameter) of every stake, for dressing their feet


def mesh_info(sm):
    if sm.get_name() not in INFO:
        bb = sm.get_bounding_box()
        mn, mx = bb.min, bb.max
        ext = [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z]
        ctr = [(mx.x + mn.x) / 2, (mx.y + mn.y) / 2, (mx.z + mn.z) / 2]
        long = ext.index(max(ext))
        INFO[sm.get_name()] = (ext, ctr, long)
    return INFO[sm.get_name()]


def place_between(label, folder, sm, a, b, dia, mat, spin=0.0):
    """Stretch a log/beam mesh so its long axis runs from point a to point b, with the given diameter."""
    ext, ctr, long = mesh_info(sm)
    to_x = [unreal.Rotator(0, 0, 0), unreal.Rotator(0, 0, -90), unreal.Rotator(0, -90, 0)][long]   # long axis -> X
    d = unreal.Vector(b.x - a.x, b.y - a.y, b.z - a.z)
    length = d.length()
    spin_r = unreal.Rotator(spin, 0, 0)                      # roll about the long axis, for variety
    rot = unreal.MathLibrary.compose_rotators(unreal.MathLibrary.compose_rotators(to_x, spin_r), unreal.MathLibrary.make_rot_from_x(d))
    scale = [dia / max(e, 0.1) for e in ext]
    scale[long] = length / max(ext[long], 0.1)
    c_scaled = unreal.Vector(ctr[0] * scale[0], ctr[1] * scale[1], ctr[2] * scale[2])
    xf = unreal.Transform(V(0, 0, 0), rot, V(1, 1, 1))
    off = unreal.MathLibrary.transform_direction(xf, c_scaled)
    mid = unreal.Vector((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2)
    loc = unreal.Vector(mid.x - off.x, mid.y - off.y, mid.z - off.z)
    act = actors.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
    c = act.static_mesh_component
    c.set_static_mesh(sm)
    c.set_world_scale3d(V(*scale))
    if mat:
        for i in range(max(1, c.get_num_materials())):
            c.set_material(i, mat)
    return tag(act, label, folder)


def upright(label, folder, sm, x, y, height, dia, mat, lean_x=0.0, lean_y=0.0, sink=40.0, tip=True, tip_mat=None):
    """A trunk standing in the mud. lean in degrees (x: toward the camera is negative)."""
    lx, ly = math.radians(lean_x), math.radians(lean_y)
    top = V(x + math.sin(lx) * height, y + math.sin(ly) * height, -sink + math.cos(lx) * math.cos(ly) * height)
    a = place_between(label, folder, sm, V(x, y, -sink), top, dia, mat, spin=rng.uniform(0, 360))
    BASES.append((x, y, dia))
    if tip and TIPS and rng.random() > 0.12:   # axe-hewn point: 3-4 uneven facets cut into the top of the trunk
        dirv = unreal.Vector(top.x - x, top.y - y, top.z + sink)
        n = math.sqrt(dirv.x ** 2 + dirv.y ** 2 + dirv.z ** 2)
        ux, uy, uz = dirv.x / n, dirv.y / n, dirv.z / n
        th = dia * rng.uniform(1.5, 2.3)
        sink_ = th * rng.uniform(0.2, 0.3)
        b0 = V(top.x - ux * sink_, top.y - uy * sink_, top.z - uz * sink_)
        place_between(label + "_Tip", folder, rng.choice(TIPS), V(b0.x + ux * th, b0.y + uy * th, b0.z + uz * th), b0,
                      dia * rng.uniform(0.74, 0.82), tip_mat or (HEWN.get("mat") if rng.random() < 0.3 else mat), spin=rng.uniform(0, 360))
        return a
    if tip and rng.random() > 0.14:            # ~1 in 7 is broken off flat
        # Crude axe-hewn point: a wedge (flattened on two faces), tilted, of varying length.
        th = dia * rng.uniform(0.7, 2.0)
        dirv = unreal.Vector(top.x - x, top.y - y, top.z + sink)
        n = math.sqrt(dirv.x ** 2 + dirv.y ** 2 + dirv.z ** 2)
        ux, uy, uz = dirv.x / n, dirv.y / n, dirv.z / n
        tl = V(top.x + ux * th * 0.42, top.y + uy * th * 0.42, top.z + uz * th * 0.42)
        base_rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(0, -90, 0), unreal.MathLibrary.make_rot_from_x(dirv))
        hew = unreal.Rotator(rng.uniform(-14, 14), rng.uniform(-14, 14), rng.uniform(0, 360))
        rot = unreal.MathLibrary.compose_rotators(hew, base_rot)
        t = actors.spawn_actor_from_class(unreal.StaticMeshActor, tl, rot)
        t.static_mesh_component.set_static_mesh(CONE)
        t.static_mesh_component.set_world_scale3d(V(dia * rng.uniform(0.75, 1.0) / 100, dia * rng.uniform(0.4, 0.95) / 100, th / 100))
        t.static_mesh_component.set_material(0, tip_mat or mat)
        tag(t, label + "_Tip", folder)
    return a


def box(label, folder, centre, size, mat, rot=(0, 0, 0)):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(*centre), unreal.Rotator(*rot))
    a.static_mesh_component.set_static_mesh(CUBE)
    a.static_mesh_component.set_world_scale3d(V(size[0] / 100, size[1] / 100, size[2] / 100))
    a.static_mesh_component.set_material(0, mat)
    return tag(a, label, folder)


def light(cls, label, folder, loc, rot=(0, 0, 0)):
    a = actors.spawn_actor_from_class(cls, V(*loc), unreal.Rotator(*rot))
    return tag(a, label, folder), a.light_component


def point(label, folder, loc, lumens, kelvin, radius=750, source=4.0, vol=0.5, shadows=True):
    a, c = light(unreal.PointLight, label, folder, loc)
    safe_set(c, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(c, "intensity", lumens)
    safe_set(c, "use_temperature", True)
    safe_set(c, "temperature", kelvin)
    safe_set(c, "attenuation_radius", radius)
    safe_set(c, "source_radius", source)
    safe_set(c, "volumetric_scattering_intensity", vol)
    safe_set(c, "cast_shadows", shadows)
    return a


def clear():
    for a in actors.get_all_level_actors():
        if TAG in [str(t) for t in a.tags]:
            actors.destroy_actor(a)


# ------------------------------------------------------------------ build

def build():
    for d in (ROOT + "/Materials", ROOT + "/Textures", ROOT + "/Meshes"):
        if not eal.does_directory_exist(d):
            eal.make_directory(d)

    MS = "Megascans/"
    L1, L2, BM = "old_wooden_log_wcokfh1_high", "old_wooden_log_wcokfdy_high", "old_wooden_beam_vkbhcbg_high"
    GR, MUD, DEC = "wild_grass_vlkhcbxia_high", "soil_mud_pkbch0_2k", "military_trenches_ground_mud_ydyqdits_2k"

    log("importing textures")
    t = {}
    for key, folder, pre in (("l1", L1, "Old_Wooden_Log_wcokfh1_High_4K_"), ("l2", L2, "Old_Wooden_Log_wcokfdy_High_4K_"),
                             ("bm", BM, "Old_Wooden_Beam_vkbhcbg_High_4K_")):
        t[key] = {"bc": tex(MS + folder, pre + "BaseColor.jpg", "color"), "n": tex(MS + folder, pre + "Normal.jpg", "normal"),
                  "r": tex(MS + folder, pre + "Roughness.jpg", "linear"), "ao": tex(MS + folder, pre + "AO.jpg", "linear")}
    gp = "Wild_Grass_vlkhcbxia_High_4K_"
    t["gr"] = {"bc": tex(MS + GR, gp + "BaseColor.jpg", "color"), "n": tex(MS + GR, gp + "Normal.jpg", "normal"),
               "op": tex(MS + GR, gp + "Opacity.jpg", "linear"), "tr": tex(MS + GR, gp + "Translucency.jpg", "color")}
    mp = "Soil_Mud_pkbch0_2K_"
    t["mud"] = {"bc": tex(MS + MUD, mp + "BaseColor.jpg", "color"), "n": tex(MS + MUD, mp + "Normal.jpg", "normal"),
                "r": tex(MS + MUD, mp + "Roughness.jpg", "linear"), "h": tex(MS + MUD, mp + "Displacement.jpg", "linear")}
    dp = "ydyqdits_2K_"
    t["dec"] = {"bc": tex(MS + DEC, dp + "Basecolor.jpg", "color"), "n": tex(MS + DEC, dp + "Normal.jpg", "normal"),
                "op": tex(MS + DEC, dp + "Opacity.jpg", "linear")}
    # The post mask (R: CROATOAN cut, G: stripped panel) is regenerated between rounds, so always re-import it.
    if eal.does_asset_exist(ROOT + "/Textures/T_CroatoanPanel_Mask"):
        eal.delete_asset(ROOT + "/Textures/T_CroatoanPanel_Mask")
    t["carve"] = {"mask": tex("Carving", "T_CroatoanPanel_Mask.png", "linear"), "grain": t["l2"]["bc"]}

    log("importing meshes")
    sm_l1 = mesh(L1, "Old_Wooden_Log_wcokfh1_High.fbx", "OldWoodenLog_A")
    sm_l2 = mesh(L2, "Old_Wooden_Log_wcokfdy_High.fbx", "OldWoodenLog_B")
    sm_bm = mesh(BM, "Old_Wooden_Beam_vkbhcbg_High.fbx", "OldWoodenBeam")
    grass = [mesh(GR, "Wild_Grass_vlkhcbxia_High_vlkhcbxia_Var%s_LOD0.fbx" % v, "WildGrass_" + v) for v in "ABCDEFGH"]
    # Axe-hewn stake points (our own meshes, Scripts/make_hewn_tips.py)
    for i in range(6):                         # always re-import: the tips are regenerated between rounds
        if eal.does_directory_exist(ROOT + "/Meshes/HewnTip_%d" % i):
            eal.delete_directory(ROOT + "/Meshes/HewnTip_%d" % i)
    TIPS[:] = [mesh("../Hewn", "HewnTip_%d.obj" % i, "HewnTip_%d" % i) for i in range(6)]
    # The CROATOAN post as real geometry (Scripts/make_panel_mask.ps1): bark, sunken panel, V-cut letters
    if eal.does_directory_exist(ROOT + "/Meshes/CroatoanPost"):
        eal.delete_directory(ROOT + "/Meshes/CroatoanPost")
    sm_post = mesh("../Carving", "CroatoanPost.obj", "CroatoanPost")
    for nm in ("Card_Base", "Card_Center"):
        if eal.does_directory_exist(ROOT + "/Meshes/" + nm):
            eal.delete_directory(ROOT + "/Meshes/" + nm)
    sm_card = mesh("../Cards", "Card_Base.obj", "Card_Base")
    sm_card_c = mesh("../Cards", "Card_Center.obj", "Card_Center")
    for sm_ in (sm_card, sm_card_c):                # flat cards: Nanite cannot draw the translucent cloud
        ns = sm_.get_editor_property("nanite_settings")
        ns.set_editor_property("enabled", False)
        sm_.set_editor_property("nanite_settings", ns)
        eal.save_loaded_asset(sm_)
    pine_tx = [tex("Pines", "T_Pine_%d.png" % i, "color") for i in range(6)]

    # ---- Poly Haven (CC0): scanned surfaces, trunks, rocks, fir trees, night sky
    WHITE = unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture")

    def ph_tex(asset, name, kind, gl=False):
        t_ = tex("PolyHaven/" + asset, name, kind)
        if gl:
            safe_set(t_, "flip_green_channel", True)            # OpenGL normal map
            eal.save_loaded_asset(t_)
        return t_

    def ph_surface(a):
        return {"bc": ph_tex(a, a + "_diff_2k.jpg", "color"), "n": ph_tex(a, a + "_nor_dx_2k.jpg", "normal"),
                "r": ph_tex(a, a + "_rough_2k.jpg", "linear"), "ao": ph_tex(a, a + "_arm_2k.jpg", "linear"),
                "h": ph_tex(a, a + "_disp_2k.jpg", "linear")}
    ph = {a: ph_surface(a) for a in ("knotted_pine_bark", "bark_brown_02", "brown_mud_leaves_01", "brown_mud_02", "forest_ground_04")}
    sm_dt1 = mesh("../PolyHaven/dead_tree_trunk", "dead_tree_trunk_2k.fbx", "PH_DeadTrunk")
    sm_dt2 = mesh("../PolyHaven/dead_tree_trunk_02", "dead_tree_trunk_02_2k.fbx", "PH_DeadTrunk02")
    dt1 = {"BaseColor": ph_tex("dead_tree_trunk/textures", "dead_tree_trunk_diff_2k.jpg", "color"),
           "Normal": ph_tex("dead_tree_trunk/textures", "dead_tree_trunk_nor_gl_2k.exr", "normal", gl=True),
           "Roughness": ph_tex("dead_tree_trunk/textures", "dead_tree_trunk_rough_2k.exr", "linear"), "AO": WHITE}
    dt2 = {"BaseColor": ph_tex("dead_tree_trunk_02/textures", "dead_tree_trunk_02_diff_2k.jpg", "color"),
           "Normal": ph_tex("dead_tree_trunk_02/textures", "dead_tree_trunk_02_nor_gl_2k.exr", "normal", gl=True),
           "Roughness": ph_tex("dead_tree_trunk_02/textures", "dead_tree_trunk_02_rough_2k.exr", "linear"), "AO": WHITE}
    sm_rock = mesh("../PolyHaven/rock_moss_set_01", "rock_moss_set_01_2k.fbx", "PH_RockMoss")
    rock_tx = {"bc": ph_tex("rock_moss_set_01/textures", "rock_moss_set_01_diff_2k.jpg", "color"),
               "n": ph_tex("rock_moss_set_01/textures", "rock_moss_set_01_nor_gl_2k.exr", "normal", gl=True),
               "r": ph_tex("rock_moss_set_01/textures", "rock_moss_set_01_rough_2k.jpg", "linear"), "ao": WHITE}
    sm_fir = mesh("../PolyHaven/fir_tree_01", "fir_tree_01_2k.fbx", "PH_FirTree")
    fir_bark = {"BaseColor": ph_tex("fir_tree_01/textures", "fir_tree_01_bark_diff_2k.png", "color"),
                "Normal": ph_tex("fir_tree_01/textures", "fir_tree_01_bark_nor_gl_2k.png", "normal", gl=True),
                "Roughness": ph_tex("fir_tree_01/textures", "fir_tree_01_bark_rough_2k.png", "linear"), "AO": WHITE}
    fir_twig = {"bc": ph_tex("fir_tree_01/textures", "fir_tree_01_twig_diff_2k.png", "color"),
                "op": ph_tex("fir_tree_01/textures", "fir_tree_01_twig_alpha_2k.png", "linear"),
                "n": ph_tex("fir_tree_01/textures", "fir_tree_01_twig_nor_gl_2k.png", "normal", gl=True),
                "tr": ph_tex("fir_tree_01/textures", "fir_tree_01_twig_diff_2k.png", "color")}
    sky_hdri = ph_tex("rogland_moonlit_night", "rogland_moonlit_night_4k.exr", "color")
    safe_set(sky_hdri, "compression_settings", unreal.TextureCompressionSettings.TC_HDR)
    safe_set(sky_hdri, "srgb", False)
    safe_set(sky_hdri, "mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    eal.save_loaded_asset(sky_hdri)
    for a_ in ("rough_wood", "thatch_roof_angled", "wood_trunk_wall"):
        ph[a_] = ph_surface(a_)
    ph["fine_grained_wood"] = {"bc": ph_tex("fine_grained_wood", "fine_grained_wood_col_2k.jpg", "color"),
                               "n": ph_tex("fine_grained_wood", "fine_grained_wood_nor_dx_2k.jpg", "normal"),
                               "r": ph_tex("fine_grained_wood", "fine_grained_wood_rough_2k.jpg", "linear"),
                               "ao": ph_tex("fine_grained_wood", "fine_grained_wood_arm_2k.jpg", "linear")}

    def acg(a_):                                      # ambientCG (CC0) 2K JPG set
        p_ = "AmbientCG/" + a_
        return {"BaseColor": tex(p_, a_ + "_2K-JPG_Color.jpg", "color"), "Normal": tex(p_, a_ + "_2K-JPG_NormalDX.jpg", "normal"),
                "Roughness": tex(p_, a_ + "_2K-JPG_Roughness.jpg", "linear"), "AO": WHITE}
    rope_tx, plaster_tx = acg("Rope001"), acg("Plaster001")

    def ph_plant(a_):
        p_ = "PolyHaven/" + a_ + "/textures"
        sm_ = mesh("../PolyHaven/" + a_, a_ + "_2k.fbx", "PH_" + a_)
        tx_ = {"bc": tex(p_, a_ + "_diff_2k.jpg", "color"), "op": tex(p_, a_ + "_alpha_2k.png", "linear"),
               "n": ph_tex(a_ + "/textures", a_ + "_nor_gl_2k.exr", "normal", gl=True), "tr": tex(p_, a_ + "_diff_2k.jpg", "color")}
        return tx_, [sm_]
    ph_grass, ph_weed = ph_plant("grass_medium_01"), ph_plant("weed_plant_02")
    # Poly Haven Lantern_01 (CC0): a metal-framed glass lantern, for the gate, the tower and the far lights
    lantern_parts = import_parts(SRC + "/PolyHaven/Lantern_01/Lantern_01_2k.fbx", ROOT + "/Meshes/PH_Lantern01")
    log("lantern parts: %s" % [(m_.get_name(), [str(s.material_slot_name) for s in m_.static_materials]) for m_ in lantern_parts])

    def ph_mi(name, a_, scalars, tint):
        d_ = ph[a_]
        return mi(name, master, scalars, tint, {"BaseColor": d_["bc"], "Normal": d_["n"], "Roughness": d_["r"], "AO": d_["ao"]})

    # the palisade, gate, rails, braces and tower are built from the scanned trunk
    sm_l1 = sm_l2 = sm_bm = sm_dt1
    # The UV Lantern's beam profile (Scripts/make_uv_ies.py): an uneven torch edge, not a stage spot
    if eal.does_directory_exist(ROOT + "/Lights"):
        eal.delete_directory(ROOT + "/Lights")
    uv_ies = next((o for o in import_file(SRC + "/Light/UVLantern.ies", ROOT + "/Lights") if isinstance(o, unreal.TextureLightProfile)), None)

    # Round 6: rocks and weeds (free Megascans, Standard License $0)
    def plant_set(folder, pre, uid, variants):
        tx = {"bc": tex(MS + folder, pre + "4K_BaseColor.jpg", "color"), "n": tex(MS + folder, pre + "4K_Normal.jpg", "normal"),
              "op": tex(MS + folder, pre + "4K_Opacity.jpg", "linear"), "tr": tex(MS + folder, pre + "4K_Translucency.jpg", "color")}
        ms = []
        for v in variants:
            fn = "%s%s_Var%s_LOD0.fbx" % (pre, uid, v)
            if os.path.exists(SRC + "/Megascans/" + folder + "/" + fn):
                ms.append(mesh(folder, fn, folder.split("_")[0] + "_" + v))
        return tx, ms

    def rock_set(folder, pre, fbx, name):
        tx = {"bc": tex(MS + folder, pre + "4K_BaseColor.jpg", "color"), "n": tex(MS + folder, pre + "4K_Normal.jpg", "normal"),
              "r": tex(MS + folder, pre + "4K_Roughness.jpg", "linear"), "ao": tex(MS + folder, pre + "4K_AO.jpg", "linear")}
        return tx, mesh(folder, fbx, name)

    plants_quixel = {
        "weeds": plant_set("curbside_weeds_ujzjfexja_high", "Curbside_Weeds_ujzjfexja_High_", "ujzjfexja", "ABCDEFGHIJK"),
        "nettle": plant_set("common_hemp_nettle_xh1kdfbqx_high", "Common_Hemp_Nettle_xh1kdfbqx_High_", "xh1kdfbqx", "ABCDEFG"),
        "dry": plant_set("dry_grass_tbbqejqr_high", "Dry_Grass_tbbqejqr_High_", "tbbqejqr", "ABCDE"),
        "wheat": plant_set("wheat_grass_tdcrdbur_high", "Wheat_Grass_tdcrdbur_High_", "tdcrdbur", "ABCDEF"),
        "shrubs": plant_set("dead_shrubs_vdknafgha_high", "Dead_Shrubs_vdknafgha_High_", "vdknafgha", "ABCDEFGH"),
    }
    plants = {"grass": ph_grass, "weed": ph_weed}
    rocks_quixel = [
        rock_set("small_stones_pack_vdjkbfmiw_high", "Small_Stones_Pack_vdjkbfmiw_High_", "Small_Stones_Pack_vdjkbfmiw_High.fbx", "SmallStones"),
        rock_set("military_trenches_scatter_rock_s_06_ydzrebd_high", "Military_Trenches_Scatter_Rock_S_06_ydzrebd_High_", "Military_Trenches_Scatter_Rock_S_06_ydzrebd_High.fbx", "Rock06"),
        rock_set("military_trenches_scatter_rock_s_03_ydzsbbr_high", "Military_Trenches_Scatter_Rock_S_03_ydzsbbr_High_", "Military_Trenches_Scatter_Rock_S_03_ydzsbbr_High.fbx", "Rock03"),
    ]

    rocks = [(rock_tx, sm_rock)]

    log("materials")
    master = m_surface(t["l1"])
    mi_l1 = mi("MI_Log_A", master, {"Wet": 0.35}, {"Tint": (0.62, 0.62, 0.66)})
    mi_l2 = mi("MI_Log_B", master, {"Wet": 0.35}, {"Tint": (0.58, 0.58, 0.62)}, {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_dark = mi("MI_Log_Dark", master, {"Wet": 0.5}, {"Tint": (0.32, 0.31, 0.32)}, {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_post = mi("MI_Log_Stripped", master, {"Pale": 0.6, "PaleBright": 1.45, "Wet": 0.15, "UVScale": 1.0}, {"Tint": (1, 1, 1)},
                 {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_beam = mi("MI_Beam", master, {"Wet": 0.4}, {"Tint": (0.5, 0.48, 0.48)}, {"BaseColor": t["bm"]["bc"], "Normal": t["bm"]["n"], "Roughness": t["bm"]["r"], "AO": t["bm"]["ao"]})
    mi_rope = mi("MI_Rope", master, {"Wet": 0.3, "UVScale": 6.0}, {"Tint": (0.9, 0.78, 0.55)}, {"BaseColor": t["bm"]["bc"], "Normal": t["bm"]["n"], "Roughness": t["bm"]["r"], "AO": t["bm"]["ao"]})
    mi_l1 = mi("MI_Log_A", master, {"Wet": 0.4}, {"Tint": (0.70, 0.68, 0.66)}, dt1)
    mi_l2 = mi("MI_Log_B", master, {"Wet": 0.4}, {"Tint": (0.60, 0.58, 0.56)}, dt1)
    mi_dark = mi("MI_Log_Dark", master, {"Wet": 0.5}, {"Tint": (0.40, 0.39, 0.38)}, dt1)
    m_mud = m_ground(ph["brown_mud_leaves_01"])
    mi_beam = mi("MI_Beam", master, {"Wet": 0.45}, {"Tint": (0.52, 0.50, 0.48)}, dt1)
    mi_rope = mi("MI_Rope", master, {"Wet": 0.45, "UVScale": 2.0}, {"Tint": (0.26, 0.22, 0.17)}, rope_tx)
    mi_thatch = ph_mi("MI_Thatch", "thatch_roof_angled", {"Wet": 0.25, "UVScale": 2.5}, {"Tint": (0.55, 0.52, 0.48)})
    m_gr = m_foliage(t["gr"])
    m_carve = m_decal("M_CroatoanCarving", t["carve"], carving=True)
    m_mdec = m_decal("M_MudDecal", t["dec"])
    m_pud = m_puddle("M_Puddle", t["mud"]["h"])
    m_lamp = m_unlit("M_LanternGlass", (1.0, 0.38, 0.10), 0.22)
    m_lamp_far = m_unlit("M_LanternGlassFar", (1.0, 0.40, 0.12), 0.9)
    m_lglass = m_glass("M_LanternGlassSoft", (1.0, 0.45, 0.16), 0.10, 0.45)
    m_flame = m_unlit("M_LanternFlame", (1.0, 0.52, 0.18), 1.6)
    m_win = m_unlit("M_WindowGlow", (1.0, 0.45, 0.22), 0.05)
    m_uvlens = m_unlit("M_UVLens", (0.42, 0.26, 1.0), 4.0)
    m_sky = m_unlit("M_NightSky", (0.060, 0.075, 0.100), 1.0)
    m_iron = mi("MI_IronDark", master, {"Wet": 0.6, "UVScale": 3.0}, {"Tint": (0.08, 0.08, 0.085)},
                {"BaseColor": WHITE, "Normal": ph["rough_wood"]["n"], "Roughness": ph["rough_wood"]["r"], "AO": WHITE})

    log("level")
    if eal.does_asset_exist(MAP):
        levels.load_level(MAP)
        clear()
    else:
        levels.new_level(MAP)

    # ==========================================================================================
    # Round "match": framed and lit to the concept sketch (art/levels/roanoke/croatoan-gate.jpg).
    # Cold moonlit fog; warm light only from three practicals (watch platform, gate, house windows).
    # Eye-height 35 mm camera; the gatepost large on the right third; the palisade receding left.
    # ==========================================================================================
    mi_bark = mi("MI_Log_PostBark", master, {"Wet": 0.45}, {"Tint": (0.30, 0.28, 0.27)},
                 {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    HEWN["mat"] = ph_mi("MI_Log_Hewn", "rough_wood", {"Pale": 0.2, "PaleBright": 1.0, "Wet": 0.45, "UVScale": 0.6}, {"Tint": (0.80, 0.74, 0.66)})
    _unused_hewn = (
                     {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_daub = mi("MI_Daub", master, {"Wet": 0.2, "UVScale": 3.0}, {"Tint": (0.20, 0.19, 0.18)}, plaster_tx)
    _unused_daub = (
                 {"BaseColor": t["bm"]["bc"], "Normal": t["bm"]["n"], "Roughness": t["bm"]["r"], "AO": t["bm"]["ao"]})

    _cb = float(os.environ.get("LETHE_CAM_BACK", "78"))          # cm further back, along the line to the post
    _pd = math.hypot(225.0 + 143.0, 465.0 - 621.0)
    CAM = (-143.0 - _cb * (225.0 + 143.0) / _pd, 621.0 - _cb * (465.0 - 621.0) / _pd, float(os.environ.get("LETHE_CAM_Z", "130")))
    CAM_YAW, CAM_PITCH = -35.0, float(os.environ.get("LETHE_CAM_PITCH", "1.0"))
    SINK = float(os.environ.get("LETHE_POST_SINK", "35"))     # the post stands this much lower: CROATOAN at chin height
    _cy, _sy = math.cos(math.radians(CAM_YAW)), math.sin(math.radians(CAM_YAW))
    _cp, _sp = math.cos(math.radians(CAM_PITCH)), math.sin(math.radians(CAM_PITCH))
    CF, CR, CU = (_cp * _cy, _cp * _sy, _sp), (-_sy, _cy, 0.0), (-_sp * _cy, -_sp * _sy, _cp)
    HX_, HY_ = 18.0 / 35.0, 10.125 / 35.0                    # tan of the half field of view, 35 mm on 36 x 20.25

    def ray(fx, fy):
        nx_, ny_ = (fx - 0.5) * 2 * HX_, (0.5 - fy) * 2 * HY_
        return tuple(CF[i] + nx_ * CR[i] + ny_ * CU[i] for i in range(3))

    def at_frame(fx, fy, depth):
        """World point seen at frame (fx, fy), `depth` cm in front of the camera."""
        r_ = ray(fx, fy)
        return tuple(CAM[i] + depth * r_[i] for i in range(3))

    def at_frame_z(fx, fy, z):
        """World point seen at frame (fx, fy) at height z."""
        r_ = ray(fx, fy)
        return at_frame(fx, fy, (z - CAM[2]) / r_[2])

    def frame_of(x, y, z):
        d_ = (x - CAM[0], y - CAM[1], z - CAM[2])
        dep = sum(d_[i] * CF[i] for i in range(3))
        return (0.5 + 0.5 * sum(d_[i] * CR[i] for i in range(3)) / dep / HX_,
                0.5 - 0.5 * sum(d_[i] * CU[i] for i in range(3)) / dep / HY_, dep)

    def unit(yaw):
        return math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

    def toward_cam(px, py, ux, uy):
        """The wall normal (perpendicular to direction u) that faces the camera."""
        nx, ny = -uy, ux
        if nx * (CAM[0] - px) + ny * (CAM[1] - py) < 0:
            nx, ny = -nx, -ny
        return nx, ny

    def local(origin, yaw, dx, dy, dz):
        """World point for an offset (dx, dy, dz) in a frame at origin turned by yaw."""
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        return (origin[0] + dx * c - dy * s, origin[1] + dx * s + dy * c, origin[2] + dz)

    def shingle_roof(label, folder, ridge, yaw, length, run, slope, mat, course=18.0, width=(14.0, 28.0), under=None):
        """A pitched roof of individual split shingles. ridge = centre of the ridge line; the ridge runs along the
        frame's local Y (yaw), each side falls away along local +-X for `run` cm at `slope` degrees. Courses overlap;
        each shingle's butt end rests on the course below, so it sits a little flatter than the roof and catches light."""
        cs, sn = math.cos(math.radians(slope)), math.sin(math.radians(slope))
        for side in (-1, 1):
            if under is not None:                       # dark underlay so the gaps never show sky
                d = run / 2
                box(label + "_Underlay", folder, local(ridge, yaw, side * cs * d + side * sn * 3, 0, -sn * d - cs * 3),
                    (run, length, 2), under, rot=(0, -side * slope, yaw))
            d = run - course * 0.6
            while d > course * 0.3:
                y = -length / 2 + rng.uniform(0, 8)
                while y < length / 2:
                    w = rng.uniform(*width)
                    w = min(w, length / 2 - y)
                    if w > 5:
                        ln = course * rng.uniform(2.1, 2.5)
                        dd = d - ln / 2 + course + rng.uniform(-1.5, 1.5)
                        lift = 2.0 + rng.uniform(0, 1.2)
                        box(label + "_Shingle", folder,
                            local(ridge, yaw, side * cs * dd + side * sn * lift, y + w / 2, -sn * dd + cs * lift),
                            (ln, w - rng.uniform(0.6, 2.0), rng.uniform(1.6, 2.6)), mat,
                            rot=(rng.uniform(-1.5, 1.5), -side * (slope - rng.uniform(2.0, 4.5)), yaw + rng.uniform(-1.2, 1.2)))
                    y += w
                d -= course
        place_between(label + "_Ridge", folder, sm_bm, V(*local(ridge, yaw, 0, -length / 2 - 10, 4)),
                      V(*local(ridge, yaw, 0, length / 2 + 10, 4)), 14, mi_dark)

    def lash_at(cx, cy, cz, ux, uy, folder, dia=22.0):
        """Three turns of rope binding a rail to a trunk, wound diagonally across the rail."""
        for k in range(3):
            o = (k - 1) * 6.0
            place_between("Lashing", folder, sm_bm, V(cx - ux * 10 + ux * o, cy - uy * 10 + uy * o, cz - dia * 0.6),
                          V(cx + ux * 10 + ux * o, cy + uy * 10 + uy * o, cz + dia * 0.6), 3.6, mi_rope, spin=rng.uniform(0, 360))

    def band_at(cx, cy, cz, dx, dy, dz, dia, folder, turns=7, rope=3.4):
        turns = int(turns * 1.6)
        """A thick hemp band: many turns of rope wound round a log whose axis is (dx, dy, dz)."""
        n = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        dx, dy, dz = dx / n, dy / n, dz / n
        base = unreal.MathLibrary.make_rot_from_z(V(dx, dy, dz))
        for k in range(turns):
            o = (k - (turns - 1) / 2.0) * rope * 0.8
            rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(0, 360)), base)
            a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(cx + dx * o, cy + dy * o, cz + dz * o), rot)
            a.static_mesh_component.set_static_mesh(CYL)
            dd = dia + rope * rng.uniform(0.55, 0.85)
            a.static_mesh_component.set_world_scale3d(V(dd / 100, dd / 100, rope / 100))
            a.static_mesh_component.set_material(0, mi_rope)
            tag(a, "RopeBand", folder)

    def curtain(label, x0, y0, yaw, length, hgt, dia, lean_out, rail_z, rail_every=2, lean_along=0.0, back_row=False,
                rail_dia=19, step=(0.62, 0.72), mats=None, taper=0.0):
        """Whole trunks set tight along a line; uneven height, girth and lean; rails roped on the outer face."""
        ux, uy = unit(yaw)
        nx, ny = toward_cam(x0, y0, ux, uy)
        s, stakes = 0.0, []
        dmax = dia[1]
        mats = mats or logs
        while s < length:
            sm_, mt = mats[rng.randrange(len(mats))]
            d = rng.uniform(*dia)
            px, py = x0 + ux * s + nx * rng.uniform(-5, 5), y0 + uy * s + ny * rng.uniform(-5, 5)
            lo = lean_out + rng.uniform(-2.0, 2.0)
            side = lean_along + rng.uniform(-2.0, 2.0)
            upright(label, "Palisade", sm_, px, py, rng.uniform(*hgt) * (1 - taper * s / length), d, mt,
                    lean_x=nx * lo + ux * side, lean_y=ny * lo + uy * side)
            stakes.append((s, d))
            s += d * rng.uniform(*step)
        if back_row:                                   # a second row behind, on the joints: no gaps, no fog through the wall
            s = dmax * 0.35
            while s < length:
                d = rng.uniform(*dia)
                px, py = x0 + ux * s - nx * dmax * 0.55, y0 + uy * s - ny * dmax * 0.55
                upright(label + "_Back", "Palisade", sm_l1, px, py, rng.uniform(hgt[0] * 0.9, hgt[1] * 0.95) * (1 - taper * s / length), d, mi_shadow,
                        lean_x=nx * lean_out + ux * lean_along, lean_y=ny * lean_out + uy * lean_along)
                s += d * rng.uniform(0.75, 0.9)
        off = dmax * 0.5 + rail_dia * 0.5 - 4
        for z in rail_z:
            zz = z + rng.uniform(-8, 8)
            z1 = zz + rng.uniform(-14, 14)
            place_between(label + "_Rail", "Palisade", sm_l1, V(x0 + nx * off - ux * 30, y0 + ny * off - uy * 30, zz),
                          V(x0 + nx * off + ux * (length + 30), y0 + ny * off + uy * (length + 30), z1), rail_dia, mi_dark)
            for i, (ss, d) in enumerate(stakes):
                if i % rail_every == 1:
                    t_ = (ss + 30) / (length + 60)
                    band_at(x0 + ux * ss + nx * off, y0 + uy * ss + ny * off, zz + (z1 - zz) * t_, ux, uy, 0.0, rail_dia,
                            "Palisade", turns=rng.choice((5, 6, 7)))

    logs = [(sm_l1, mi_dark), (sm_l2, mi_l1)]
    mi_shadow = mi("MI_Log_Shadow", master, {"Wet": 0.5}, {"Tint": (0.22, 0.21, 0.21)}, dt1)

    def lantern(label, folder, c, height, lumens, kelvin=2700, radius=450, vol=1.5, flame=1.0):
        """A lantern centred on c, `height` cm tall: Lantern_01 frame (dark iron), soft glass, a flame, a hazy light."""
        lo = [1e9, 1e9, 1e9]; hi = [-1e9, -1e9, -1e9]
        for m_ in lantern_parts:
            bb = m_.get_bounding_box()
            for i, (a_, b_) in enumerate(((bb.min.x, bb.max.x), (bb.min.y, bb.max.y), (bb.min.z, bb.max.z))):
                lo[i] = min(lo[i], a_); hi[i] = max(hi[i], b_)
        sc = height / max(1.0, hi[2] - lo[2])
        ctr = [(lo[i] + hi[i]) / 2 * sc for i in range(3)]
        for m_ in lantern_parts:
            a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(c[0] - ctr[0], c[1] - ctr[1], c[2] - ctr[2]), unreal.Rotator(0, 0, 0))
            a.static_mesh_component.set_static_mesh(m_)
            a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
            for k, slot in enumerate(m_.static_materials):
                a.static_mesh_component.set_material(k, m_lglass if "glass" in str(slot.material_slot_name).lower() else m_iron)
            tag(a, label + "_Frame", folder)
        f = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(c[0], c[1], c[2] - height * 0.08), unreal.Rotator(0, 0, 0))
        f.static_mesh_component.set_static_mesh(SPHERE)
        f.static_mesh_component.set_world_scale3d(V(height * 0.07 / 100 * flame, height * 0.07 / 100 * flame, height * 0.16 / 100 * flame))
        f.static_mesh_component.set_material(0, m_flame)
        f.static_mesh_component.set_editor_property("cast_shadow", False)
        tag(f, label + "_Flame", folder)
        return point(label + "_Light", folder, (c[0], c[1], c[2] - height * 0.05), lumens, kelvin, radius=radius, source=2.5, vol=vol)
    dark_logs = [(sm_l1, mi_dark), (sm_l1, mi_shadow)]

    # Ground: dark wet mud, puddles in the low spots of the scan
    MUDPATCH = os.environ.get("LETHE_MUDPATCH", "1") == "1" and os.path.exists(SRC + "/Ground/MudPatch.obj")
    g = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(1500, 0, -6.0 if MUDPATCH else 0.0), unreal.Rotator(0, 0, 0))
    g.static_mesh_component.set_static_mesh(PLANE)
    g.static_mesh_component.set_world_scale3d(V(80, 80, 1))
    mi_mud = mi("MI_Mud", m_mud, {"UVScale": 34.0, "PuddleLevel": 0.50, "PuddleSharpness": 10.0,
                                  "WetDarken": 2.4, "RoughnessMult": 0.30, "Desat": 0.7}, {"MudTint": (1.0, 0.90, 0.86)})
    g.static_mesh_component.set_material(0, mi_mud)
    tag(g, "Ground_Mud", "Ground")
    if MUDPATCH:
        # the foreground mud sculpted (Scripts/make_mud_patch.py): cart ruts to the gate, footprints, clods; the flat
        # plane above sits 6 cm lower and only shows beyond it
        mdir = ROOT + "/Meshes/MudPatch"
        if eal.does_directory_exist(mdir):
            eal.delete_directory(mdir)
        import_file(SRC + "/Ground/MudPatch.obj", mdir)
        mp_sm = next((a_ for a_ in (unreal.load_asset(p_) for p_ in eal.list_assets(mdir, recursive=True))
                      if isinstance(a_, unreal.StaticMesh)), None)
        if mp_sm:
            bb_ = mp_sm.get_bounding_box()
            cy_ = (bb_.min.y + bb_.max.y) / 2
            mir_ = -1.0 if cy_ < 0 else 1.0                  # it should centre near y = +210; the importer may flip Y
            mpa = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(0, 0, 0), unreal.Rotator(0, 0, 0))
            mpa.static_mesh_component.set_static_mesh(mp_sm)
            mpa.set_actor_scale3d(V(1, mir_, 1))
            mpa.static_mesh_component.set_material(0, mi_mud)
            tag(mpa, "Ground_MudSculpt", "Ground")
            log("mud patch: bbox %s..%s, mirror y %s" % (bb_.min, bb_.max, mir_))
        else:
            log("MUD PATCH IMPORT FAILED")

    # --- the CROATOAN post: right-hand post of the entrance, a great trunk with its bark taken off in front
    P = "CroatoanPost"
    PX, PY = 225.0, 465.0
    face = -12.0                                      # the panel faces yaw 168, the word centred in view
    fx, fy = unit(face)
    post = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(PX, PY, -SINK), unreal.Rotator(0, 0, face + 180))
    post.static_mesh_component.set_static_mesh(sm_post)
    l2 = {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]}
    post_mats = {
        "Bark": mi("MI_Post_Bark", master, {"Wet": 0.2, "RoughnessMult": 1.4}, {"Tint": (0.62, 0.57, 0.53)},
                   {"BaseColor": ph["knotted_pine_bark"]["bc"], "Normal": ph["knotted_pine_bark"]["n"],
                    "Roughness": ph["knotted_pine_bark"]["r"], "AO": ph["knotted_pine_bark"]["ao"]}),
        "Panel": ph_mi("MI_Post_Panel", "rough_wood", {"Pale": 0.92, "PaleBright": float(os.environ.get("LETHE_PANEL_BRIGHT", "4.8")),
                                                       "PaleContrast": 1.35, "Wet": 0.08, "RoughnessMult": 1.2},
                       {"PaleColor": (0.80, 0.72, 0.61), "Tint": (1.0, 1.0, 1.0)}),
        "Cut": ph_mi("MI_Post_CutWood", "rough_wood", {"Pale": 0.92, "PaleBright": 1.5, "PaleContrast": 1.15, "Wet": 0.05,
                                                        "RoughnessMult": 1.3, "UVScale": 3.0},
                     {"PaleColor": (0.70, 0.60, 0.55), "Tint": (1.0, 1.0, 1.0)}),
    }
    for k, slot in enumerate(sm_post.static_materials):
        post.static_mesh_component.set_material(k, post_mats.get(str(slot.material_slot_name), post_mats["Bark"]))
    tag(post, "CROATOAN_Post", P)
    place_between("SecondPost", P, sm_dt1, V(315, 375, -60), V(318, 371, 950), 52, post_mats["Bark"], spin=200)

    # --- the entrance: left gatepost, a dark trunk beside the CROATOAN post, and a lashed gate between
    G = "Gate"
    place_between("GatePost_L", G, sm_l2, V(700, -158, -60), V(703, -160, 520), 50, mi_dark, spin=120)     # spec x 0.39-0.46
    place_between("GatePost_L2", G, sm_l1, V(712, -112, -60), V(713, -110, 490), 46, mi_dark, spin=40)
    upright("GateTrunk", G, sm_l1, 722, 138, 560, 54, mi_dark, lean_x=-1.0, lean_y=0.5)
    vy = -84.0
    while vy < 112:                                    # the gate leaf: upright poles, tight
        d = rng.uniform(19, 25)
        upright("GatePole", G, logs[rng.randrange(2)][0], 728 + rng.uniform(-3, 3), vy, rng.uniform(330, 360), d, mi_dark,
                lean_y=rng.uniform(-1.5, 1.5))
        vy += d * rng.uniform(0.85, 0.95)
    for z in (60, 186):                               # rails on the outer face, rope bands at the poles (spec y 0.72, 0.51)
        zz = z + rng.uniform(-6, 6)
        z1 = zz + rng.uniform(-8, 8)
        place_between("GateBar", G, sm_l1, V(704, -150, zz), V(704, 125, z1), 26, mi_beam)
        for yy in (-135, -60, 20, 100):
            band_at(704, yy, zz + (z1 - zz) * (yy + 150) / 275.0, 0.0, 1.0, 0.0, 26, G, turns=rng.choice((6, 7, 8)))
    for z in (395, 355):                              # two thick round crossbeams (spec y 0.15-0.28), roped to the posts
        z1 = z + rng.uniform(-8, 8)
        place_between("GateLintel", G, sm_l2, V(712, -185, z), V(718, 165, z1), 40, mi_dark)
        band_at(712, -136, z + (z1 - z) * 0.14, 0.0, 1.0, 0.0, 40, G, turns=8)
        band_at(718, 126, z1 - (z1 - z) * 0.1, 0.0, 1.0, 0.0, 40, G, turns=7)
    # Dark stakes close behind the gate (spec: the gap and crossbeams are dark, not fog-lit grey)
    vy = -420.0
    while vy < 150:
        d = rng.uniform(30, 40)
        upright("GateInner", G, sm_l1, 960 + rng.uniform(-10, 10), vy, rng.uniform(340, 400), d, mi_shadow)
        vy += d * rng.uniform(0.7, 0.8)
    box("GateInner_Backing", G, (1010, -140, 200), (20, 620, 420), mi_shadow)
    # A lantern hung on the gate
    lx, ly, lz = 676.0, 92.0, 256.0                      # spec: frame (0.537, 0.38)
    _ld = frame_of(lx, ly, lz)[2]
    lx, ly, lz = at_frame(float(os.environ.get("LETHE_GLANTERN_FX", "0.505")), float(os.environ.get("LETHE_GLANTERN_FY", "0.355")), _ld)
    log("gate lantern at (%.0f, %.0f, %.0f), frame %s" % (lx, ly, lz, str(frame_of(lx, ly, lz))))
    place_between("GateLantern_Hook", G, sm_bm, V(lx, ly, lz + 18), V(lx, ly, lz + 40), 1.6, m_iron)
    lantern("GateLantern", G, (lx, ly, lz), 50, float(os.environ.get("LETHE_GLANTERN_LM", "16")), radius=520, vol=0.45, flame=1.15)

    # --- the palisade -------------------------------------------------------------------------
    # left: a tight bundle of 35-50 cm trunks leaning toward the gate ("/" in frame), two roped rails, a row behind
    curtain("Trunk_L", 712, -300, -90, 1500, (430, 505), (35, 50), 3.0, (95, 315), rail_every=3, lean_along=-14.0,
            back_row=True, rail_dia=27, taper=0.40)
    for yy_ in (-200, -224, -248, -272):                           # upright stakes closing the foot of the wall against the gatepost
        upright("Trunk_LG", "Palisade", sm_l1, 714 + rng.uniform(-4, 4), yy_, rng.uniform(400, 440), rng.uniform(36, 44), mi_dark)
    # right: tall, more upright, separate pointed stakes, set back so the barrel stands in front of them
    curtain("Trunk_R", 905, 75, 50, 520, (360, 420), (36, 46), 1.0, (120,), rail_every=2, step=(0.98, 1.08), rail_dia=22)

    # --- the watchtower, top left: legs, platform, railed walk, shingled pitched roof, a lantern
    T = "Watchtower"
    _wl = at_frame_z(0.19, 0.14, 850.0)
    TX, TY = _wl[0] + 140.0, _wl[1] - 140.0
    log("tower at (%.0f, %.0f), lantern depth %.0f" % (TX, TY, frame_of(*_wl)[2]))
    mi_shingle = ph_mi("MI_Shingle", "wood_trunk_wall", {"Wet": 0.35, "UVScale": 1.5}, {"Tint": (0.40, 0.38, 0.36)})
    _unused_shingle = (
                    {"BaseColor": t["bm"]["bc"], "Normal": t["bm"]["n"], "Roughness": t["bm"]["r"], "AO": t["bm"]["ao"]})
    legs = [(-170, -170), (170, -170), (170, 170), (-170, 170)]            # round the square
    for (ox, oy) in legs:
        place_between("Tower_Leg", T, sm_l2, V(TX + ox, TY + oy, -40), V(TX + ox * 0.95, TY + oy * 0.95, 910), 30, mi_dark)
    for k in range(4):                                                     # X braces on every face, both storeys
        a_, b_ = legs[k], legs[(k + 1) % 4]
        for (z0, z1) in ((20, 345), (365, 700)):
            place_between("Tower_Brace", T, sm_bm, V(TX + a_[0], TY + a_[1], z0), V(TX + b_[0], TY + b_[1], z1), 12, mi_dark)
            place_between("Tower_Brace", T, sm_bm, V(TX + b_[0], TY + b_[1], z0), V(TX + a_[0], TY + a_[1], z1), 12, mi_dark)
        for zz in (355, 710):                                              # floor beams
            place_between("Tower_Beam", T, sm_bm, V(TX + a_[0], TY + a_[1], zz), V(TX + b_[0], TY + b_[1], zz), 16, mi_beam)
        for zz in (755, 805):                                              # rails round the walk
            place_between("Tower_Rail", T, sm_bm, V(TX + a_[0], TY + a_[1], zz), V(TX + b_[0], TY + b_[1], zz + rng.uniform(-4, 4)), 10, mi_beam)
        for j in range(1, 12):                                             # balusters
            t_ = j / 12.0
            bx0, by0 = TX + a_[0] + (b_[0] - a_[0]) * t_, TY + a_[1] + (b_[1] - a_[1]) * t_
            place_between("Tower_Baluster", T, sm_bm, V(bx0, by0, 722), V(bx0, by0, 808), 6, mi_beam)
    box("Tower_Floor", T, (TX, TY, 718), (380, 380, 12), mi_beam)
    box("Tower_MidFloor", T, (TX, TY, 361), (360, 360, 10), mi_beam)
    for sy in (-38, 38):                                                   # ladder up the near face
        place_between("Tower_LadderRail", T, sm_bm, V(TX - 200, TY + sy, -10), V(TX - 178, TY + sy, 715), 8, mi_beam)
    for k in range(21):
        zz = 20 + k * 34
        place_between("Tower_Rung", T, sm_bm, V(TX - 199 + k * 1.6, TY - 40, zz), V(TX - 199 + k * 1.6, TY + 40, zz), 5, mi_beam)
    # Pitched roof, ridge along X, 80 cm of overhang: rows of boards, each kicked out a little at its lower edge
    eave, ridge, half = 910.0, 1050.0, 250.0
    slope = math.degrees(math.atan2(ridge - eave, half))
    run = half / math.cos(math.radians(slope))
    shingle_roof("Tower_Roof", T, (TX, TY, ridge + 2), 90.0, 560, run, slope, mi_shingle, course=17.0, width=(13.0, 26.0), under=m_iron)
    for side in (-1, 1):
        place_between("Tower_Fascia", T, sm_bm, V(TX - 275, TY + side * half, eave - 4), V(TX + 275, TY + side * half, eave - 4), 12, mi_dark)
    wl = (TX - 140, TY + 140, 850)
    place_between("Tower_LampHook", T, sm_bm, V(wl[0], wl[1], wl[2] + 14), V(wl[0], wl[1], wl[2] + 45), 1.6, m_iron)
    lantern("Tower_Lamp", T, wl, 44, float(os.environ.get("LETHE_TOWER_LAMP", "170")), kelvin=2200, radius=900, vol=1.1, flame=1.4)
    point("Tower_GalleryGlow", T, (TX, TY, 790), float(os.environ.get("LETHE_TOWER_GLOW", "300")), 2200, radius=520, source=30, vol=0.9)     # warm light inside the gallery
    # the tower stands on a log-walled lower storey down to the ground (solid below the gallery, as painted)
    for (ax, ay, bx_, by_) in ((-185, -185, 185, -185), (185, -185, 185, 185), (185, 185, -185, 185), (-185, 185, -185, -185)):
        zz = 4.0
        while zz < 700:
            place_between("Tower_WallLog", T, sm_l1, V(TX + ax * 1.04, TY + ay * 1.04, zz), V(TX + bx_ * 1.04, TY + by_ * 1.04, zz + rng.uniform(-3, 3)),
                          30, mi_dark, spin=rng.uniform(0, 360))
            zz += 28.0

    # --- the house behind, top right (painting: a gabled two-storey house well behind the palisade, seen at an angle,
    # its roof and two chimneys dark against the fog, a warm window high in the left gable and a lit door below it)
    B = "House"
    _rg = at_frame(float(os.environ.get("LETHE_HOUSE_FX", "0.885")), float(os.environ.get("LETHE_HOUSE_FY", "0.115")),
                   float(os.environ.get("LETHE_HOUSE_DEPTH", "2650")))
    HX, HY = _rg[0], _rg[1]
    HS = max(0.45, min(1.1, _rg[2] / 930.0))              # scale so the ridge lands where the painting has it
    hy = math.degrees(math.atan2(CAM[1] - HY, CAM[0] - HX)) - float(os.environ.get("LETHE_HOUSE_TURN", "50"))

    def hloc(dx, dy, dz):
        return local((HX, HY, 0.0), hy, dx * HS, dy * HS, dz * HS)

    def hbox(label, dx, dy, dz, size, mat, roll=0.0, pitch=0.0):
        return box(label, B, hloc(dx, dy, dz), tuple(s_ * HS for s_ in size), mat, rot=(roll, pitch, hy))

    hbox("House_Walls", 0, 0, 300, (600, 900, 600), mi_daub)
    hbox("House_Attic", 0, 0, 600, (440, 880, 440), mi_daub, pitch=45.0)          # fills the gables under the roof
    for dy_ in (-445, -225, 0, 225, 445):
        hbox("House_Stud", 304, dy_, 300, (14, 22, 600), mi_dark)
    for dz_ in (12, 300, 590):
        hbox("House_Rail", 303, 0, dz_, (14, 910, 20), mi_dark)
    for (dy_, dz_, s_) in ((-335, 150, 1), (335, 150, -1), (-112, 445, -1), (112, 445, 1)):
        hbox("House_Brace", 304, dy_, dz_, (12, 18, 300), mi_dark, roll=s_ * 35)
    hbox("House_Door", 302, -330, 105, (4, 100, 200), mi_dark)
    # the left gable end: a warm window high up, a lit doorway below
    for (lbl, dx_, dz_, w_, h_, lum) in (("House_GableWindow", 0, 700, 80, 95, 16), ("House_GableWindow2", -150, 330, 70, 90, 6),
                                          ("House_GableDoor", 150, 110, 95, 200, 10)):
        hbox(lbl, dx_, -452, dz_, (w_, 4, h_), m_win)
        hbox(lbl + "_Frame", dx_, -455, dz_, (6, 5, h_ + 4), mi_dark)
        hbox(lbl + "_Head", dx_, -455, dz_ + h_ / 2, (w_ + 10, 6, 8), mi_dark)
        point(lbl + "_Light", B, hloc(dx_, -520, dz_), lum, 2000, radius=420 * HS, source=25, vol=0.6)
    for (dx_, dz_) in ((-230, 300), (230, 300), (0, 12)):
        hbox("House_EndRail", dx_ * 0 + 0, -453, dz_, (600, 12, 18), mi_dark) if dx_ == 0 else None
    shingle_roof("House_Roof", B, hloc(0, 0, 930), hy, 1010 * HS, 480 * HS, 45.0, mi_thatch, course=30.0 * HS,
                 width=(45.0 * HS, 70.0 * HS), under=mi_thatch)
    for (cdy, ch_) in ((-250, 360), (290, 320)):                                       # two chimneys on the ridge
        hbox("House_Chimney", -30, cdy, 900 + ch_ / 2 - 120, (75, 75, ch_), mi_dark)
        hbox("House_ChimneyCap", -30, cdy, 900 + ch_ - 120 + 6, (92, 92, 12), mi_dark)
    log("house at (%.0f, %.0f) scale %.2f, ridge frame %s, gable window frame %s" % (HX, HY, HS, str(frame_of(*hloc(0, 0, 930))),
        str(frame_of(*hloc(0, -452, 700)))))

    for (lbl, fx_, fy_, dep) in (("FarLantern_L", 0.32, 0.215, 2100.0), ("FarLantern_R", 0.935, 0.245, 1750.0)):
        fl_ = at_frame(fx_, fy_, dep)
        place_between(lbl + "_Pole", "Lights", sm_l1, V(fl_[0], fl_[1], -20), V(fl_[0], fl_[1] + 1, fl_[2] + 30), 16, mi_dark)
        lantern(lbl, "Lights", (fl_[0] - 14, fl_[1], fl_[2]), 40, 30 if fx_ < 0.5 else 12, kelvin=2300, radius=600,
                vol=0.8 if fx_ < 0.5 else 0.2, flame=1.3)        # the right one dim: no glowing fog between house and post
        log("%s at %s" % (lbl, str(frame_of(*fl_))))

    # --- a barrel at the foot of the right palisade (spec x 0.81-0.85, y 0.67-0.80) ------------------
    mi_stave = ph_mi("MI_BarrelStave", "rough_wood", {"Wet": 0.45, "UVScale": 0.5}, {"Tint": (0.36, 0.32, 0.30)})
    bxx, byy, _ = at_frame_z(0.83, 0.79, 0.0)
    _, _, bdep = frame_of(bxx, byy, 0.0)
    log("barrel at (%.0f, %.0f), depth %.0f" % (bxx, byy, bdep))
    BR, BH = 29.0, 88.0
    for k in range(18):                                  # staves, bellied in the middle
        a_ = 2 * math.pi * k / 18 + rng.uniform(-0.03, 0.03)
        for (z0, z1, r0, r1) in ((0, BH / 2, BR * 0.88, BR), (BH / 2, BH, BR, BR * 0.88)):
            zc, rc = (z0 + z1) / 2, (r0 + r1) / 2
            tilt = math.degrees(math.atan2(r1 - r0, z1 - z0))
            box("Barrel_Stave", "Ground/Barrel", (bxx + math.cos(a_) * rc, byy + math.sin(a_) * rc, zc - 4),
                (2.4, 2 * math.pi * BR / 18 + 0.4, z1 - z0 + 0.5), mi_stave, rot=(0, -tilt, math.degrees(a_)))
    for zh in (8, 26, BH - 26, BH - 8):                  # iron hoops
        rr = BR * (0.9 + 0.1 * math.sin(math.pi * zh / BH)) + 1.6
        h_ = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(bxx, byy, zh - 4), unreal.Rotator(0, 0, 0))
        h_.static_mesh_component.set_static_mesh(CYL)
        h_.static_mesh_component.set_world_scale3d(V(rr * 2 / 100, rr * 2 / 100, 0.035))
        h_.static_mesh_component.set_material(0, m_iron)
        tag(h_, "Barrel_Hoop", "Ground/Barrel")
    lid = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(bxx, byy, BH - 6), unreal.Rotator(0, 0, 0))
    lid.static_mesh_component.set_static_mesh(CYL)
    lid.static_mesh_component.set_world_scale3d(V(BR * 1.8 / 100, BR * 1.8 / 100, 0.02))
    lid.static_mesh_component.set_material(0, mi_stave)
    tag(lid, "Barrel_Lid", "Ground/Barrel")

    # --- ground dressing: small sparse tufts at the stake feet; a few stones in the mud -----------
    PLANT_MI = {}

    def plant(kind, x, y_, sc):
        tx, ms = plants[kind]
        if not ms:
            return
        if kind not in PLANT_MI:
            PLANT_MI[kind] = mi("MI_Plant_" + kind, m_gr, None, {"Tint": (0.30, 0.27, 0.24)},
                                {"BaseColor": tx["bc"], "Opacity": tx["op"], "Normal": tx["n"], "Translucency": tx["tr"]})
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, -3), unreal.Rotator(rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(rng.choice(ms))
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
        for k in range(max(1, a.static_mesh_component.get_num_materials())):
            a.static_mesh_component.set_material(k, PLANT_MI[kind])
        tag(a, "Tuft_" + kind, "Ground/Plants")

    for (bx, by, bd) in BASES:
        if rng.random() < 0.3:
            nx, ny = (CAM[0] - bx), (CAM[1] - by)
            ln = math.hypot(nx, ny) or 1
            r_ = bd * 0.5 + rng.uniform(4, 16)
            plant(rng.choice(["grass", "grass", "weed"]), bx + nx / ln * r_, by + ny / ln * r_, rng.uniform(0.7, 1.3))

    rock_mis = [mi("MI_Rock_%d" % i, master, {"Wet": 0.5}, {"Tint": (0.55, 0.46, 0.42)},
                   {"BaseColor": tx["bc"], "Normal": tx["n"], "Roughness": tx["r"], "AO": tx["ao"]}) for i, (tx, _) in enumerate(rocks)]
    placed = 0
    while placed < int(os.environ.get("LETHE_ROCKS", "28")):
        fx_, fy_ = rng.uniform(-0.02, 1.02), rng.uniform(0.80, 1.02) ** 1.0         # the visible foreground mud
        if 0.60 < fx_ < 0.80 or (fx_ > 0.55 and rng.random() < 0.5):
            continue
        x, y_, _ = at_frame_z(fx_, fy_, 0.0)
        j = rng.randrange(len(rocks))
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, rng.uniform(-10, -3)),
                                          unreal.Rotator(rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(rocks[j][1])
        sc = rng.uniform(0.04, 0.09)
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
        for k in range(max(1, a.static_mesh_component.get_num_materials())):
            a.static_mesh_component.set_material(k, rock_mis[j])
        tag(a, "Rock", "Ground/Rocks")
        placed += 1

    # Ground decals: hand-placed puddles on the approach (they catch the gate lantern), mud patches, two cart ruts
    def ground_decal(label, mat, x, y_, length, width, yaw, depth=40):
        d_ = actors.spawn_actor_from_class(unreal.DecalActor, V(x, y_, 0), unreal.Rotator(0, -90, yaw))
        d_.decal.set_decal_material(mat)
        d_.decal.set_editor_property("decal_size", V(depth, width / 2, length / 2))
        tag(d_, label, "Ground/Decals")
    mi_pud = mi("MI_Puddle", m_pud)
    for (fx_, fy_, ln, wd) in ((0.38, 0.88, 240, 120), (0.45, 0.83, 260, 110), (0.22, 0.90, 180, 90),
                               (0.53, 0.86, 200, 100), (0.88, 0.90, 200, 100), (0.41, 0.80, 220, 90)):
        x, y_, _ = at_frame_z(fx_, fy_, 0.0)
        ground_decal("Puddle", mi_pud, x, y_, ln * 0.45, wd * 0.45, rng.uniform(0, 180))     # smaller: the camera is closer to the ground now
    mi_md = mi("MI_MudPatch", m_mdec)
    for _ in range(0):
        dist, brg = rng.uniform(150, 900), CAM_YAW + rng.uniform(-28, 26)
        ground_decal("MudPatch", mi_md, CAM[0] + math.cos(math.radians(brg)) * dist, CAM[1] + math.sin(math.radians(brg)) * dist,
                     rng.uniform(150, 280), rng.uniform(120, 220), rng.uniform(0, 360))
    for _ in range(0):                              # (Quixel mud decal: not used)
        dist, brg = rng.uniform(110, 520), CAM_YAW + rng.uniform(-30, -8)
        ground_decal("MudPatch", mi_md, CAM[0] + math.cos(math.radians(brg)) * dist, CAM[1] + math.sin(math.radians(brg)) * dist,
                     rng.uniform(110, 240), rng.uniform(90, 180), rng.uniform(0, 360))
    ry = math.degrees(math.atan2(20 - 430, 650 - 140))
    for off in ():
        nx_, ny_ = -math.sin(math.radians(ry)), math.cos(math.radians(ry))
        ground_decal("Rut", mi_md, 395 + nx_ * off, 225 + ny_ * off, 700, 34, ry + 90)

    # --- sky, moon, fog ---------------------------------------------------------------------------
    L = "Lighting"
    # The moon sits top left, behind the watchtower (frame x ~0.24, y ~0.10), half lost in thin cloud.
    def along(yaw, pitch, dist):
        cp = math.cos(math.radians(pitch))
        return (CAM[0] + dist * cp * math.cos(math.radians(yaw)), CAM[1] + dist * cp * math.sin(math.radians(yaw)),
                CAM[2] + dist * math.sin(math.radians(pitch)))
    MYAW, MPITCH = CAM_YAW - 1.8, CAM_PITCH + 14.3            # open sky above the gate (frame ~0.47, 0.06)
    mdir = (math.cos(math.radians(MPITCH)) * math.cos(math.radians(MYAW)), math.cos(math.radians(MPITCH)) * math.sin(math.radians(MYAW)),
            math.sin(math.radians(MPITCH)))
    m_sky = m_hdri_sky("M_SkyHDRI", sky_hdri, (0.0, 0.0, -1.0), float(os.environ.get("LETHE_SKY_YAW", "0.15")),
                       float(os.environ.get("LETHE_SKY_BRIGHT", "0.30")))
    sky = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(*CAM), unreal.Rotator(0, 0, 0))
    sky.static_mesh_component.set_static_mesh(SPHERE)
    sky.static_mesh_component.set_world_scale3d(V(4000, 4000, 4000))       # 2 km round the camera
    sky.static_mesh_component.set_material(0, m_sky)
    sky.static_mesh_component.set_editor_property("cast_shadow", False)
    tag(sky, "NightSky", L)

    # The moon, high behind the tower: backlights the fog cold blue-grey
    _, moon = light(unreal.DirectionalLight, "Moon", L, (0, 0, 2000), (0, -28, MYAW + 180.0 - 25.0))   # from the moon, behind-left
    safe_set(moon, "intensity", float(os.environ.get("LETHE_MOON", "0.7")))
    safe_set(moon, "use_temperature", True)
    safe_set(moon, "temperature", 10000.0)
    safe_set(moon, "volumetric_scattering_intensity", 0.25)
    safe_set(moon, "light_source_angle", 1.0)
    safe_set(moon, "cast_volumetric_shadow", False)

    # Overcast fill: a weak, shadowless cool light from the camera side, as the painting's soft night ambient
    _, ofill = light(unreal.DirectionalLight, "OvercastFill", L, (0, 0, 1800), (0, -40, CAM_YAW))
    safe_set(ofill, "intensity", float(os.environ.get("LETHE_FILL", "0.50")))
    safe_set(ofill, "light_color", unreal.Color(r=205, g=198, b=200, a=255))
    safe_set(ofill, "cast_shadows", False)
    safe_set(ofill, "volumetric_scattering_intensity", 0.0)
    safe_set(ofill, "specular_scale", 0.3)
    safe_set(ofill, "atmosphere_sun_light", False)
    _, skyl = light(unreal.SkyLight, "SkyFill", L, (0, 0, 1500))
    safe_set(skyl, "real_time_capture", True)              # the overcast sky lights the shadows
    safe_set(skyl, "intensity", 1.1)
    safe_set(skyl, "lower_hemisphere_color", unreal.LinearColor(0.025, 0.025, 0.030, 1))

    # Cool moonlit fill on the stripped panel: the pale wood is the brightest surface in the shot
    pf = (PX - 393.0, PY - 275.0, 430.0)
    fa, fl = light(unreal.SpotLight, "PanelMoonFill", P, pf)
    fa.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*pf), V(PX - 34 * fx, PY - 34 * fy, 115 - SINK)), False)
    safe_set(fl, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(fl, "intensity", float(os.environ.get("LETHE_POST_FILL", "28")))
    safe_set(fl, "use_temperature", True)
    safe_set(fl, "temperature", 8500.0)
    safe_set(fl, "inner_cone_angle", 8.0)
    safe_set(fl, "outer_cone_angle", 42.0)
    safe_set(fl, "attenuation_radius", 1600.0)
    safe_set(fl, "source_radius", 40.0)
    safe_set(fl, "volumetric_scattering_intensity", 0.0)
    rk = (PX - 52 * fx, PY - 52 * fy, 330.0 - SINK)
    rka, rkl = light(unreal.SpotLight, "CarveRake", P, rk)
    rka.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*rk), V(PX - 35 * fx, PY - 35 * fy, 187 - SINK)), False)
    safe_set(rkl, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(rkl, "intensity", float(os.environ.get("LETHE_RAKE", "1.0")))
    safe_set(rkl, "use_temperature", True)
    safe_set(rkl, "temperature", 6500.0)
    safe_set(rkl, "inner_cone_angle", 6.0)
    safe_set(rkl, "outer_cone_angle", 9.0)
    safe_set(rkl, "attenuation_radius", 400.0)
    safe_set(rkl, "source_radius", 1.0)
    safe_set(rkl, "volumetric_scattering_intensity", 0.0)

    # --- Nysa: "Free Medieval Assassin Girl" by Dimentrius3dArtist (Fab, CC BY 4.0), hood, mask and weapons removed,
    # posed by Scripts/nysa_pose.py (right arm raised with the lamp, left arm down), clothes and hair darkened, a long
    # coat skirt over the trousers. Back to camera, at the post.
    N = "Nysa"
    NYSA_HAND = None
    if not os.environ.get("LETHE_NO_NYSA") and os.environ.get("LETHE_NYSA_MH", "1") == "1":
        # Nysa as a MetaHuman (Scripts/make_nysa_mh.py builds BP_MH_Nysa; make_nysa_pose_anim.py makes her lamp pose).
        # MetaHumans face +Y in their own space, feet at the origin, real centimetres.
        pose = json.load(open("C:/LETHE/Saved/nysa_mh_pose.json"))
        nfx = float(os.environ.get("LETHE_NYSA_FX", "0.565"))
        ngap = float(os.environ.get("LETHE_NYSA_GAP", "88"))         # her root to the post's axis
        r_ = ray(nfx, 0.5)
        hn = math.hypot(r_[0], r_[1])
        best = None
        for k_ in range(1500):
            d_ = 100.0 + k_ * 0.5
            qx, qy = CAM[0] + d_ * r_[0] / hn, CAM[1] + d_ * r_[1] / hn
            e_ = abs(math.hypot(PX - qx, PY - qy) - ngap)
            if best is None or e_ < best[0] - 1e-6:
                best = (e_, qx, qy)
            if e_ < 1.0:
                break                                               # the near side of the post, not behind it
        NX, NY = best[1], best[2]
        nyaw = math.degrees(math.atan2(PY - NY, PX - NX)) + float(os.environ.get("LETHE_NYSA_TURN", "8"))
        fwx, fwy = unit(nyaw)
        rtx, rty = unit(nyaw + 90.0)
        nsc = float(os.environ.get("LETHE_NYSA_SCALE", "1.0"))
        myaw = nyaw - 90.0
        # A MetaHuman rebuild can leave its face anim blueprints without a skeleton; any blueprint with errors makes PIE
        # (and so the movie render) stop on a modal dialog. Repoint them to the face skeleton and recompile first.
        _fsk = unreal.load_asset("/Game/Lethe/MetaHumans/Common/Face/Face_Archetype_Skeleton")
        for _ad in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path("/Game/Lethe/MetaHumans", recursive=True):
            if str(_ad.asset_class_path.asset_name) != "AnimBlueprint":
                continue
            _abp = unreal.load_asset(str(_ad.package_name))
            if _abp.get_editor_property("target_skeleton") is None and _fsk:
                _abp.set_editor_property("target_skeleton", _fsk)
                unreal.BlueprintEditorLibrary.compile_blueprint(_abp)
                eal.save_loaded_asset(_abp, False)
                log("anim blueprint %s: skeleton restored, status %s" % (_ad.asset_name, _abp.get_editor_property("status")))
            if str(_abp.get_editor_property("status")).find("ERROR") >= 0:
                # still failing: use the skeleton of the pose asset its pose-blend node reads
                _opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
                _deps = unreal.AssetRegistryHelpers.get_asset_registry().get_dependencies(_ad.package_name, _opts) or []
                for _dp in _deps:
                    _da = unreal.load_asset(str(_dp)) if str(_dp).startswith("/Game") else None
                    if isinstance(_da, unreal.PoseAsset) and _da.get_editor_property("skeleton"):
                        _abp.set_editor_property("target_skeleton", _da.get_editor_property("skeleton"))
                        unreal.BlueprintEditorLibrary.compile_blueprint(_abp)
                        log("anim blueprint %s: skeleton from pose asset %s -> status %s" % (_ad.asset_name, _da.get_name(),
                                                                                           _abp.get_editor_property("status")))
                        break
                else:
                    log("anim blueprint %s still in error; deps %s" % (_ad.asset_name, [str(d_) for d_ in _deps][:12]))
                if str(_abp.get_editor_property("status")).find("ERROR") < 0:
                    eal.save_loaded_asset(_abp, False)
        bp_cls = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Lethe/MetaHumans/MH_Nysa/BP_MH_Nysa")
        mh = actors.spawn_actor_from_class(bp_cls, V(NX, NY, 0.0), unreal.Rotator(0, 0, myaw))
        mh.set_actor_scale3d(V(nsc, nsc, nsc))
        tag(mh, "Nysa_MH", N)
        seq = unreal.load_asset("/Game/Lethe/Characters/AS_Nysa_LampPose")
        body = [c_ for c_ in mh.get_components_by_class(unreal.SkeletalMeshComponent) if c_.get_name() == "Body"][0]
        body.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        body.set_animation(seq)
        ad = unreal.SingleAnimationPlayData()
        ad.set_editor_property("anim_to_play", seq)
        ad.set_editor_property("saved_playing", False)
        ad.set_editor_property("saved_position", 0.0)
        body.set_editor_property("animation_data", ad)
        body.set_position(0.0, False)
        mi_coat = m_cloth("M_Nysa_Coat", (0.030, 0.028, 0.032), 0.85, plaster_tx.get("BaseColor"), 0.3)

        def mh_world(p_):
            yr = math.radians(myaw)
            x_, y_ = p_[0] * nsc, p_[1] * nsc
            return (NX + x_ * math.cos(yr) - y_ * math.sin(yr), NY + x_ * math.sin(yr) + y_ * math.cos(yr), p_[2] * nsc)
        NYSA_HAND = mh_world(pose["hand_r"])
        s100 = nsc
        # her long coat with sleeves, belt, shoulder bag and strap (Scripts/make_nysa_coat.py, shaped to the lamp pose);
        # the MetaHuman's stock t-shirt and shorts are hidden under it
        cdir = ROOT + "/NysaCoat"
        if eal.does_directory_exist(cdir):
            eal.delete_directory(cdir)
        import_file(SRC + "/Nysa/coat/NysaCoat.obj", cdir)
        coat_parts = [a_ for a_ in (unreal.load_asset(p_) for p_ in eal.list_assets(cdir, recursive=True))
                      if isinstance(a_, unreal.StaticMesh)]
        if coat_parts:
            ylo_ = min(a_.get_bounding_box().min.y for a_ in coat_parts)
            yhi_ = max(a_.get_bounding_box().max.y for a_ in coat_parts)
            mir = -1.0 if yhi_ < -ylo_ else 1.0          # the importer may flip Y; the sleeves reach forward (+Y)
            log("coat: %d part(s), y %.1f..%.1f, mirror y %s" % (len(coat_parts), ylo_, yhi_, mir))
            mi_wool = m_cloth("M_Nysa_Wool", (0.034, 0.033, 0.040), 0.82, plaster_tx.get("BaseColor"), 0.25)
            mi_leather = m_cloth("M_Nysa_Leather", (0.075, 0.048, 0.032), 0.5, plaster_tx.get("BaseColor"), 0.0)
            for coat_sm in coat_parts:
                ca_ = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(NX, NY, 0.0), unreal.Rotator(0, 0, myaw))
                ca_.static_mesh_component.set_static_mesh(coat_sm)
                ca_.set_actor_scale3d(V(nsc, nsc * mir, nsc))
                for k_, slot in enumerate(coat_sm.static_materials):
                    nm_s = (str(slot.material_slot_name) + coat_sm.get_name()).lower()
                    ca_.static_mesh_component.set_material(k_, mi_leather if "leather" in nm_s else mi_wool)
                tag(ca_, "Nysa_Coat_" + coat_sm.get_name(), N)
        else:
            log("COAT IMPORT FAILED")
        for c_ in mh.get_components_by_class(unreal.SkeletalMeshComponent):
            if c_.get_name() == "SkeletalMesh":
                c_.set_visibility(False, False)
                c_.set_hidden_in_game(True, False)
        # her long dark ringlets: a groom generated by Scripts/make_nysa_curls.py (USD curves), replacing the MetaHuman's
        # straight hairstyle, in the same component space (so it stands where she does, turned as she is)
        if os.environ.get("LETHE_NYSA_CURLS", "1") == "1":
            hdir = ROOT + "/NysaCurls"
            usd_ = "C:/LETHE/SourceArt/Nysa/curls/NysaCurls.usda"
            stamp_ = "C:/LETHE/Saved/nysa_curls_imported.txt"
            need = not eal.does_directory_exist(hdir) or not os.path.exists(stamp_) or \
                open(stamp_).read().strip() != str(os.path.getmtime(usd_))
            if need:
                if eal.does_directory_exist(hdir):
                    eal.delete_directory(hdir)
                uopt = unreal.UsdStageImportOptions()
                for k_, v_ in (("import_actors", False), ("import_geometry", True), ("import_materials", False),
                               ("import_groom_assets", True), ("import_skeletal_animations", False), ("import_level_sequences", False)):
                    safe_set(uopt, k_, v_)
                ut = unreal.AssetImportTask()
                for k_, v_ in (("filename", usd_), ("destination_path", hdir), ("automated", True), ("save", True),
                               ("replace_existing", True), ("options", uopt)):
                    ut.set_editor_property(k_, v_)
                assets.import_asset_tasks([ut])
                open(stamp_, "w").write(str(os.path.getmtime(usd_)))
                log("curls imported")
            groom_ = next((a_ for a_ in (unreal.load_asset(p_) for p_ in eal.list_assets(hdir, recursive=True))
                           if isinstance(a_, unreal.GroomAsset)), None)
            if groom_:
                m_curls = m_hair_strands("M_Nysa_Curls", [float(x) for x in os.environ.get("LETHE_CURL_RGB", "0.045,0.027,0.018").split(",")])
                log("curl material: hair strands usage %s" % m_curls.get_editor_property("used_with_hair_strands"))
                # no simulation (it would let the curls sag flat during the render), and our material on the asset itself
                # (struct arrays come back as copies: modify, then set them back)
                try:
                    phs_ = groom_.get_editor_property("hair_groups_physics")
                    for ph_ in phs_:
                        ss_ = ph_.get_editor_property("solver_settings")
                        ss_.set_editor_property("enable_simulation", False)
                        ph_.set_editor_property("solver_settings", ss_)
                    groom_.set_editor_property("hair_groups_physics", phs_)
                except Exception as e_:  # noqa: BLE001
                    log("curls physics setting skipped: %s" % e_)
                try:
                    gms_ = groom_.get_editor_property("hair_groups_materials")
                    for gm_ in gms_:
                        gm_.set_editor_property("material", m_curls)
                    if not len(gms_):
                        gm_ = unreal.HairGroupsMaterial()
                        gm_.set_editor_property("material", m_curls)
                        gm_.set_editor_property("slot_name", "Hair")
                        gms_ = [gm_]
                    groom_.set_editor_property("hair_groups_materials", gms_)
                    rds_ = groom_.get_editor_property("hair_groups_rendering")
                    for rd_ in rds_:
                        rd_.set_editor_property("material_slot_name", gms_[0].get_editor_property("slot_name"))
                    groom_.set_editor_property("hair_groups_rendering", rds_)
                    eal.save_loaded_asset(groom_, False)
                    log("curl groom: %d material slot(s), simulation %s" % (len(gms_), [p_.get_editor_property("solver_settings").get_editor_property("enable_simulation") for p_ in groom_.get_editor_property("hair_groups_physics")]))
                except Exception as e_:  # noqa: BLE001
                    log("curls material setting failed: %s" % e_)
                ga_ = actors.spawn_actor_from_class(unreal.GroomActor, V(NX, NY, 0.0), unreal.Rotator(0, 0, myaw))
                gc_ = ga_.get_component_by_class(unreal.GroomComponent)
                gc_.set_editor_property("groom_asset", groom_)
                for k_ in range(max(1, gc_.get_num_materials())):
                    gc_.set_material(k_, m_curls)
                ga_.set_actor_scale3d(V(nsc, nsc, nsc))
                tag(ga_, "Nysa_Curls", N)
                for g_ in mh.get_components_by_class(unreal.GroomComponent):
                    if g_.get_name() == "Hair":
                        g_.set_visibility(False, False)
                        g_.set_hidden_in_game(True, False)
                o_, e_ = ga_.get_actor_bounds(False)
                log("curls groom placed: bounds centre %s, extent %s" % (o_, e_))
            else:
                log("CURLS IMPORT FAILED")
        # darker hair: find the groom material's melanin / redness and make an instance
        for g_ in mh.get_components_by_class(unreal.GroomComponent):
            if g_.get_name() != "Hair":
                continue
            for k_ in range(g_.get_num_materials()):
                m0 = g_.get_material(k_)
                if not m0:
                    continue
                # MetaHuman hair takes its colour from the "hairDye" vector: a deep, nearly black brown. The MetaHuman
                # component re-applies its own materials when play starts, so dye the built material instances themselves.
                if not isinstance(m0, unreal.MaterialInstanceConstant):
                    continue
                dye = [float(x) for x in os.environ.get("LETHE_HAIR_DYE", "0.035,0.020,0.013,1.0").split(",")]
                mel.set_material_instance_vector_parameter_value(m0, "hairDye", unreal.LinearColor(*dye))
                mel.update_material_instance(m0)
                eal.save_loaded_asset(m0, False)
                log("hair material %s dyed %s" % (m0.get_name(), dye))

        cfx, cfy = unit(CAM_YAW); clx, cly = unit(CAM_YAW - 90.0)
        rim_ = (NX + cfx * 130 + clx * 70, NY + cfy * 130 + cly * 70, 215.0)
        ra_, rl_ = light(unreal.SpotLight, "Nysa_Rim", N, rim_)
        ra_.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*rim_), V(NX, NY, 150.0 * s100)), False)
        safe_set(rl_, "intensity_units", unreal.LightUnits.LUMENS)
        safe_set(rl_, "intensity", float(os.environ.get("LETHE_NYSA_RIM", "7")))
        safe_set(rl_, "light_color", unreal.Color(r=205, g=200, b=220, a=255))
        safe_set(rl_, "outer_cone_angle", 22.0)
        safe_set(rl_, "attenuation_radius", 260.0)
        safe_set(rl_, "volumetric_scattering_intensity", 0.0)
        if os.environ.get("LETHE_NYSA_SKIRT", "0") == "1":
            cb = CONE.get_bounding_box()
            ch, cw = cb.max.z - cb.min.z, cb.max.x - cb.min.x
            top_, bot_, rb_ = 100.0 * s100, -2.0, 34.0 * s100
            szc = (top_ - bot_) / ch
            sk_c = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(NX - fwx * 2, NY - fwy * 2, bot_ - cb.min.z * szc), unreal.Rotator(0, 0, nyaw))
            sk_c.static_mesh_component.set_static_mesh(CONE)
            sk_c.static_mesh_component.set_world_scale3d(V(2 * rb_ * 0.80 / cw, 2 * rb_ / cw, szc))
            sk_c.static_mesh_component.set_material(0, mi_coat)
            tag(sk_c, "Nysa_CoatSkirt", N)
        lb = (NYSA_HAND[0] - fwx * 6, NYSA_HAND[1] - fwy * 6, NYSA_HAND[2] + 3)
        lf = (NYSA_HAND[0] + fwx * 7, NYSA_HAND[1] + fwy * 7, NYSA_HAND[2] + 4)
        place_between("Nysa_Lamp", N, CYL, V(*lb), V(*lf), 3.6, m_iron)
        place_between("Nysa_LampLens", N, CYL, V(*lf), V(lf[0] + fwx * 0.8, lf[1] + fwy * 0.8, lf[2]), 3.0, m_uvlens)
        if os.environ.get("LETHE_NYSA_MH", "1") == "1":
            # the lens's glow, just clear of her fingers and cuff: the bright violet point the painting shows
            gp_ = (lf[0] + fwx * 2.0, lf[1] + fwy * 2.0, lf[2] + 1.0)
            gl_a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(*gp_), unreal.Rotator(0, 0, 0))
            gl_a.static_mesh_component.set_static_mesh(SPHERE)
            gl_a.static_mesh_component.set_world_scale3d(V(0.026, 0.026, 0.026))
            gl_a.static_mesh_component.set_material(0, m_uvlens)
            gl_a.static_mesh_component.set_editor_property("cast_shadow", False)
            tag(gl_a, "Nysa_UVGlow", N)
            point("Nysa_UVGlowLight", N, gp_, 0.6, 12000, radius=60, source=1.0, vol=1.5, shadows=False)
        for a_ in [x for x in actors.get_all_level_actors() if x.get_actor_label().startswith("Nysa_Lamp")]:
            a_.static_mesh_component.set_editor_property("cast_shadow", False)
        log("nysa MH at (%.0f, %.0f) yaw %.0f, head frame %s, hand frame %s" % (NX, NY, nyaw,
            str(frame_of(*mh_world(pose["head"]))), str(frame_of(*NYSA_HAND))))
    elif not os.environ.get("LETHE_NO_NYSA"):
        ndir = ROOT + "/Nysa"
        if not [p_ for p_ in eal.list_assets(ndir, recursive=True)] if eal.does_directory_exist(ndir) else True:
            import_file(SRC + "/Nysa/gltf/NysaPosed.gltf", ndir)
        parts = [unreal.load_asset(p_) for p_ in eal.list_assets(ndir, recursive=True)]
        parts = [a_ for a_ in parts if isinstance(a_, unreal.StaticMesh)]
        info = json.load(open(SRC + "/Nysa/gltf/NysaPosed_info.json"))
        ntx = lambda f_, k_: tex("Nysa/gltf/textures", f_, k_)
        def nmat(slot, tint, rough_mult=1.0):
            nrm = ntx(slot + "_Normal.png", "normal")
            safe_set(nrm, "flip_green_channel", True)
            return m_char("M_Nysa_" + slot, ntx(slot + "_BaseColor.jpeg", "color"), nrm, ntx(slot + "_ORM.jpeg", "linear"), tint, rough_mult)
        nm_ = {"armor": nmat("M_armor", (0.17, 0.16, 0.18), 1.1), "hair": nmat("M_hair", (0.30, 0.20, 0.17), 0.9),
               "body": nmat("M_body1", (0.85, 0.80, 0.80), 1.0),
               "curl": m_curlcard("M_Nysa_Curls", ntx("M_curls_BaseColor.png", "color"), (2.6, 2.2, 2.0))}
        # measure the import: height, and which horizontal axis she faces along (the raised arm reaches forward)
        lo_ = [1e9] * 3; hi_ = [-1e9] * 3
        for a_ in parts:
            bb = a_.get_bounding_box()
            for k_, (u_, v_) in enumerate(((bb.min.x, bb.max.x), (bb.min.y, bb.max.y), (bb.min.z, bb.max.z))):
                lo_[k_] = min(lo_[k_], u_); hi_[k_] = max(hi_[k_], v_)
        hgt = hi_[2] - lo_[2]
        ax = 0 if abs(hi_[0] + lo_[0]) > abs(hi_[1] + lo_[1]) else 1
        sg = 1.0 if (hi_[ax] + lo_[ax]) > 0 else -1.0
        mesh_yaw = math.degrees(math.atan2(sg if ax == 1 else 0.0, sg if ax == 0 else 0.0))      # her forward, in mesh space
        log("nysa import: %d parts, bbox %s..%s, height %.0f, forward axis %s%d" % (len(parts), str([round(x, 1) for x in lo_]),
            str([round(x, 1) for x in hi_]), hgt, "+" if sg > 0 else "-", ax))
        nsc = float(os.environ.get("LETHE_NYSA_H", "180")) / max(1.0, hgt) * (info["hi"][1] - info["lo"][1]) / max(1.0, info["hi"][1] - info["lo"][1])
        nd = float(os.environ.get("LETHE_NYSA_DEPTH", "340"))
        nfx = float(os.environ.get("LETHE_NYSA_FX", "0.57"))
        r_ = ray(nfx, 0.5)
        hn = math.hypot(r_[0], r_[1])
        NX, NY = CAM[0] + nd * r_[0] / hn, CAM[1] + nd * r_[1] / hn
        hx_, hy_, hz_ = info["hand_r"]
        # face so the raised hand points at the word on the post (her hand is off to her right)
        nyaw = math.degrees(math.atan2(PY - NY, PX - NX)) + float(os.environ.get("LETHE_NYSA_TURN", "8"))
        fwx, fwy = unit(nyaw)
        rtx, rty = unit(nyaw + 90.0)
        nback = float(os.environ.get("LETHE_NYSA_BACK", "25"))      # step back so the lamp is clear of the bark
        NX, NY = NX - fwx * nback, NY - fwy * nback
        for a_ in parts:
            act = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(NX, NY, -lo_[2] * nsc), unreal.Rotator(0, 0, nyaw - mesh_yaw))
            c_ = act.static_mesh_component
            c_.set_static_mesh(a_)
            c_.set_world_scale3d(V(nsc, nsc, nsc))
            for k_, slot in enumerate(a_.static_materials):
                s_ = str(slot.material_slot_name).lower()
                c_.set_material(k_, nm_["curl"] if "curl" in s_ else nm_["hair"] if "hair" in s_ else nm_["body"] if "body" in s_ else nm_["armor"])
            tag(act, "Nysa_" + a_.get_name(), N)
        s100 = nsc * hgt / max(1.0, info["hi"][1] - info["lo"][1])          # glTF centimetres -> world
        NYSA_HAND = (NX + (fwx * hz_ - rtx * hx_) * s100, NY + (fwy * hz_ - rty * hx_) * s100, hy_ * s100)
        # warm rim from the gate lantern's side, behind her and to the left: catches the curls and her shoulder
        cfx, cfy = unit(CAM_YAW); clx, cly = unit(CAM_YAW - 90.0)
        rim_ = (NX + cfx * 130 + clx * 70, NY + cfy * 130 + cly * 70, 215.0)
        ra_, rl_ = light(unreal.SpotLight, "Nysa_Rim", N, rim_)
        ra_.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*rim_), V(NX, NY, 150.0 * s100)), False)
        safe_set(rl_, "intensity_units", unreal.LightUnits.LUMENS)
        safe_set(rl_, "intensity", float(os.environ.get("LETHE_NYSA_RIM", "22")))
        safe_set(rl_, "light_color", unreal.Color(r=255, g=168, b=105, a=255))
        safe_set(rl_, "outer_cone_angle", 22.0)
        safe_set(rl_, "attenuation_radius", 260.0)
        safe_set(rl_, "volumetric_scattering_intensity", 0.0)
        # a long dark coat skirt from the waist to the mud, over the trousers
        mi_coat = m_cloth("M_Nysa_Coat", (0.030, 0.028, 0.032), 0.85, plaster_tx.get("BaseColor"), 0.3)
        cb = CONE.get_bounding_box()
        ch, cw = cb.max.z - cb.min.z, cb.max.x - cb.min.x
        top_, bot_, rb_ = 150.0 * s100, -2.0, 36.0 * s100
        szc = (top_ - bot_) / ch
        sk_c = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(NX - fwx * 2, NY - fwy * 2, bot_ - cb.min.z * szc), unreal.Rotator(0, 0, nyaw))
        sk_c.static_mesh_component.set_static_mesh(CONE)
        sk_c.static_mesh_component.set_world_scale3d(V(2 * rb_ * 0.80 / cw, 2 * rb_ / cw, szc))
        sk_c.static_mesh_component.set_material(0, mi_coat)
        tag(sk_c, "Nysa_CoatSkirt", N)
        # the UV lamp in her hand
        lb = (NYSA_HAND[0] - fwx * 6, NYSA_HAND[1] - fwy * 6, NYSA_HAND[2] + 3)
        lf = (NYSA_HAND[0] + fwx * 7, NYSA_HAND[1] + fwy * 7, NYSA_HAND[2] + 4)
        place_between("Nysa_Lamp", N, CYL, V(*lb), V(*lf), 3.6, m_iron)
        place_between("Nysa_LampLens", N, CYL, V(*lf), V(lf[0] + fwx * 0.8, lf[1] + fwy * 0.8, lf[2]), 3.0, m_uvlens)
        for a_ in [x for x in actors.get_all_level_actors() if x.get_actor_label().startswith("Nysa_Lamp")]:
            a_.static_mesh_component.set_editor_property("cast_shadow", False)
        log("nysa at (%.0f, %.0f) yaw %.0f scale %.3f, head frame %s, hand frame %s" % (NX, NY, nyaw, nsc,
            str(frame_of(NX, NY, info["head"][1] * s100)), str(frame_of(*NYSA_HAND))))

    # Nysa's UV Lantern (from where she will stand): a tight violet pool on the post, no spill
    src = (CAM[0] + 300 * math.cos(math.radians(CAM_YAW + 8.5)), CAM[1] + 300 * math.sin(math.radians(CAM_YAW + 8.5)), 168.0 - SINK)
    if NYSA_HAND:
        # from the letters back toward her hand, at least 45 cm out, so the light never starts inside the bark
        tg_ = (PX - 38 * fx, PY - 38 * fy, 187.0 - SINK)
        dv_ = [h_ - t_ for h_, t_ in zip(NYSA_HAND, tg_)]
        dd_ = math.sqrt(sum(x * x for x in dv_))
        k_ = max(dd_, float(os.environ.get("LETHE_UV_STANDOFF", "90"))) / dd_
        if os.environ.get("LETHE_NYSA_MH", "1") == "1":
            k_ = max(0.2, (dd_ - 10.0) / dd_)               # the lens, 10 cm out from her hand toward the letters
        src = tuple(t_ + x * k_ for t_, x in zip(tg_, dv_))
        log("uv: hand %.0f cm from the letters, light at %s" % (dd_, str([round(x) for x in src])))
    uva, uv = light(unreal.SpotLight, "UVLantern", L, src)
    uva.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*src), V(PX - 38 * fx, PY - 38 * fy, 187 - SINK)), False)
    safe_set(uv, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(uv, "intensity", float(os.environ.get("LETHE_UV", "0.75")))
    safe_set(uv, "light_color", unreal.Color(r=112, g=72, b=232, a=255))
    safe_set(uv, "inner_cone_angle", 0.0)
    safe_set(uv, "outer_cone_angle", 30.0 if NYSA_HAND else 17.0)
    if NYSA_HAND:
        safe_set(uv, "cast_shadows", False)          # her own hand and sleeve sit right at the lamp
        safe_set(uv, "volumetric_scattering_intensity", float(os.environ.get("LETHE_UV_VOL", "6")))
    safe_set(uv, "attenuation_radius", 320.0)
    safe_set(uv, "volumetric_scattering_intensity", 0.1)
    safe_set(uv, "source_radius", 4.0)
    uva.set_actor_label("UVLantern")
    # Two weaker, slightly mis-aimed lobes of different widths around the main beam: a torch's lumpy, uneven edge,
    # a little brighter on the side it is held from. (An IES profile here came out aimed off the light's axis.)
    for k, (dz, dside, cone, share) in enumerate(((7.0, -9.0, 11.0, 0.45), (-6.0, 8.0, 19.0, 0.30))):
        sa, sl = light(unreal.SpotLight, "UVLantern_Lobe%d" % k, L, src)
        tgt = V(PX - 38 * fx - fy * dside, PY - 38 * fy + fx * dside, 180 - SINK + dz)
        sa.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*src), tgt), False)
        safe_set(sl, "intensity_units", unreal.LightUnits.LUMENS)
        safe_set(sl, "intensity", float(os.environ.get("LETHE_UV", "0.75")) * share)
        safe_set(sl, "light_color", unreal.Color(r=112, g=72, b=232, a=255))
        safe_set(sl, "inner_cone_angle", 0.0)
        safe_set(sl, "outer_cone_angle", cone * (1.7 if NYSA_HAND else 1.0))
        if NYSA_HAND:
            safe_set(sl, "cast_shadows", False)
        safe_set(sl, "attenuation_radius", 320.0)
        safe_set(sl, "source_radius", 4.0)
        safe_set(sl, "volumetric_scattering_intensity", 0.1)

    if NYSA_HAND and float(os.environ.get("LETHE_UV_SHAFT", "0.6")) > 0:
        # the beam's visible shaft from the lamp lens to the letters
        mi_beam = m_beam("M_UVBeam", (0.42, 0.26, 1.0), float(os.environ.get("LETHE_UV_SHAFT", "0.6")))
        lens_ = (NYSA_HAND[0] + fwx * 8, NYSA_HAND[1] + fwy * 8, NYSA_HAND[2] + 4)
        bl_ = math.sqrt(sum((a_ - b_) ** 2 for a_, b_ in zip(lens_, tg_)))
        bm = mi("MI_UVBeam", mi_beam, {"Length": bl_ * 0.93}, {"LampPos": lens_})
        ba = place_between("Nysa_UVBeam", N, CONE, V(*[l_ + (t_ - l_) * 0.93 for l_, t_ in zip(lens_, tg_)]), V(*lens_), 2 * bl_ * math.tan(math.radians(13)), bm)
        ba.static_mesh_component.set_editor_property("cast_shadow", False)
        log("uv beam: %.0f cm long" % bl_)

    wf = (250.0, -1500.0, 480.0)
    wfa, wfl = light(unreal.SpotLight, "WallFill", L, wf)
    wfa.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*wf), V(712, -700, 250)), False)
    safe_set(wfl, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(wfl, "intensity", float(os.environ.get("LETHE_WALL_FILL", "150")))
    safe_set(wfl, "use_temperature", True)
    safe_set(wfl, "temperature", 8000.0)
    safe_set(wfl, "inner_cone_angle", 15.0)
    safe_set(wfl, "outer_cone_angle", 45.0)
    safe_set(wfl, "attenuation_radius", 2500.0)
    safe_set(wfl, "source_radius", 80.0)
    safe_set(wfl, "volumetric_scattering_intensity", 0.0)
    _gt = at_frame_z(0.28, 0.90, 0.0)
    _gs = at_frame_z(0.36, 0.74, 0.0)
    _gs = (_gs[0], _gs[1], 260.0)
    _wt = at_frame_z(0.20, 0.88, 0.0)
    _ws = at_frame_z(0.28, 0.66, 0.0)                       # off to the left of Nysa, so it never lights her
    _ws = (_ws[0], _ws[1], 90.0)
    wga, wgl = light(unreal.SpotLight, "MudGlintWarm", L, _ws)
    wga.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*_ws), V(*_wt)), False)
    safe_set(wgl, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(wgl, "intensity", float(os.environ.get("LETHE_MUD_WARM", "28")))
    safe_set(wgl, "use_temperature", True)
    safe_set(wgl, "temperature", 2300.0)
    safe_set(wgl, "inner_cone_angle", 12.0)
    safe_set(wgl, "outer_cone_angle", 34.0)
    safe_set(wgl, "attenuation_radius", 1200.0)
    safe_set(wgl, "source_radius", 15.0)
    safe_set(wgl, "volumetric_scattering_intensity", 0.0)
    safe_set(wgl, "cast_shadows", True)
    ga, gl_ = light(unreal.SpotLight, "MudGlint", L, _gs)
    ga.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*_gs), V(*_gt)), False)
    safe_set(gl_, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(gl_, "intensity", float(os.environ.get("LETHE_MUD_GLINT", "90")))
    safe_set(gl_, "use_temperature", True)
    safe_set(gl_, "temperature", 7000.0)
    safe_set(gl_, "inner_cone_angle", 10.0)
    safe_set(gl_, "outer_cone_angle", 55.0)
    safe_set(gl_, "attenuation_radius", 1400.0)
    safe_set(gl_, "source_radius", 60.0)
    safe_set(gl_, "volumetric_scattering_intensity", 0.0)

    fog = actors.spawn_actor_from_class(unreal.ExponentialHeightFog, V(0, 0, 0), unreal.Rotator(0, 0, 0))
    fc = fog.component
    safe_set(fc, "fog_density", float(os.environ.get("LETHE_FOG", "0.040")))
    safe_set(fc, "fog_height_falloff", 25.0)             # dense on the ground, thin by tree-top height
    safe_set(fc, "fog_inscattering_luminance", unreal.LinearColor(0.052, 0.050, 0.056, 1))
    safe_set(fc, "enable_volumetric_fog", True)
    safe_set(fc, "volumetric_fog_albedo", unreal.Color(r=150, g=165, b=190, a=255))
    safe_set(fc, "volumetric_fog_emissive", unreal.LinearColor(0.016, 0.0165, 0.020, 1))
    safe_set(fc, "volumetric_fog_extinction_scale", 0.6)
    safe_set(fc, "volumetric_fog_scattering_distribution", 0.35)
    safe_set(fc, "volumetric_fog_distance", 8000.0)
    safe_set(fc, "fog_cutoff_distance", 9000.0)              # the sky, moon and cloud stay clear of the ground fog
    tag(fog, "NightFog", L)
    # Fir forest behind the settlement (Poly Haven fir_tree_01), thinning into the fog with distance
    fir_mats = {"bark": mi("MI_Fir_Bark", master, {"Wet": 0.3}, {"Tint": (0.45, 0.43, 0.42)}, fir_bark),
                "twig": mi("MI_Fir_Twig", m_gr, None, {"Tint": (0.30, 0.34, 0.30)},
                           {"BaseColor": fir_twig["bc"], "Opacity": fir_twig["op"], "Normal": fir_twig["n"], "Translucency": fir_twig["tr"]})}
    fbb = sm_fir.get_bounding_box()
    fir_h = max(1.0, fbb.max.z - fbb.min.z)
    placed = 0
    tries = 0
    for k in range(9):                                  # close firs behind the gate (spec: the gap is dark)
        brg = CAM_YAW + rng.uniform(-9, 5)
        dist = rng.uniform(1500, 2400)
        x, y_ = CAM[0] + math.cos(math.radians(brg)) * dist, CAM[1] + math.sin(math.radians(brg)) * dist
        sc = rng.uniform(1600, 2400) / fir_h
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, -30), unreal.Rotator(0, 0, rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(sm_fir)
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
        for kk, slot in enumerate(sm_fir.static_materials):
            nm = str(slot.material_slot_name).lower()
            a.static_mesh_component.set_material(kk, fir_mats["twig"] if ("twig" in nm or "leaf" in nm or "needle" in nm) else fir_mats["bark"])
        tag(a, "Fir", "Forest")
    while placed < 26 and tries < 2000:
        tries += 1
        brg = CAM_YAW + rng.uniform(-34, 30)
        dist = rng.uniform(2700, 7000)
        x, y_ = CAM[0] + math.cos(math.radians(brg)) * dist, CAM[1] + math.sin(math.radians(brg)) * dist
        if math.hypot(x - TX, y_ - TY) < 500 or math.hypot(x - HX, y_ - HY) < 800:
            continue
        if abs(brg - (-13.0)) < 10 and dist < 3800:
            continue
        if abs(brg - MYAW) < 6.0:
            continue
        h = rng.uniform(1300, 2400)
        sc = h / fir_h
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, -30), unreal.Rotator(rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(sm_fir)
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
        for k, slot in enumerate(sm_fir.static_materials):
            nm = str(slot.material_slot_name).lower()
            a.static_mesh_component.set_material(k, fir_mats["twig"] if ("twig" in nm or "leaf" in nm or "needle" in nm) else fir_mats["bark"])
        tag(a, "Fir", "Forest")
        placed += 1

    lfv_cls = unreal.load_class(None, "/Script/Engine.LocalFogVolume")
    if lfv_cls and not os.environ.get("LETHE_NOMIST"):   # low mist lying along the wall foot
        mist = []
        for (fx_, fy_, sx_, sz_) in ((0.04, 0.70, 6, 0.45), (0.17, 0.71, 5, 0.4), (0.30, 0.74, 4.5, 0.35), (0.44, 0.79, 4, 0.3),
                                     (0.10, 0.86, 4, 0.35), (0.27, 0.90, 3.5, 0.3), (0.52, 0.86, 3, 0.3)):
            gx, gy, _ = at_frame_z(fx_, fy_, 0.0)
            mist.append((gx, gy, sx_, sz_))
        for (x, y_, sx, sz) in tuple(mist) + ((760, -700, 12, 1.6), (1200, -200, 12, 1.6),
                                (2400, -1600, 22, 4.0), (3300, 300, 24, 5.0), (5200, -2600, 40, 9.0),
                                (300, -650, 9, 0.9)):                                           # + the low mist bank, left
            v = actors.spawn_actor_from_class(lfv_cls, V(x, y_, 0), unreal.Rotator(0, 0, 0))
            v.set_actor_scale3d(V(sx, sx, sz))
            ext = ((0.30 if frame_of(x, y_, 0.0)[0] < 0.3 else 0.15) if sx < 8 else 0.40 if sx < 11 else 0.10) if sx < 20 else 0.022  # rolling ground mist, low, thickest left
            for comp in v.get_components_by_class(unreal.LocalFogVolumeComponent):
                safe_set(comp, "radial_fog_extinction", ext)
                safe_set(comp, "height_fog_extinction", ext)
            tag(v, "GroundMist", L)
        # the painting's bright mist bank at the far left, lying on the wall foot
        for (fx_, fy_, sx_, sz_, ext_) in ((0.02, 0.63, 7.0, 0.95, 0.55), (0.12, 0.66, 6.0, 0.8, 0.45), (0.22, 0.70, 4.5, 0.55, 0.30)):
            gx, gy, _ = at_frame_z(fx_, fy_, 0.0)
            v = actors.spawn_actor_from_class(lfv_cls, V(gx, gy, 0), unreal.Rotator(0, 0, 0))
            v.set_actor_scale3d(V(sx_, sx_, sz_))
            for comp in v.get_components_by_class(unreal.LocalFogVolumeComponent):
                safe_set(comp, "radial_fog_extinction", ext_ * float(os.environ.get("LETHE_MIST_LEFT", "1.0")))
                safe_set(comp, "height_fog_extinction", ext_ * float(os.environ.get("LETHE_MIST_LEFT", "1.0")))
            tag(v, "GroundMist_Left", L)

    ppv = actors.spawn_actor_from_class(unreal.PostProcessVolume, V(0, 0, 0), unreal.Rotator(0, 0, 0))
    ppv.set_editor_property("unbound", True)
    s = ppv.settings
    for prop, val in (
        ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
        ("auto_exposure_apply_physical_camera_exposure", False),
        ("auto_exposure_bias", float(os.environ.get("LETHE_BEAUTY_EV", "0.0"))),
        ("bloom_intensity", 0.85),
        ("bloom_threshold", 0.8),
        ("vignette_intensity", 0.5),
        ("film_grain_intensity", 0.35),
        ("scene_fringe_intensity", 0.2),
        ("color_saturation", unreal.Vector4(0.74, 0.76, 0.82, 1.0)),
        ("color_contrast", unreal.Vector4(1.22, 1.22, 1.22, 1.0)),
        ("color_gain_shadows", unreal.Vector4(1.02, 0.98, 0.98, 1.0)),
        ("color_gain_midtones", unreal.Vector4(1.02, 0.99, 0.98, 1.0)),
        ("color_gain_highlights", unreal.Vector4(1.0, 1.0, 1.0, 1.0)),
        ("lumen_final_gather_quality", 4.0),
        ("lumen_scene_lighting_quality", 2.0),
        ("lumen_scene_detail", 2.0),
        ("lumen_reflection_quality", 2.0),
        ("motion_blur_amount", 0.0),
    ):
        if safe_set(s, "override_" + prop, True):
            safe_set(s, prop, val)
    ppv.set_editor_property("settings", s)
    tag(ppv, "Grade", L)

    # --- the camera: eye height, 35 mm, slight upward tilt -----------------------------------------
    cam = actors.spawn_actor_from_class(unreal.CineCameraActor, V(*CAM), unreal.Rotator(0, CAM_PITCH, CAM_YAW))
    if os.environ.get("LETHE_DEBUG_CAM") and NYSA_HAND:
        # close-up check of Nysa from behind her left shoulder (does not move anything else)
        dyaw = float(os.environ.get("LETHE_DEBUG_CAM"))
        bx_, by_ = unit(nyaw + 180.0 + dyaw)
        dloc = (NX + bx_ * 190.0, NY + by_ * 190.0, 125.0)
        cam.set_actor_location(V(*dloc), False, False)
        cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*dloc), V(NX + fwx * 15, NY + fwy * 15, 105.0)), False)
    cc = cam.get_cine_camera_component()
    fb = unreal.CameraFilmbackSettings()
    safe_set(fb, "sensor_width", 36.0)
    safe_set(fb, "sensor_height", 20.25)
    safe_set(cc, "filmback", fb)
    safe_set(cc, "current_focal_length", 35.0)
    safe_set(cc, "current_aperture", float(os.environ.get("LETHE_FSTOP", "2.8")))
    fs = unreal.CameraFocusSettings()
    safe_set(fs, "focus_method", unreal.CameraFocusMethod.MANUAL)
    safe_set(fs, "manual_focus_distance", 420.0)
    safe_set(cc, "focus_settings", fs)
    tag(cam, "BeautyCam", "Camera")

    levels.save_current_level()
    eal.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
    log("built " + MAP)
    return cam


def shoot(cam):
    os.makedirs(OUT, exist_ok=True)
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    try:
        levels.editor_set_game_view(True)
    except Exception:  # noqa: BLE001
        pass
    for cmd in ("t.IdleWhenNotForeground 0", "ShowFlag.BillboardSprites 0", "ShowFlag.Volumes 0", "ShowFlag.Selection 0", "ShowFlag.Grid 0",
                "r.VolumetricFog.GridPixelSize 4", "r.VolumetricFog.GridSizeZ 128",
                "r.Shadow.Virtual.ResolutionLodBiasLocal -1", "r.Streaming.PoolSize 8000", "r.Streaming.FullyLoadUsedTextures 1", "r.Tonemapper.Sharpen 0", "r.Lumen.ScreenProbeGather.ScreenSpaceBentNormal 1"):
        unreal.SystemLibrary.execute_console_command(w, cmd)
    tagname = os.environ.get("LETHE_SHOT_TAG", "v1")
    # Exposure bracket (manual EV bias); LETHE_BEAUTY_EVS="-2,-1,0" overrides.
    evs = [float(v) for v in os.environ.get("LETHE_BEAUTY_EVS", "-4,-2.5,-1,0.5,2").split(",")]
    ppv = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "Grade")
    queue = []
    for ev in evs:
        p = "%s/croatoan_gate_%s_ev%+.1f.png" % (OUT, tagname, ev)
        if os.path.exists(p):
            os.remove(p)
        queue.append((ev, p))
    uv_off_ev = os.environ.get("LETHE_UVOFF_EV")
    if uv_off_ev:
        p = "%s/croatoan_gate_%s_uvoff_ev%+.1f.png" % (OUT, tagname, float(uv_off_ev))
        if os.path.exists(p):
            os.remove(p)
        queue.append((float(uv_off_ev), p))
    uv_actors = [a for a in actors.get_all_level_actors() if a.get_actor_label().startswith("UVLantern")]
    insp_ev = os.environ.get("LETHE_INSPECT_EV")
    if insp_ev:
        p = "%s/croatoan_gate_%s_inspect_ev%+.1f.png" % (OUT, tagname, float(insp_ev))
        if os.path.exists(p):
            os.remove(p)
        queue.append((float(insp_ev), p))
    state = {"t0": time.time(), "i": 0, "phase": "warm", "busy": False, "handle": None, "at": 0.0}

    def set_ev(ev):
        s = ppv.settings
        s.set_editor_property("override_auto_exposure_bias", True)
        s.set_editor_property("auto_exposure_bias", ev)
        ppv.set_editor_property("settings", s)

    def tick(dt):
        if state["busy"]:
            return
        state["busy"] = True
        try:
            now = time.time()
            ph = state["phase"]
            if ph == "warm" and now - state["t0"] > 120:          # shaders, Lumen, fog history settle
                state["phase"] = "set"
            elif ph == "set":
                if state["i"] >= len(queue):
                    state["phase"] = "quit"
                    state["at"] = now
                else:
                    set_ev(queue[state["i"]][0])
                    if "_uvoff_" in queue[state["i"]][1]:
                        for ua in uv_actors:
                            ua.light_component.set_intensity(0.0)
                    if "_inspect_" in queue[state["i"]][1]:
                        cl = cam.get_actor_location()
                        ia = actors.spawn_actor_from_class(unreal.PointLight, V(cl.x, cl.y, cl.z + 40), unreal.Rotator(0, 0, 0))
                        ia.light_component.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
                        ia.light_component.set_intensity(3000.0)
                        ia.light_component.set_editor_property("attenuation_radius", 3000.0)
                    state["phase"] = "settle"
                    state["at"] = now
            elif ph == "settle" and now - state["at"] > 6:
                unreal.AutomationLibrary.take_high_res_screenshot(2560, 1440, queue[state["i"]][1], cam)
                state["phase"] = "wait"
                state["at"] = now
            elif ph == "wait":
                p = queue[state["i"]][1]
                if os.path.exists(p) or now - state["at"] > 900:
                    log("shot %s %s" % ("saved" if os.path.exists(p) else "MISSING", p))
                    state["i"] += 1
                    state["phase"] = "set"
            elif ph == "quit" and now - state["at"] > 3:
                unreal.unregister_slate_post_tick_callback(state["handle"])
                unreal.SystemLibrary.quit_editor()
        finally:
            state["busy"] = False

    state["handle"] = unreal.register_slate_post_tick_callback(tick)


def render_mrq(cam):
    """One cinematic still through Movie Render Queue: 64 warm-up frames for Lumen and the fog, 32 temporal samples."""
    seq_dir = "/Game/Lethe/Cinematics"
    if eal.does_asset_exist(seq_dir + "/LS_GateFull"):
        eal.delete_asset(seq_dir + "/LS_GateFull")
    seq = assets.create_asset("LS_GateFull", seq_dir, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(24, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(1)
    binding = seq.add_possessable(cam)
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack)
    sec = cut.add_section()
    sec.set_range(0, 1)
    try:
        bid = unreal.MovieSceneSequenceExtensions.get_portable_binding_id(seq, seq, binding)
    except Exception:  # noqa: BLE001
        bid = unreal.MovieSceneSequenceExtensions.get_binding_id(seq, binding)
    sec.set_camera_binding_id(bid)
    eal.save_loaded_asset(seq)
    levels.save_current_level()

    sub = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = sub.get_queue()
    q.delete_all_jobs()
    job = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.sequence = unreal.SoftObjectPath(seq.get_path_name())
    job.map = unreal.SoftObjectPath(MAP + "." + MAP.split("/")[-1])
    job.job_name = "GateFull"
    cfg = job.get_configuration()
    o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    o.output_resolution = unreal.IntPoint(2560, 1440)
    o.output_directory = unreal.DirectoryPath(OUT)
    o.file_name_format = "croatoan_gate_" + os.environ.get("LETHE_SHOT_TAG", "full") + "_mrq_{frame_number}"
    o.override_existing_output = True
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.override_anti_aliasing = True
    aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
    aa.spatial_sample_count = 1
    aa.temporal_sample_count = int(os.environ.get("LETHE_MRQ_SAMPLES", "32"))
    aa.render_warm_up_count = 64
    aa.engine_warm_up_count = 64
    cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
    for k, v in (("r.VolumetricFog.GridPixelSize", 4), ("r.VolumetricFog.GridSizeZ", 128), ("r.VolumetricFog.HistoryMissSupersampleCount", 16),
                 ("r.Lumen.ScreenProbeGather.ScreenSpaceBentNormal", 1), ("r.Shadow.Virtual.ResolutionLodBiasLocal", -1),
                 ("r.Tonemapper.Sharpen", 0.0), ("r.DepthOfFieldQuality", 4)):
        try:
            cv.add_or_update_console_variable(k, float(v))
        except Exception as e:  # noqa: BLE001
            unreal.log_warning("LETHE beauty: cvar %s: %s" % (k, e))
    state = {}

    def done(executor, success):
        log("mrq finished, success=%s" % success)
        unreal.SystemLibrary.quit_editor()

    ex = sub.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
    state["ex"] = ex
    if ex:
        ex.on_executor_finished_delegate.add_callable_unique(done)
    unreal._lethe_mrq_state = state
    log("mrq started")


if not getattr(unreal, "_lethe_beauty_started", False):
    unreal._lethe_beauty_started = True
    c = build()
    if os.environ.get("LETHE_MRQ"):
        st = {"t0": time.time(), "h": None}

        def go(dt):                                   # PIE cannot start while the editor is still loading
            if time.time() - st["t0"] > 45:
                unreal.unregister_slate_post_tick_callback(st["h"])
                render_mrq(c)
        st["h"] = unreal.register_slate_post_tick_callback(go)
        unreal._lethe_mrq_tick = st
    elif not os.environ.get("LETHE_BEAUTY_NOSHOOT"):
        shoot(c)
