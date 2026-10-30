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
    pale_col = mul(m, mul(m, lum, vparam(m, "PaleColor", (0.86, 0.70, 0.50), -800, -60), -650, -150), sparam(m, "PaleBright", 2.4, -650, -60), -500, -150)
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
    """Wet mud with puddles collecting in the low spots of the scan's displacement."""
    m = new_material("M_LetheMud")
    uv = mul(m, E(m, unreal.MaterialExpressionTextureCoordinate, -1600, 0), sparam(m, "UVScale", 16.0, -1600, 120), -1400, 0)
    bc = tparam(m, "BaseColor", d["bc"], SC.SAMPLERTYPE_COLOR, -1200, -300, uv)
    nm = tparam(m, "Normal", d["n"], SC.SAMPLERTYPE_NORMAL, -1200, 0, uv)
    ro = tparam(m, "Roughness", d["r"], SC.SAMPLERTYPE_MASKS, -1200, 250, uv)
    ds = tparam(m, "Height", d["h"], SC.SAMPLERTYPE_MASKS, -1200, 500, uv)
    # puddle = saturate((PuddleLevel - height) * Sharpness)
    sub = E(m, unreal.MaterialExpressionSubtract, -950, 500)
    link(sparam(m, "PuddleLevel", 0.38, -1100, 650), "", sub, "A")
    link(ds, "R", sub, "B")
    pud = E(m, unreal.MaterialExpressionSaturate, -650, 500)
    link(mul(m, sub, sparam(m, "PuddleSharpness", 14.0, -950, 650), -800, 500), "", pud, "")
    wetbase = mul(m, bc, sparam(m, "WetDarken", 0.55, -1000, -420), -900, -300, "RGB")
    base = lerp(m, wetbase, mul(m, wetbase, E(m, unreal.MaterialExpressionConstant, -900, -150, r=0.22), -750, -200), pud, -500, -300)
    to_prop(base, "", MP.MP_BASE_COLOR)
    r = mul(m, ro, sparam(m, "RoughnessMult", 0.7, -1000, 300), -900, 250, "R")
    to_prop(lerp(m, r, E(m, unreal.MaterialExpressionConstant, -700, 380, r=0.03), pud, -500, 250), "", MP.MP_ROUGHNESS)
    flat = E(m, unreal.MaterialExpressionConstant3Vector, -900, 120, constant=unreal.LinearColor(0, 0, 1, 1))
    to_prop(lerp(m, nm, flat, pud, -500, 0, "RGB"), "", MP.MP_NORMAL)
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
        guv = mul(m, E(m, unreal.MaterialExpressionTextureCoordinate, -1700, -400),
                  E(m, unreal.MaterialExpressionConstant2Vector, -1700, -320, r=1.5, g=6.0), -1500, -400)
        grain = tparam(m, "Grain", d["grain"], SC.SAMPLERTYPE_COLOR, -1300, -400, guv)
        lum = E(m, unreal.MaterialExpressionDotProduct, -1100, -500)
        link(grain, "RGB", lum, "A")
        link(E(m, unreal.MaterialExpressionConstant3Vector, -1300, -560, constant=unreal.LinearColor(0.3, 0.59, 0.11, 1)), "", lum, "B")
        pale = mul(m, mul(m, lum, vparam(m, "PaleColor", (0.80, 0.77, 0.72), -1100, -640), -950, -560),
                   sparam(m, "PaleBright", 1.9, -950, -660), -800, -560)
        cut_col = mul(m, grain, vparam(m, "CutColor", (0.16, 0.11, 0.08), -1100, -250), -950, -300, "RGB")
        cut_a = E(m, unreal.MaterialExpressionSaturate, -700, 0)
        link(mul(m, mask, sparam(m, "Depth", 2.6, -900, 120), -800, 0, "R"), "", cut_a, "")
        to_prop(lerp(m, pale, cut_col, cut_a, -550, -400), "", MP.MP_BASE_COLOR)
        to_prop(E(m, unreal.MaterialExpressionConstant, -700, -100, r=0.82), "", MP.MP_ROUGHNESS)
        op = E(m, unreal.MaterialExpressionMax, -500, 0)
        link(mask, "G", op, "A")
        link(cut_a, "", op, "B")
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
        dx = E(m, unreal.MaterialExpressionSubtract, -950, 700)
        link(mx, "R", dx, "A")
        link(m0, "R", dx, "B")
        dy = E(m, unreal.MaterialExpressionSubtract, -950, 850)
        link(my, "R", dy, "A")
        link(m0, "R", dy, "B")
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


def m_unlit(name, rgb, strength):
    m = new_material(name)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    to_prop(vparam(m, "Color", (rgb[0] * strength, rgb[1] * strength, rgb[2] * strength), -400, 0), "", MP.MP_EMISSIVE_COLOR)
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
    if tip and TIPS and rng.random() > 0.1:    # axe-hewn point: 4-6 uneven facets, apex off-centre
        dirv = unreal.Vector(top.x - x, top.y - y, top.z + sink)
        n = math.sqrt(dirv.x ** 2 + dirv.y ** 2 + dirv.z ** 2)
        ux, uy, uz = dirv.x / n, dirv.y / n, dirv.z / n
        th = dia * rng.uniform(1.1, 1.8)
        b0 = V(top.x - ux * 4, top.y - uy * 4, top.z - uz * 4)
        place_between(label + "_Tip", folder, rng.choice(TIPS), V(b0.x + ux * th, b0.y + uy * th, b0.z + uz * th), b0,
                      dia * 1.07, tip_mat or HEWN.get("mat") or mat, spin=rng.uniform(0, 360))
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

    plants = {
        "weeds": plant_set("curbside_weeds_ujzjfexja_high", "Curbside_Weeds_ujzjfexja_High_", "ujzjfexja", "ABCDEFGHIJK"),
        "nettle": plant_set("common_hemp_nettle_xh1kdfbqx_high", "Common_Hemp_Nettle_xh1kdfbqx_High_", "xh1kdfbqx", "ABCDEFG"),
        "dry": plant_set("dry_grass_tbbqejqr_high", "Dry_Grass_tbbqejqr_High_", "tbbqejqr", "ABCDE"),
        "wheat": plant_set("wheat_grass_tdcrdbur_high", "Wheat_Grass_tdcrdbur_High_", "tdcrdbur", "ABCDEF"),
        "shrubs": plant_set("dead_shrubs_vdknafgha_high", "Dead_Shrubs_vdknafgha_High_", "vdknafgha", "ABCDEFGH"),
    }
    rocks = [
        rock_set("small_stones_pack_vdjkbfmiw_high", "Small_Stones_Pack_vdjkbfmiw_High_", "Small_Stones_Pack_vdjkbfmiw_High.fbx", "SmallStones"),
        rock_set("military_trenches_scatter_rock_s_06_ydzrebd_high", "Military_Trenches_Scatter_Rock_S_06_ydzrebd_High_", "Military_Trenches_Scatter_Rock_S_06_ydzrebd_High.fbx", "Rock06"),
        rock_set("military_trenches_scatter_rock_s_03_ydzsbbr_high", "Military_Trenches_Scatter_Rock_S_03_ydzsbbr_High_", "Military_Trenches_Scatter_Rock_S_03_ydzsbbr_High.fbx", "Rock03"),
    ]

    log("materials")
    master = m_surface(t["l1"])
    mi_l1 = mi("MI_Log_A", master, {"Wet": 0.35}, {"Tint": (0.62, 0.62, 0.66)})
    mi_l2 = mi("MI_Log_B", master, {"Wet": 0.35}, {"Tint": (0.58, 0.58, 0.62)}, {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_dark = mi("MI_Log_Dark", master, {"Wet": 0.5}, {"Tint": (0.32, 0.31, 0.32)}, {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_post = mi("MI_Log_Stripped", master, {"Pale": 0.6, "PaleBright": 1.45, "Wet": 0.15, "UVScale": 1.0}, {"Tint": (1, 1, 1)},
                 {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_beam = mi("MI_Beam", master, {"Wet": 0.4}, {"Tint": (0.5, 0.48, 0.48)}, {"BaseColor": t["bm"]["bc"], "Normal": t["bm"]["n"], "Roughness": t["bm"]["r"], "AO": t["bm"]["ao"]})
    mi_rope = mi("MI_Rope", master, {"Wet": 0.3, "UVScale": 6.0}, {"Tint": (0.9, 0.78, 0.55)}, {"BaseColor": t["bm"]["bc"], "Normal": t["bm"]["n"], "Roughness": t["bm"]["r"], "AO": t["bm"]["ao"]})
    m_mud = m_ground(t["mud"])
    m_gr = m_foliage(t["gr"])
    m_carve = m_decal("M_CroatoanCarving", t["carve"], carving=True)
    m_mdec = m_decal("M_MudDecal", t["dec"])
    m_lamp = m_unlit("M_LanternGlass", (1.0, 0.62, 0.3), 5.0)
    m_win = m_unlit("M_WindowGlow", (1.0, 0.5, 0.18), 6.0)
    m_sky = m_unlit("M_NightSky", (0.030, 0.040, 0.056), 1.0)
    m_iron = mi("MI_IronDark", master, {"Wet": 0.6, "UVScale": 3.0}, {"Tint": (0.08, 0.08, 0.085)})

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
    mi_bark = mi("MI_Log_PostBark", master, {"Wet": 0.3}, {"Tint": (0.42, 0.42, 0.44)})
    HEWN["mat"] = mi("MI_Log_Hewn", master, {"Pale": 0.2, "PaleBright": 1.1, "Wet": 0.45}, {"Tint": (0.5, 0.5, 0.52)},
                     {"BaseColor": t["l2"]["bc"], "Normal": t["l2"]["n"], "Roughness": t["l2"]["r"], "AO": t["l2"]["ao"]})
    mi_daub = mi("MI_Daub", master, {"Wet": 0.2, "UVScale": 3.0}, {"Tint": (0.30, 0.30, 0.31)},
                 {"BaseColor": t["bm"]["bc"], "Normal": t["bm"]["n"], "Roughness": t["bm"]["r"], "AO": t["bm"]["ao"]})

    CAM = (-143.0, 621.0, 160.0)
    CAM_YAW, CAM_PITCH = -35.0, 3.5

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

    def lash_at(cx, cy, cz, ux, uy, folder, dia=22.0):
        """Three turns of rope binding a rail to a trunk, wound diagonally across the rail."""
        for k in range(3):
            o = (k - 1) * 6.0
            place_between("Lashing", folder, sm_bm, V(cx - ux * 10 + ux * o, cy - uy * 10 + uy * o, cz - dia * 0.6),
                          V(cx + ux * 10 + ux * o, cy + uy * 10 + uy * o, cz + dia * 0.6), 2.6, mi_rope, spin=rng.uniform(0, 360))

    def curtain(label, x0, y0, yaw, length, hgt, dia, lean_out, rail_z, rail_every=2):
        """Whole trunks set tight along a line; uneven height, girth and lean; rails lashed on the outer face."""
        ux, uy = unit(yaw)
        nx, ny = toward_cam(x0, y0, ux, uy)
        s, stakes = 0.0, []
        dmax = dia[1]
        while s < length:
            sm_, mt = logs[rng.randrange(2)]
            d = rng.uniform(*dia)
            px, py = x0 + ux * s + nx * rng.uniform(-6, 6), y0 + uy * s + ny * rng.uniform(-6, 6)
            lo = lean_out + rng.uniform(-2.5, 2.5)
            side = rng.uniform(-2.5, 2.5)
            upright(label, "Palisade", sm_, px, py, rng.uniform(*hgt), d, mt,
                    lean_x=nx * lo + ux * side, lean_y=ny * lo + uy * side)
            stakes.append((s, d))
            s += d * rng.uniform(0.82, 0.92)
        off = dmax * 0.5 + 9
        for z in rail_z:
            zz = z + rng.uniform(-8, 8)
            place_between(label + "_Rail", "Palisade", sm_l1, V(x0 + nx * off - ux * 30, y0 + ny * off - uy * 30, zz),
                          V(x0 + nx * off + ux * (length + 30), y0 + ny * off + uy * (length + 30), zz + rng.uniform(-14, 14)), 19, mi_dark)
            for i, (ss, d) in enumerate(stakes):
                if i % rail_every == 0:
                    lash_at(x0 + ux * ss + nx * (off + 2), y0 + uy * ss + ny * (off + 2), zz, ux, uy, "Palisade")

    logs = [(sm_l1, mi_dark), (sm_l2, mi_l1)]

    # Ground: dark wet mud, puddles in the low spots of the scan
    g = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(1500, 0, 0), unreal.Rotator(0, 0, 0))
    g.static_mesh_component.set_static_mesh(PLANE)
    g.static_mesh_component.set_world_scale3d(V(80, 80, 1))
    g.static_mesh_component.set_material(0, mi("MI_Mud", m_mud, {"UVScale": 22.0, "PuddleLevel": 0.47, "PuddleSharpness": 10.0,
                                                               "WetDarken": 0.42, "RoughnessMult": 0.55}))
    tag(g, "Ground_Mud", "Ground")

    # --- the CROATOAN post: right-hand post of the entrance, a great trunk with its bark taken off in front
    P = "CroatoanPost"
    PX, PY = 290.0, 437.0
    place_between("CROATOAN_Post", P, sm_l2, V(PX, PY, -60), V(PX + 4, PY - 3, 690), 76, mi_bark, spin=40)
    face = -18.0                                      # the panel faces the approach, a little toward Nysa's lantern
    fx, fy = unit(face)
    dec = actors.spawn_actor_from_class(unreal.DecalActor, V(PX - 60 * fx, PY - 60 * fy, 210), unreal.Rotator(90, 0, face))
    dec.decal.set_decal_material(mi("MI_CroatoanCarving", m_carve))
    dec.decal.set_editor_property("decal_size", V(45, 200, 50))   # depth, height 4 m (z 10-410), width 1 m
    tag(dec, "CROATOAN_Panel", P)

    # --- the entrance: left gatepost, a dark trunk beside the CROATOAN post, and a lashed gate between
    G = "Gate"
    place_between("GatePost_L", G, sm_l2, V(705, -95, -60), V(708, -96, 640), 62, mi_dark, spin=120)
    upright("GateTrunk", G, sm_l1, 712, 72, 650, 54, mi_dark, lean_x=-1.0, lean_y=0.5)
    vy = -66.0
    while vy < 40:                                    # the gate leaf: upright poles
        d = rng.uniform(17, 23)
        upright("GatePole", G, logs[rng.randrange(2)][0], 726 + rng.uniform(-3, 3), vy, rng.uniform(285, 320), d, mi_dark,
                lean_y=rng.uniform(-1.5, 1.5))
        vy += d * rng.uniform(1.05, 1.2)
    for z in (95, 232):                               # crossbars on the outer face, roped to every pole
        zz = z + rng.uniform(-6, 6)
        place_between("GateBar", G, sm_l1, V(704, -118, zz), V(704, 64, zz + rng.uniform(-8, 8)), 22, mi_beam)
        for yy in range(-60, 50, 24):
            lash_at(700, yy, zz, 0.0, 1.0, G)
    for z in (440, 492):                              # heavy lintel logs up top, behind the posts
        place_between("GateLintel", G, sm_l2, V(722, -135, z), V(722, 120, z + rng.uniform(-10, 10)), 32, mi_dark)
    # A lantern hung on the gate
    lx, ly, lz = 690.0, 0.0, 214.0
    place_between("GateLantern_Hook", G, sm_bm, V(lx, ly, lz + 18), V(lx, ly, lz + 40), 1.6, m_iron)
    box("GateLantern_Cap", G, (lx, ly, lz + 16), (17, 17, 4), m_iron)
    box("GateLantern_Glass", G, (lx, ly, lz), (12, 12, 24), m_lamp)
    box("GateLantern_Base", G, (lx, ly, lz - 14), (17, 17, 4), m_iron)
    point("GateLantern_Light", G, (lx - 14, ly, lz), 160, 2200, radius=900, source=3, vol=0.45)

    # --- the palisade -------------------------------------------------------------------------
    curtain("Trunk_L", 715, -150, -90, 1700, (370, 470), (30, 48), 5.0, (135, 330))      # recedes to the left
    curtain("Trunk_R", 765, 162, 50, 420, (215, 280), (26, 38), 1.5, (120,), rail_every=1)   # behind the post, right

    # --- the watchtower, top left: legs, platform, railed walk, shingled pitched roof, a lantern
    T = "Watchtower"
    TX, TY = 1140.0, -1010.0
    legs = [(-170, -170), (170, -170), (-170, 170), (170, 170)]
    for (ox, oy) in legs:
        place_between("Tower_Leg", T, sm_l2, V(TX + ox, TY + oy, -40), V(TX + ox * 0.94, TY + oy * 0.94, 640), 30, mi_dark)
    for (a_, b_) in ((legs[0], legs[3]), (legs[1], legs[2])):        # cross braces under the platform
        place_between("Tower_Brace", T, sm_bm, V(TX + a_[0], TY + a_[1], 80), V(TX + b_[0], TY + b_[1], 440), 14, mi_dark)
    box("Tower_Floor", T, (TX, TY, 450), (380, 380, 16), mi_beam)
    for zz in (495, 545):                                            # rails round the walk
        for (a_, b_) in ((legs[0], legs[1]), (legs[1], legs[3]), (legs[3], legs[2]), (legs[2], legs[0])):
            place_between("Tower_Rail", T, sm_bm, V(TX + a_[0], TY + a_[1], zz), V(TX + b_[0], TY + b_[1], zz + rng.uniform(-4, 4)), 10, mi_beam)
    # Shingled gable roof, ridge running along X; rows of overlapping boards, each a little askew
    eave, ridge, half = 640.0, 760.0, 230.0
    slope = math.degrees(math.atan2(ridge - eave, half))
    for side in (-1, 1):
        for row in range(7):
            f = (row + 0.5) / 7
            yy = TY + side * half * f
            zz = ridge - (ridge - eave) * f + 2
            for k in range(6):
                bx = TX - 250 + (k + 0.5) * (500 / 6) + rng.uniform(-6, 6)
                box("Tower_Shingle", T, (bx, yy, zz), (500 / 6 + 4, (half / 7) * 1.5 / math.cos(math.radians(slope)), 4), mi_dark,
                    rot=(side * slope + rng.uniform(-2, 2), rng.uniform(-1.5, 1.5), rng.uniform(-2, 2)))
    place_between("Tower_Ridge", T, sm_bm, V(TX - 260, TY, ridge + 4), V(TX + 260, TY, ridge + 4), 16, mi_dark)
    wl = (TX - 150, TY + 150, 520)
    box("Tower_Lamp", T, wl, (14, 14, 22), m_lamp)
    point("Tower_LampLight", T, wl, 220, 2200, radius=1100, source=4, vol=0.6)

    # --- the house behind, top right: timber frame, chimney, two lit windows, softened by the fog
    B = "House"
    HX, HY, HZ = 2195.0, 81.0, 60.0
    hy = math.degrees(math.atan2(CAM[1] - HY, CAM[0] - HX))         # local +X faces the camera

    def hloc(dx, dy, dz):
        return local((HX, HY, HZ), hy, dx, dy, dz)

    def hbox(label, dx, dy, dz, size, mat, roll=0.0, pitch=0.0):
        return box(label, B, hloc(dx, dy, dz), size, mat, rot=(roll, pitch, hy))

    hbox("House_Walls", 0, 0, 300, (600, 900, 600), mi_daub)
    for dy_ in (-445, -225, 0, 225, 445):
        hbox("House_Stud", 303, dy_, 300, (14, 22, 600), mi_dark)
    for dz_ in (12, 300, 590):
        hbox("House_Rail", 303, 0, dz_, (14, 910, 20), mi_dark)
    for (dy_, dz_, s_) in ((-335, 150, 1), (335, 150, -1), (-112, 445, -1), (112, 445, 1)):
        hbox("House_Brace", 304, dy_, dz_, (12, 18, 300), mi_dark, roll=s_ * 35)
    for (dy_, dz_) in ((-150, 430), (190, 430)):                      # the two warm windows, upper floor
        hbox("House_Window", 302, dy_, dz_, (4, 90, 110), m_win)
        hbox("House_Mullion", 305, dy_, dz_, (5, 6, 112), mi_dark)
        hbox("House_Transom", 305, dy_, dz_ + 10, (5, 92, 6), mi_dark)
        point("House_WindowLight", B, hloc(330, dy_, dz_), 90, 2000, radius=600, source=30, vol=0.15)
    hbox("House_Door", 302, -330, 105, (4, 100, 200), mi_dark)
    for side in (-1, 1):                                               # steep dark roof, ridge along the front
        hbox("House_Roof", side * 160, 0, 760, (470, 980, 22), mi_dark, pitch=-side * 42)
    hbox("House_Chimney", -90, 330, 760, (90, 90, 300), mi_dark)
    hbox("House_ChimneyCap", -90, 330, 915, (110, 110, 14), mi_dark)

    # --- ground dressing: small sparse tufts at the stake feet; a few stones in the mud -----------
    PLANT_MI = {}

    def plant(kind, x, y_, sc):
        tx, ms = plants[kind]
        if not ms:
            return
        if kind not in PLANT_MI:
            PLANT_MI[kind] = mi("MI_Plant_" + kind, m_gr, None, {"Tint": (0.40, 0.42, 0.40)},
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
            plant(rng.choice(["dry", "weeds", "wheat"]), bx + nx / ln * r_, by + ny / ln * r_, rng.uniform(0.28, 0.5))

    rock_mis = [mi("MI_Rock_%d" % i, master, {"Wet": 0.7}, {"Tint": (0.42, 0.43, 0.46)},
                   {"BaseColor": tx["bc"], "Normal": tx["n"], "Roughness": tx["r"], "AO": tx["ao"]}) for i, (tx, _) in enumerate(rocks)]
    placed = 0
    while placed < int(os.environ.get("LETHE_ROCKS", "26")):
        dist, brg = rng.uniform(170, 520), CAM_YAW + rng.uniform(-30, 2)      # left and centre foreground only
        x, y_ = CAM[0] + math.cos(math.radians(brg)) * dist, CAM[1] + math.sin(math.radians(brg)) * dist
        if x > PX - 60:
            continue
        j = rng.randrange(len(rocks))
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, rng.uniform(-10, -3)),
                                          unreal.Rotator(rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(rocks[j][1])
        sc = rng.uniform(0.5, 1.2) if j else rng.uniform(0.6, 0.9)
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
        for k in range(max(1, a.static_mesh_component.get_num_materials())):
            a.static_mesh_component.set_material(k, rock_mis[j])
        tag(a, "Rock", "Ground/Rocks")
        placed += 1

    # --- sky, moon, fog ---------------------------------------------------------------------------
    L = "Lighting"
    sky = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(9000, -4000, 1500), unreal.Rotator(0, 90, 0))
    sky.static_mesh_component.set_static_mesh(PLANE)
    sky.static_mesh_component.set_world_scale3d(V(500, 500, 1))
    sky.static_mesh_component.set_material(0, m_sky)
    sky.static_mesh_component.set_editor_property("cast_shadow", False)
    tag(sky, "NightSky", L)

    # The moon, high behind the tower: backlights the fog cold blue-grey
    _, moon = light(unreal.DirectionalLight, "Moon", L, (0, 0, 2000), (0, -38, 150))
    safe_set(moon, "intensity", float(os.environ.get("LETHE_MOON", "2.2")))
    safe_set(moon, "use_temperature", True)
    safe_set(moon, "temperature", 10000.0)
    safe_set(moon, "volumetric_scattering_intensity", 0.7)
    safe_set(moon, "light_source_angle", 1.0)

    _, skyl = light(unreal.SkyLight, "SkyFill", L, (0, 0, 1500))
    safe_set(skyl, "real_time_capture", False)
    safe_set(skyl, "intensity", 0.8)
    safe_set(skyl, "lower_hemisphere_color", unreal.LinearColor(0.004, 0.005, 0.007, 1))

    # Cool moonlit fill on the stripped panel: the pale wood is the brightest surface in the shot
    pf = (PX - 370.0, PY - 480.0, 560.0)
    fa, fl = light(unreal.SpotLight, "PanelMoonFill", P, pf)
    fa.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*pf), V(PX - 34 * fx, PY - 34 * fy, 200)), False)
    safe_set(fl, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(fl, "intensity", float(os.environ.get("LETHE_POST_FILL", "260")))
    safe_set(fl, "use_temperature", True)
    safe_set(fl, "temperature", 8500.0)
    safe_set(fl, "inner_cone_angle", 8.0)
    safe_set(fl, "outer_cone_angle", 20.0)
    safe_set(fl, "attenuation_radius", 1600.0)
    safe_set(fl, "source_radius", 40.0)
    safe_set(fl, "volumetric_scattering_intensity", 0.0)

    # Nysa's UV Lantern (from where she will stand): a tight violet pool on the post, no spill
    src = (PX + 150 * math.cos(math.radians(200)), PY + 150 * math.sin(math.radians(200)), 145.0)
    uva, uv = light(unreal.SpotLight, "UVLantern", L, src)
    uva.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(*src), V(PX - 36 * fx, PY - 36 * fy, 150)), False)
    safe_set(uv, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(uv, "intensity", float(os.environ.get("LETHE_UV", "120")))
    safe_set(uv, "light_color", unreal.Color(r=95, g=60, b=255, a=255))
    safe_set(uv, "inner_cone_angle", 3.0)
    safe_set(uv, "outer_cone_angle", 15.0)
    safe_set(uv, "attenuation_radius", 320.0)
    safe_set(uv, "volumetric_scattering_intensity", 0.1)
    safe_set(uv, "source_radius", 1.5)

    fog = actors.spawn_actor_from_class(unreal.ExponentialHeightFog, V(0, 0, 0), unreal.Rotator(0, 0, 0))
    fc = fog.component
    safe_set(fc, "fog_density", float(os.environ.get("LETHE_FOG", "0.03")))
    safe_set(fc, "fog_height_falloff", 0.28)
    safe_set(fc, "fog_inscattering_luminance", unreal.LinearColor(0.010, 0.013, 0.019, 1))
    safe_set(fc, "enable_volumetric_fog", True)
    safe_set(fc, "volumetric_fog_albedo", unreal.Color(r=150, g=165, b=190, a=255))
    safe_set(fc, "volumetric_fog_emissive", unreal.LinearColor(0.0012, 0.0015, 0.0021, 1))
    safe_set(fc, "volumetric_fog_extinction_scale", 1.0)
    safe_set(fc, "volumetric_fog_scattering_distribution", 0.35)
    safe_set(fc, "volumetric_fog_distance", 8000.0)
    tag(fog, "NightFog", L)
    lfv_cls = unreal.load_class(None, "/Script/Engine.LocalFogVolume")
    if lfv_cls:                                    # low mist lying along the wall foot
        for (x, y_) in ((760, -700), (780, 400), (1200, -200)):
            v = actors.spawn_actor_from_class(lfv_cls, V(x, y_, 0), unreal.Rotator(0, 0, 0))
            v.set_actor_scale3d(V(12, 12, 1.6))
            tag(v, "GroundMist", L)

    ppv = actors.spawn_actor_from_class(unreal.PostProcessVolume, V(0, 0, 0), unreal.Rotator(0, 0, 0))
    ppv.set_editor_property("unbound", True)
    s = ppv.settings
    for prop, val in (
        ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
        ("auto_exposure_apply_physical_camera_exposure", False),
        ("auto_exposure_bias", float(os.environ.get("LETHE_BEAUTY_EV", "0.0"))),
        ("bloom_intensity", 0.6),
        ("bloom_threshold", 1.0),
        ("vignette_intensity", 0.5),
        ("film_grain_intensity", 0.15),
        ("scene_fringe_intensity", 0.2),
        ("color_saturation", unreal.Vector4(0.74, 0.76, 0.82, 1.0)),
        ("color_contrast", unreal.Vector4(1.1, 1.1, 1.1, 1.0)),
        ("color_gain_shadows", unreal.Vector4(0.86, 0.94, 1.12, 1.0)),
        ("color_gain_midtones", unreal.Vector4(0.95, 0.98, 1.04, 1.0)),
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
    cc = cam.get_cine_camera_component()
    fb = unreal.CameraFilmbackSettings()
    safe_set(fb, "sensor_width", 36.0)
    safe_set(fb, "sensor_height", 20.25)
    safe_set(cc, "filmback", fb)
    safe_set(cc, "current_focal_length", 35.0)
    safe_set(cc, "current_aperture", 4.0)
    fs = unreal.CameraFocusSettings()
    safe_set(fs, "focus_method", unreal.CameraFocusMethod.MANUAL)
    safe_set(fs, "manual_focus_distance", 470.0)
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
                "r.Shadow.Virtual.ResolutionLodBiasLocal -1", "r.Streaming.PoolSize 8000", "r.Streaming.FullyLoadUsedTextures 1", "r.Tonemapper.Sharpen 0.6", "r.Lumen.ScreenProbeGather.ScreenSpaceBentNormal 1"):
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
                    state["phase"] = "settle"
                    state["at"] = now
            elif ph == "settle" and now - state["at"] > 6:
                unreal.AutomationLibrary.take_high_res_screenshot(2560, 1440, queue[state["i"]][1], cam)
                state["phase"] = "wait"
                state["at"] = now
            elif ph == "wait":
                p = queue[state["i"]][1]
                if os.path.exists(p) or now - state["at"] > 300:
                    log("shot %s %s" % ("saved" if os.path.exists(p) else "MISSING", p))
                    state["i"] += 1
                    state["phase"] = "set"
            elif ph == "quit" and now - state["at"] > 3:
                unreal.unregister_slate_post_tick_callback(state["handle"])
                unreal.SystemLibrary.quit_editor()
        finally:
            state["busy"] = False

    state["handle"] = unreal.register_slate_post_tick_callback(tick)


if not getattr(unreal, "_lethe_beauty_started", False):
    unreal._lethe_beauty_started = True
    c = build()
    if not os.environ.get("LETHE_BEAUTY_NOSHOOT"):
        shoot(c)
