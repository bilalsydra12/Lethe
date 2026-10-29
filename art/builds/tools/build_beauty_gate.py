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
        mask = tparam(m, "Mask", d["mask"], SC.SAMPLERTYPE_MASKS, -1000, 0)
        # Cut wood: dark in the groove; the deep CROATOAN cut fully opaque, later scratches fainter.
        # Inside the cut: the same wood, darkened, so its grain still shows in the groove.
        grain = tparam(m, "Grain", d["grain"], SC.SAMPLERTYPE_COLOR, -1200, -400,
                       mul(m, E(m, unreal.MaterialExpressionTextureCoordinate, -1500, -400), sparam(m, "GrainScale", 0.5, -1500, -320), -1350, -400))
        to_prop(mul(m, grain, vparam(m, "CutColor", (0.16, 0.11, 0.08), -900, -250), -700, -300, "RGB"), "", MP.MP_BASE_COLOR)
        to_prop(E(m, unreal.MaterialExpressionConstant, -700, -100, r=0.85), "", MP.MP_ROUGHNESS)
        op = E(m, unreal.MaterialExpressionSaturate, -400, 0)
        link(mul(m, mask, sparam(m, "Depth", 2.6, -800, 120), -600, 0, "R"), "", op, "")
        to_prop(op, "", MP.MP_OPACITY)
        # Deep cut: a normal derived from the mask's slope, so the groove walls catch the light.
        uv0 = E(m, unreal.MaterialExpressionTextureCoordinate, -1600, 600)
        def shifted(du, dv, y):
            add = E(m, unreal.MaterialExpressionAdd, -1400, y)
            link(uv0, "", add, "A")
            link(E(m, unreal.MaterialExpressionConstant2Vector, -1600, y + 60, r=du, g=dv), "", add, "B")
            return tparam(m, "Mask", d["mask"], SC.SAMPLERTYPE_MASKS, -1200, y, add)
        m0 = tparam(m, "Mask", d["mask"], SC.SAMPLERTYPE_MASKS, -1200, 600, uv0)
        mx = shifted(1.0 / 1024, 0.0, 760)
        my = shifted(0.0, 1.0 / 2048, 920)
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
    t["carve"] = {"mask": tex("Carving", "T_CroatoanCarving_Mask.png", "linear"), "grain": t["l2"]["bc"]}

    log("importing meshes")
    sm_l1 = mesh(L1, "Old_Wooden_Log_wcokfh1_High.fbx", "OldWoodenLog_A")
    sm_l2 = mesh(L2, "Old_Wooden_Log_wcokfdy_High.fbx", "OldWoodenLog_B")
    sm_bm = mesh(BM, "Old_Wooden_Beam_vkbhcbg_High.fbx", "OldWoodenBeam")
    grass = [mesh(GR, "Wild_Grass_vlkhcbxia_High_vlkhcbxia_Var%s_LOD0.fbx" % v, "WildGrass_" + v) for v in "ABCDEFGH"]

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
    m_sky = m_unlit("M_NightSky", (0.012, 0.016, 0.026), 1.0)
    m_iron = mi("MI_IronDark", master, {"Wet": 0.6, "UVScale": 3.0}, {"Tint": (0.08, 0.08, 0.085)})

    log("level")
    if eal.does_asset_exist(MAP):
        levels.load_level(MAP)
        clear()
    else:
        levels.new_level(MAP)

    logs = [(sm_l1, mi_l1), (sm_l2, mi_l2)]

    def pick():
        return logs[rng.randrange(2)]

    # Ground: wet mud, 80 m square
    g = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(1500, 0, 0), unreal.Rotator(0, 0, 0))
    g.static_mesh_component.set_static_mesh(PLANE)
    g.static_mesh_component.set_world_scale3d(V(80, 80, 1))
    g.static_mesh_component.set_material(0, mi("MI_Mud", m_mud, {"UVScale": 32.0}))
    tag(g, "Ground_Mud", "Ground")

    # --- the palisade: "a high palisado of great trees" --------------------------------------
    F = "Palisade"

    def lash(a_, b_, at_y, folder):
        """Withy/rope lashing wrapped round a rail where it crosses a trunk."""
        for k in range(3):
            place_between("Lashing", folder, sm_bm, V(a_ - 14, at_y - 12, b_ - 12 + k * 8), V(a_ - 14, at_y + 12, b_ + 12 + k * 8), 3.0, mi_rope)

    def run(label, x0, y_start, y_end, z_rail):
        """A curtain of whole trunks: irregular heights, diameters, lean and spin; the odd gap; a lashed rail."""
        step = 1 if y_end > y_start else -1
        y = y_start
        trunks = []
        while (y - y_end) * step < 0:
            s, mt = pick()
            d = rng.uniform(35, 55)
            if rng.random() > 0.03:                     # only where a trunk has rotted out
                upright(label, F, s, x0 + rng.uniform(-10, 10), y, rng.uniform(350, 450), d, mt,
                        lean_x=rng.uniform(-3, 2.5), lean_y=rng.uniform(-3, 3))
                trunks.append(y)
            y += step * d * rng.uniform(0.80, 0.90)          # set tight: "a high palisado of great trees"
        if trunks:
            place_between(label + "_Rail", F, sm_bm, V(x0 + 34, y_start, z_rail), V(x0 + 34, y_end, z_rail + rng.uniform(-15, 15)), 20, mi_beam)   # rails behind the trunks
            for ty in trunks[::3]:
                lash(x0 + 62, z_rail, ty, F)

    run("Trunk_R", 740, 230, 2600, 240)          # right curtain, behind the CROATOAN post
    run("Trunk_L", 715, -150, -650, 250)         # left curtain, from the gate to the flanker
    # The flanker (bastion): trunks leaning outward toward the field, its face angled across the view
    for i in range(20):
        f = i / 19.0
        s, mt = pick()
        upright("Bastion", F, s, 700 - f * 480, -660 - f * 760, rng.uniform(430, 520), rng.uniform(30, 46), mt,
                lean_x=-13 + rng.uniform(-3, 3), lean_y=rng.uniform(-3, 3))
    for zz in (60, 300):
        place_between("Bastion_Rail", F, sm_l1, V(735, -660, zz), V(220, -1420, zz + 20), 28, mi_dark)
    # Watch platform on the flanker (top left of the reference)
    T = "Bastion/Watch"
    for (px, py) in ((850, -1000), (1250, -1000), (850, -1400), (1250, -1400)):
        place_between("Watch_Leg", T, sm_l2, V(px, py, -40), V(px + rng.uniform(-10, 10), py, 900), 32, mi_dark)
    box("Watch_Floor", T, (1050, -1200, 640), (480, 480, 18), mi_beam)
    for (a_, b_) in (((810, -960, 760), (1290, -960, 760)), ((810, -1440, 760), (1290, -1440, 760)), ((810, -960, 760), (810, -1440, 760))):
        place_between("Watch_Rail", T, sm_bm, V(*a_), V(*b_), 16, mi_beam)
    box("Watch_RoofL", T, (1050, -1090, 1020), (560, 330, 14), mi_dark, rot=(28, 0, 0))
    box("Watch_RoofR", T, (1050, -1310, 1020), (560, 330, 14), mi_dark, rot=(-28, 0, 0))
    box("Watch_Lamp", T, (1000, -1050, 700), (16, 16, 24), m_lamp)
    point("Watch_LampLight", T, (1000, -1050, 700), 120, 2300, radius=700, vol=0.15)

    # --- the main entrance: a narrow gap between two great posts, barred with heavy timbers ---
    G = "Gate"
    place_between("GatePost_L", G, sm_l2, V(705, -95, -60), V(708, -95, 620), 78, mi_dark, spin=120)
    for zz in (70, 245, 330):                      # heavy bars across the gap, kept clear of the 1.5 m line
        z2 = zz + rng.uniform(-10, 10)
        place_between("GateBar", G, sm_l1 if zz != 245 else sm_bm, V(668, -150, zz), V(672, 112, z2), rng.uniform(26, 32), mi_beam)
        lash(705, zz, -95, G)
    # The lantern hangs just inside the gap
    lx, ly, lz = 860, 20, 255
    box("GateLantern_Frame", G, (lx, ly, lz + 22), (18, 18, 4), m_iron)
    box("GateLantern_Glass", G, (lx, ly, lz), (13, 13, 24), m_lamp)
    box("GateLantern_Cap", G, (lx, ly, lz - 14), (18, 18, 4), m_iron)
    point("GateLantern_Light", G, (lx, ly, lz), 140, 2300, radius=700, source=3, vol=0.25)

    # --- the CROATOAN post: the RIGHT-hand post of the entrance, bark taken off, letters at 5 ft --
    P = "CroatoanPost"
    PX, PY = 700, 150
    place_between("CROATOAN_Post", P, sm_l2, V(PX, PY, -60), V(PX + 3, PY - 2, 300), 126, mi_post, spin=40)        # stripped section
    place_between("CROATOAN_Post_Bark", P, sm_l1, V(PX + 3, PY - 2, 285), V(PX + 6, PY - 4, 700), 126, mi_dark, spin=90)  # bark left on above
    # Face the carving toward the approach and the camera (about 25° off the wall normal).
    face = math.radians(6.0)
    dec = actors.spawn_actor_from_class(unreal.DecalActor, V(PX - 95 * math.cos(face), PY - 95 * math.sin(face), 150),
                                        unreal.Rotator(90, 0, math.degrees(face)))
    dc = dec.decal
    dc.set_decal_material(mi("MI_CroatoanCarving", m_carve))
    dc.set_editor_property("decal_size", V(70, 124, 62))     # half-extents after the 90° roll: depth, height 2.48 m, width 1.24 m
    # Cool fill on the post from out of frame left: the stripped wood should be the palest thing in the shot.
    fa, fl = light(unreal.SpotLight, "PostFill", P, (-150, -250, 250))
    fa.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(-150, -250, 250), V(PX - 50, PY, 160)), False)
    safe_set(fl, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(fl, "intensity", float(os.environ.get("LETHE_POST_FILL", "220")))
    safe_set(fl, "use_temperature", True)
    safe_set(fl, "temperature", 7000.0)
    safe_set(fl, "inner_cone_angle", 6.0)
    safe_set(fl, "outer_cone_angle", 14.0)
    safe_set(fl, "attenuation_radius", 1400.0)
    safe_set(fl, "source_radius", 30.0)
    safe_set(fl, "volumetric_scattering_intensity", 0.0)
    tag(dec, "CROATOAN_Carving", P)

    # --- behind the wall: lanterns leaking through the gaps, a house with lit windows -------
    B = "BehindWall"
    for (x, y_, z) in ((950, 600, 260), (1000, 1500, 240), (980, -600, 280), (1050, -150, 230)):
        point("Lantern_Behind", B, (x, y_, z), 55, 2300, radius=550, vol=0.1)
    box("House_Wall", B, (2300, 300, 300), (900, 1200, 600), mi_dark)
    box("House_RoofA", B, (2300, 30, 760), (980, 700, 24), mi_dark, rot=(35, 0, 0))
    box("House_RoofB", B, (2300, 570, 760), (980, 700, 24), mi_dark, rot=(-35, 0, 0))
    box("House_Chimney", B, (2500, 100, 930), (90, 90, 300), mi_dark)
    for (wy, wz) in ((-50, 300), (450, 300), (200, 520)):
        box("House_Window", B, (1848, wy, wz), (6, 80, 110), m_win)
    _, rc = light(unreal.RectLight, "House_WindowLight", B, (1830, 200, 330), (0, 0, 180))
    safe_set(rc, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(rc, "intensity", 60.0)
    safe_set(rc, "use_temperature", True)
    safe_set(rc, "temperature", 2000.0)
    safe_set(rc, "source_width", 300.0)
    safe_set(rc, "source_height", 150.0)
    safe_set(rc, "attenuation_radius", 900.0)
    safe_set(rc, "volumetric_scattering_intensity", 0.15)

    # --- ground dressing: grass "almost ouergrowen", mud decals ------------------------------
    GD = "Ground/Grass"
    for i in range(260):
        if i < 140:
            x, y_ = rng.uniform(560, 820), rng.uniform(-1900, 2600)        # along the wall foot
        elif i < 200:
            x, y_ = rng.uniform(-200, 500), rng.uniform(-1700, -500)       # left foreground
        else:
            x, y_ = rng.uniform(150, 700), rng.uniform(400, 1600)          # right of the post
        s = rng.choice(grass)
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, -2), unreal.Rotator(rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(s)
        sc = rng.uniform(0.7, 1.3)
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc * rng.uniform(0.8, 1.2)))
        for k in range(max(1, a.static_mesh_component.get_num_materials())):
            a.static_mesh_component.set_material(k, m_gr)
        tag(a, "Grass", GD)

    # Weeds, nettles, dry and wheat grass crowding the wall foot and the post; rocks half sunk in the mud.
    def plant(kind, x, y_, scale_rng=(0.8, 1.3)):
        tx, ms = plants[kind]
        if not ms:
            return
        mat = mi("MI_Plant_" + kind, m_gr, None, {"Tint": (0.5, 0.52, 0.46)},
                 {"BaseColor": tx["bc"], "Opacity": tx["op"], "Normal": tx["n"], "Translucency": tx["tr"]}) if kind not in PLANT_MI else PLANT_MI[kind]
        PLANT_MI[kind] = mat
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, -3), unreal.Rotator(rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(rng.choice(ms))
        sc = rng.uniform(*scale_rng)
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
        for k in range(max(1, a.static_mesh_component.get_num_materials())):
            a.static_mesh_component.set_material(k, mat)
        tag(a, "Plant_" + kind, "Ground/Plants")

    PLANT_MI = {}
    for i in range(int(os.environ.get("LETHE_PLANTS", "420"))):
        r = rng.random()
        if r < 0.55:                                   # wall foot band, both curtains and the flanker
            y_ = rng.uniform(-1300, 2200)
            x = 690 + rng.uniform(-90, 25) if y_ > -650 else 700 - (abs(y_) - 660) * 0.63 + rng.uniform(-90, 20)
        elif r < 0.75:                                 # round the CROATOAN post and the gate
            x, y_ = rng.uniform(560, 700), rng.uniform(-200, 320)
        else:                                          # scattered across the foreground mud, sparser
            x, y_ = rng.uniform(150, 650), rng.uniform(-900, 1200)
        kind = rng.choices(["weeds", "nettle", "dry", "wheat", "shrubs"], weights=[3, 2, 3, 3, 1])[0]
        plant(kind, x, y_, (0.7, 1.4) if kind != "shrubs" else (0.6, 1.0))

    rock_mis = [mi("MI_Rock_%d" % i, master, {"Wet": 0.55}, {"Tint": (0.55, 0.56, 0.6)},
                   {"BaseColor": tx["bc"], "Normal": tx["n"], "Roughness": tx["r"], "AO": tx["ao"]}) for i, (tx, _) in enumerate(rocks)]
    for i in range(int(os.environ.get("LETHE_ROCKS", "40"))):
        j = rng.randrange(len(rocks))
        y_ = rng.uniform(-900, 1800)
        x = rng.uniform(520, 700) if rng.random() < 0.7 else rng.uniform(150, 500)
        a = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y_, rng.uniform(-12, -3)),
                                          unreal.Rotator(rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(0, 360)))
        a.static_mesh_component.set_static_mesh(rocks[j][1])
        sc = rng.uniform(0.6, 1.6) if j else rng.uniform(0.8, 1.2)
        a.static_mesh_component.set_world_scale3d(V(sc, sc, sc))
        for k in range(max(1, a.static_mesh_component.get_num_materials())):
            a.static_mesh_component.set_material(k, rock_mis[j])
        tag(a, "Rock", "Ground/Rocks")
    mdi = mi("MI_MudDecal", m_mdec)
    for i in range(int(os.environ.get("LETHE_MUD_DECALS", "0"))):   # off until the decal mask is verified
        a = actors.spawn_actor_from_class(unreal.DecalActor, V(rng.uniform(-100, 700), rng.uniform(-900, 900), 0), unreal.Rotator(0, -90, rng.uniform(0, 360)))
        a.decal.set_decal_material(mdi)
        s = rng.uniform(120, 260)
        a.decal.set_editor_property("decal_size", V(40, s, s))
        tag(a, "MudDecal", "Ground/Decals")

    # --- sky and light ------------------------------------------------------------------------
    L = "Lighting"
    sky = actors.spawn_actor_from_class(unreal.StaticMeshActor, V(9000, 0, 1500), unreal.Rotator(0, 90, 0))
    sky.static_mesh_component.set_static_mesh(PLANE)
    sky.static_mesh_component.set_world_scale3d(V(400, 400, 1))
    sky.static_mesh_component.set_material(0, m_sky)
    sky.static_mesh_component.set_editor_property("cast_shadow", False)
    tag(sky, "NightSky", L)

    _, moon = light(unreal.DirectionalLight, "MoonBacklight", L, (0, 0, 2000), (0, -22, 175))
    safe_set(moon, "intensity", 0.9)
    safe_set(moon, "use_temperature", True)
    safe_set(moon, "temperature", 12000.0)
    safe_set(moon, "volumetric_scattering_intensity", 0.3)
    safe_set(moon, "light_source_angle", 1.5)

    _, skyl = light(unreal.SkyLight, "SkyFill", L, (0, 0, 1500))
    safe_set(skyl, "real_time_capture", False)
    safe_set(skyl, "intensity", 0.35)
    safe_set(skyl, "lower_hemisphere_color", unreal.LinearColor(0.0, 0.0, 0.0, 1))

    # Nysa's UV Lantern, just out of frame to the right: a violet beam across the carving.
    uva, uv = light(unreal.SpotLight, "UVLantern", L, (120, 920, 140))
    uva.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(120, 920, 140), V(PX - 56, PY, 150)), False)
    safe_set(uv, "intensity_units", unreal.LightUnits.LUMENS)
    safe_set(uv, "intensity", 220.0)
    safe_set(uv, "light_color", unreal.Color(r=95, g=60, b=255, a=255))
    safe_set(uv, "inner_cone_angle", 1.8)
    safe_set(uv, "outer_cone_angle", 3.6)
    safe_set(uv, "attenuation_radius", 1800.0)
    safe_set(uv, "volumetric_scattering_intensity", 0.25)
    safe_set(uv, "source_radius", 1.5)

    fog = actors.spawn_actor_from_class(unreal.ExponentialHeightFog, V(0, 0, 0), unreal.Rotator(0, 0, 0))
    fc = fog.component
    safe_set(fc, "fog_density", 0.03)
    safe_set(fc, "fog_height_falloff", 0.35)
    safe_set(fc, "fog_inscattering_luminance", unreal.LinearColor(0.004, 0.008, 0.018, 1))
    safe_set(fc, "enable_volumetric_fog", True)
    safe_set(fc, "volumetric_fog_albedo", unreal.Color(r=140, g=160, b=192, a=255))
    safe_set(fc, "volumetric_fog_emissive", unreal.LinearColor(0.0008, 0.001, 0.0014, 1))
    safe_set(fc, "volumetric_fog_extinction_scale", 1.2)
    safe_set(fc, "volumetric_fog_scattering_distribution", 0.25)
    safe_set(fc, "volumetric_fog_distance", 6000.0)
    tag(fog, "NightFog", L)
    lfv_cls = unreal.load_class(None, "/Script/Engine.LocalFogVolume")
    if lfv_cls:
        for (x, y_) in ((700, -800), (750, 900), (300, 0)):
            v = actors.spawn_actor_from_class(lfv_cls, V(x, y_, 0), unreal.Rotator(0, 0, 0))
            v.set_actor_scale3d(V(14, 14, 2.2))
            for comp in v.get_components_by_class(unreal.ActorComponent):
                safe_set(comp, "radial_fog_extinction", 0.25)
                safe_set(comp, "height_fog_extinction", 0.6)
            tag(v, "GroundMist", L)

    ppv = actors.spawn_actor_from_class(unreal.PostProcessVolume, V(0, 0, 0), unreal.Rotator(0, 0, 0))
    ppv.set_editor_property("unbound", True)
    s = ppv.settings
    for prop, val in (
        ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
        ("auto_exposure_apply_physical_camera_exposure", False),
        ("auto_exposure_bias", float(os.environ.get("LETHE_BEAUTY_EV", "0.0"))),
        ("bloom_intensity", 0.55),
        ("bloom_threshold", 1.5),
        ("vignette_intensity", 0.55),
        ("film_grain_intensity", 0.18),
        ("scene_fringe_intensity", 0.25),
        ("color_saturation", unreal.Vector4(0.92, 0.92, 0.96, 1.0)),
        ("color_contrast", unreal.Vector4(1.08, 1.08, 1.08, 1.0)),
        ("color_gain_shadows", unreal.Vector4(0.86, 0.92, 1.08, 1.0)),
        ("color_gain_highlights", unreal.Vector4(1.06, 1.0, 0.92, 1.0)),
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

    # --- the camera ---------------------------------------------------------------------------
    cam = actors.spawn_actor_from_class(unreal.CineCameraActor, V(-80, 520, 150), unreal.Rotator(0, 0, 0))
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(V(-80, 520, 150), V(760, -180, 235)), False)
    cc = cam.get_cine_camera_component()
    fb = unreal.CameraFilmbackSettings()
    safe_set(fb, "sensor_width", 36.0)
    safe_set(fb, "sensor_height", 20.25)
    safe_set(cc, "filmback", fb)
    safe_set(cc, "current_focal_length", 40.0)
    safe_set(cc, "current_aperture", 2.8)
    fs = unreal.CameraFocusSettings()
    safe_set(fs, "focus_method", unreal.CameraFocusMethod.MANUAL)
    safe_set(fs, "manual_focus_distance", 810.0)
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
