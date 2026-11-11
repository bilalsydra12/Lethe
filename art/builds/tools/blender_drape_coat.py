"""
Blender (headless) cloth pass for Nysa's coat.
  blender -b --factory-startup -P C:/LETHE/Scripts/blender_drape_coat.py
1. Imports her MetaHuman body in the lamp pose (SourceArt/Nysa/blender/NysaBody_pose.fbx, exported by
   export_nysa_body_fbx.py) and fits it to MetaHuman component space (cm, feet at origin, facing +Y, her right -X)
   using the bone landmarks in Saved/nysa_mh_pose.json.
2. Takes the hand-shaped coat (SourceArt/Nysa/coat/NysaCoat.obj, material Coat), loosens it, subdivides it and lets a
   heavy-wool cloth simulation hang it on her posed body (pinned at the shoulders and collar), so it gets real folds.
3. Adds thickness, front buttons, pocket flaps; models a leather satchel (body, flap, straps, buckle), belt and
   strap; UV-unwraps everything at a constant texel scale for tiling wool / leather textures.
4. Writes SourceArt/Nysa/coat/NysaCoat_cloth.obj in component space with materials Coat, Leather, Metal.
"""
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

SRC = "C:/LETHE/SourceArt/Nysa"
POSE = json.load(open("C:/LETHE/Saved/nysa_mh_pose.json"))
OUT = SRC + "/coat/NysaCoat_cloth.obj"
FRAMES = int(os.environ.get("LETHE_CLOTH_FRAMES", "0"))   # 0: shaped folds only, no cloth simulation
LOG = "C:/LETHE/Saved/blender_drape.log"
open(LOG, "w").close()


def log(*a):
    s = " ".join(str(x) for x in a)
    print("DRAPE:", s)
    with open(LOG, "a") as f:
        f.write(s + "\n")


bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.scale_length = 1.0

# ------------------------------------------------------------------ body, posed, in component space (we work in cm)
# Her own body + skeleton come from the rest file; the pose file's skeleton only supplies the lamp-pose rotations
# (its rest proportions are the generic ones, so its bones are not used for positions).
import numpy as np  # noqa: E402  (bundled with Blender)


def umeyama(pairs):
    n = len(pairs)
    ma = sum((a for a, _ in pairs), Vector()) / n
    mb = sum((b for _, b in pairs), Vector()) / n
    A = np.array([list(a - ma) for a, _ in pairs])
    Bm = np.array([list(b - mb) for _, b in pairs])
    U, S, Vt = np.linalg.svd(Bm.T @ A / n)
    D = np.eye(3)
    D[2, 2] = np.sign(np.linalg.det(U @ Vt))
    R = U @ D @ Vt
    s = float(np.trace(np.diag(S) @ D) / ((A ** 2).sum() / n))
    t = np.array(list(mb)) - s * R @ np.array(list(ma))
    M = Matrix([[*(s * R[i]), t[i]] for i in range(3)] + [[0, 0, 0, 1]])
    return M, s, max((M @ a - b).length for a, b in pairs)


TORSO = [k for k in POSE["bones"] if not k.startswith(("clavicle", "upperarm", "neck", "head"))]
bpy.ops.import_scene.fbx(filepath=SRC + "/blender/NysaBody_pose.fbx", global_scale=100.0, automatic_bone_orientation=False)
parm = next(o for o in scn.objects if o.type == "ARMATURE")
# the pose file carries her placeholder shirt + shorts, bound to that skeleton: it stands in for her torso (the body
# mesh itself has the torso cut away under clothing)
outfit = max((o for o in scn.objects if o.type == "MESH"), key=lambda o: len(o.data.vertices))
act = parm.animation_data.action if parm.animation_data else None
if act:
    scn.frame_set(int(act.frame_range[0]))
    log("pose action", act.name, act.frame_range[:])
before = set(scn.objects)
bpy.ops.import_scene.fbx(filepath=SRC + "/blender/NysaBody_rest.fbx", global_scale=100.0, automatic_bone_orientation=False)
new = [o for o in scn.objects if o not in before]
body = max((o for o in new if o.type == "MESH"), key=lambda o: len(o.data.vertices))
arm = next(o for o in new if o.type == "ARMATURE")
for o in new:
    if o not in (body, arm):
        bpy.data.objects.remove(o, do_unlink=True)
# Unreal's FBX export mirrors Y (left-handed -> right-handed): mirror both skeletons back before fitting
MIR = Matrix.Scale(-1.0, 4, Vector((0, 1, 0)))
for o_ in (arm, parm):
    o_.matrix_world = MIR @ o_.matrix_world
bpy.context.view_layer.update()
# fit her own skeleton (rest = standing; torso and legs are not moved by the lamp pose) to component space
FIT, s, err = umeyama([(arm.matrix_world @ arm.data.bones[k].head_local, Vector(POSE["bones"][k])) for k in TORSO if k in arm.data.bones])
log("body skeleton fit: scale %.4f, max landmark error %.2f cm" % (s, err))
arm.matrix_world = FIT @ arm.matrix_world
bpy.context.view_layer.update()
# copy the lamp pose as world-space rotation changes, parent before child
def depth(b):
    d = 0
    while b.parent:
        d, b = d + 1, b.parent
    return d


for b in sorted(arm.data.bones, key=depth):
    src = parm.pose.bones.get(b.name)
    if not src:
        continue
    rw_rest = (parm.matrix_world @ src.bone.matrix_local).to_quaternion()
    rw_pose = (parm.matrix_world @ src.matrix).to_quaternion()
    delta = rw_pose @ rw_rest.inverted()
    if abs(delta.angle) < 1e-4:
        continue
    pb = arm.pose.bones[b.name]
    cur = pb.matrix.copy()                         # armature space, already following its posed parent
    tgt_rot = arm.matrix_world.to_quaternion().inverted() @ delta @ (arm.matrix_world.to_quaternion() @ (arm.matrix_world.inverted() @ arm.matrix_world @ b.matrix_local).to_quaternion())
    pb.matrix = Matrix.LocRotScale(cur.to_translation(), tgt_rot, cur.to_scale())
    bpy.context.view_layer.update()
pairs_arm = [(arm.matrix_world @ arm.pose.bones[k].head, Vector(v)) for k, v in POSE["bones"].items() if k in arm.pose.bones]
log("posed skeleton vs landmarks, worst: %.2f cm" % max((a - b).length for a, b in pairs_arm))
for side_ in ("r", "l"):
    for j_, bn_ in (("elbow", "lowerarm_"), ("hand", "hand_")):
        p_ = arm.matrix_world @ arm.pose.bones[bn_ + side_].head
        log("%s %s: posed (%.1f %.1f %.1f) vs pose data (%.1f %.1f %.1f)" % ((side_, j_) + tuple(p_) + tuple(POSE["arms"][side_][j_])))
FITP, sp_, errp = umeyama([(parm.matrix_world @ parm.pose.bones[k].head, Vector(POSE["bones"][k])) for k in TORSO if k in parm.pose.bones])
log("shirt skeleton fit: scale %.4f, max landmark error %.2f cm" % (sp_, errp))
parm.matrix_world = FITP @ parm.matrix_world
bpy.context.view_layer.update()
# bake the posed body (limbs) + shirt (torso) to one plain mesh: the collider
dg = bpy.context.evaluated_depsgraph_get()
bm_c = bmesh.new()
for o in (body, outfit):
    m_ = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    m_.transform(o.matrix_world)
    bm_c.from_mesh(m_)
    if o is outfit:
        shirt_me = m_.copy()
bmesh.ops.reverse_faces(bm_c, faces=bm_c.faces)   # the mirror (MIR) turned the surfaces inside out: face them outward again
bm_c.normal_update()
me = bpy.data.meshes.new("Collider")
bm_c.to_mesh(me)
bm_c.free()
collider = bpy.data.objects.new("BodyCollider", me)
scn.collection.objects.link(collider)
for o in list(scn.objects):
    if o is not collider:
        bpy.data.objects.remove(o, do_unlink=True)
zs = [v.co.z for v in me.vertices]
log("posed body: %d verts, z %.1f..%.1f" % (len(me.vertices), min(zs), max(zs)))
_c = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
_out = sum(1 for p in me.polygons if (p.center - Vector((_c.x, _c.y, p.center.z))).dot(p.normal) > 0)
log("collider faces pointing outward: %d of %d" % (_out, len(me.polygons)))
# check the arm landmark lands on the mesh: nearest body vertex to the right hand
hr = Vector(POSE["hand_r"]) if isinstance(POSE["hand_r"], list) else None
if hr:
    d = min((v.co - hr).length for v in me.vertices)
    log("right hand landmark to body surface: %.1f cm" % d)

# ------------------------------------------------------------------ the starting coat: one clean piece, shaped from her body
# Body + skirt: rings of points up her torso. Down to the hips each ring hugs the shirt (ray cast in from outside, +2 cm);
# below that the skirt keeps the hip shape and flares out to the hem. Sleeves: tubes along each arm, shoulder to wrist.
from mathutils.bvhtree import BVHTree  # noqa: E402
shirt_tree = BVHTree.FromPolygons([v.co.copy() for v in shirt_me.vertices], [tuple(p.vertices) for p in shirt_me.polygons])
SEG = 64
Z_TOP, Z_HEM, DZ = 148.0, 14.0, 1.6
Z_HIP = 84.0
sp_keys = sorted((POSE["bones"][k][2], POSE["bones"][k][1]) for k in ("pelvis", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01"))


def spine_y(z):
    if z <= sp_keys[0][0]:
        return sp_keys[0][1]
    for (z0, y0), (z1, y1) in zip(sp_keys, sp_keys[1:]):
        if z0 <= z <= z1:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
    return sp_keys[-1][1]


def ring_radii(z):
    c = Vector((0.0, spine_y(z), z))
    out = []
    for k in range(SEG):
        a = 2 * math.pi * k / SEG
        d = Vector((math.cos(a), math.sin(a), 0.0))
        hit = shirt_tree.ray_cast(c + d * 80.0, -d, 80.0)
        out.append((80.0 - hit[3]) if hit[0] is not None else None)
    return c, out


rings = []
zs_ = []
z = Z_TOP
while z >= Z_HEM - 1e-6:
    zs_.append(z)
    z -= DZ
hip_r = None
prev = None
for z in zs_:
    c, rr = ring_radii(max(z, Z_HIP) if z < Z_HIP else z)
    c = Vector((c.x, c.y, z))
    rr = [r if r is not None else (prev[k] if prev else 12.0) for k, r in enumerate(rr)]
    if z >= Z_HIP:
        rr = [r + 1.4 for r in rr]
        prev = rr
        if hip_r is None or z <= Z_HIP + DZ:
            hip_r = rr
    else:
        f_ = (Z_HIP - z) / (Z_HIP - Z_HEM)
        rr = [hr * (1.0 + 0.18 * f_) + 1.0 * f_ for hr in hip_r]       # A-line flare to the hem
    # smooth around the ring (the shirt has seams and short sleeves)
    for _ in range(3):
        rr = [(rr[k - 1] + 2 * rr[k] + rr[(k + 1) % SEG]) / 4 for k in range(SEG)]
    rings.append((c, rr))
# smooth between rings
for _ in range(2):
    rings = [(c, [(rings[max(i - 1, 0)][1][k] + 2 * rr[k] + rings[min(i + 1, len(rings) - 1)][1][k]) / 4 for k in range(SEG)]) for i, (c, rr) in enumerate(rings)]
# the shoulders: the top rings narrow to a collar round the neck base
verts, faces_ = [], []
for i, (c, rr) in enumerate(rings):
    z = c.z
    col = max(0.0, min(1.0, (z - 140.0) / (Z_TOP - 140.0)))
    for k in range(SEG):
        a = 2 * math.pi * k / SEG
        r = rr[k] * (1 - col) + 8.5 * col * (1.0 + 0.15 * abs(math.cos(a)))
        # heavy wool folds: soft vertical folds from the hips, deepening and sharpening toward the hem; the back panel
        # (she faces +Y, so the back is a ~ -pi/2) folds a little less than the sides
        if z < Z_HIP + 8:
            fz = max(0.0, min(1.0, (Z_HIP + 8 - z) / (Z_HIP + 8 - Z_HEM)))
            ph = 0.9 * math.sin(0.11 * z) + 0.5 * math.sin(3.1 * a)
            wave = math.sin(9 * a + ph)
            wave = math.copysign(abs(wave) ** (1.0 - 0.45 * fz), wave)       # rounder at the hip, crisper at the hem
            back = 0.75 + 0.25 * abs(math.cos(a))
            r += (0.6 + 5.8 * fz ** 1.2) * back * (0.5 + 0.5 * wave) + 1.0 * math.sin(4 * a + 0.07 * z) * fz
        # the belt cinches the waist; small compression folds just above and below it
        wz_ = abs(z - 100.0)
        if wz_ < 7.0:
            r -= 1.6 * math.exp(-(wz_ / 2.5) ** 2)
            r += 0.45 * (1 - wz_ / 7.0) * math.sin(13 * a + 0.9 * z)
        # a few long creases running down from the shoulder blades
        if 104 < z < 138:
            r += 0.35 * math.sin(6 * a + 0.05 * z) * math.sin(math.pi * (z - 104) / 34)
        verts.append((c.x + r * math.cos(a), c.y + r * math.sin(a), z))
for i in range(len(rings) - 1):
    for k in range(SEG):
        a, b = i * SEG + k, i * SEG + (k + 1) % SEG
        faces_.append((a, b, b + SEG, a + SEG))
# sleeves
SSEG = 24
for sd in ("r", "l"):
    A_ = POSE["arms"][sd]
    sh, el, ha = Vector(A_["shoulder"]), Vector(A_["elbow"]), Vector(A_["hand"])
    path = []
    L1, L2 = (el - sh).length, (ha - el).length
    n1 = max(2, int(L1 / 1.6))
    n2 = max(2, int((L2 - 6.0) / 1.6))
    for j in range(n1):
        path.append(sh.lerp(el, j / n1))
    for j in range(n2 + 1):
        path.append(el.lerp(ha, (j / n2) * (L2 - 6.0) / L2))
    base = len(verts)
    tot = len(path)
    for j, p in enumerate(path):
        t = (path[min(j + 1, tot - 1)] - path[max(j - 1, 0)]).normalized()
        u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-3:
            u = t.cross(Vector((1, 0, 0)))
        u.normalize()
        w = t.cross(u).normalized()
        s_ = j / (tot - 1)
        r = 7.6 - 2.4 * s_ + 0.6 * math.sin(math.pi * s_)
        de_ = (p - el).length
        bend_ = max(0.0, 1.0 - de_ / 9.0)                          # bunching where the arm bends
        cuff_ = max(0.0, (s_ - 0.8) / 0.2)                         # pushed-up cuff gathers
        for k in range(SSEG):
            a = 2 * math.pi * k / SSEG
            rk = r + 0.9 * bend_ * math.sin(2.2 * de_ + 2 * a) + 0.5 * cuff_ * math.sin(3 * a + 1.7 * j) + 0.25 * math.sin(5 * a + 0.8 * j)
            verts.append(tuple(p + (u * math.cos(a) + w * math.sin(a)) * rk))
    for j in range(tot - 1):
        for k in range(SSEG):
            a, b = base + j * SSEG + k, base + j * SSEG + (k + 1) % SSEG
            faces_.append((a, b, b + SSEG, a + SSEG))
cm = bpy.data.meshes.new("Coat")
cm.from_pydata(verts, [], faces_)
cm.validate()
cm.update()
coat = bpy.data.objects.new("Coat", cm)
scn.collection.objects.link(coat)
# face the rings outward
bm = bmesh.new()
bm.from_mesh(cm)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(cm)
bm.free()
log("coat start: %d verts %d faces" % (len(cm.vertices), len(cm.polygons)))

bpy.context.view_layer.objects.active = coat
coat.select_set(True)
# loosen a little so the cloth has slack to fold, then even the mesh out
# the coat must start fully outside the body: push any point inside it (or closer than GAP) out along the surface normal,
# then relax so the pushed points don't leave creases
from mathutils.bvhtree import BVHTree  # noqa: E402
tree = BVHTree.FromObject(collider, bpy.context.evaluated_depsgraph_get())
GAP = 1.6
for it in range(3):
    moved = 0
    for v in cm.vertices:
        loc, nrm, idx, dist = tree.find_nearest(v.co)
        if loc is None:
            continue
        side = (v.co - loc).dot(nrm)
        if side < GAP:
            v.co = loc + nrm * GAP
            moved += 1
    bm_r = bmesh.new()
    bm_r.from_mesh(cm)
    bmesh.ops.smooth_vert(bm_r, verts=bm_r.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm_r.to_mesh(cm)
    bm_r.free()
    log("push-out pass %d: %d points moved" % (it, moved))
for v in cm.vertices:
    loc, nrm, idx, dist = tree.find_nearest(v.co)
    if loc is not None and (v.co - loc).dot(nrm) < GAP:
        v.co = loc + nrm * GAP
for v in cm.vertices:
    v.co += v.normal * 0.4
# (simulated at the shaped mesh's own density; subdivided after)
log("coat sim mesh: %d verts" % len(cm.vertices))

# pin group: shoulders / collar / top of the sleeves, fading out downward
pin = coat.vertex_groups.new(name="pin")
ua_r, ua_l = Vector(POSE["bones"]["upperarm_r"]), Vector(POSE["bones"]["upperarm_l"])
for v in cm.vertices:
    z = v.co.z
    w = max(0.0, min(1.0, (z - 130.0) / 8.0))
    for ua in (ua_r, ua_l):                       # sleeve caps at the shoulder joints
        w = max(w, max(0.0, 1.0 - (v.co - ua).length / 9.0))
    for sd_ in ("r", "l"):                       # sleeves held loosely along the arm so they don't slide down to the wrist
        A_ = POSE["arms"][sd_]
        for p0_, p1_ in ((A_["shoulder"], A_["elbow"]), (A_["elbow"], A_["hand"])):
            p0_, p1_ = Vector(p0_), Vector(p1_)
            seg_ = p1_ - p0_
            tt_ = max(0.0, min(1.0, (v.co - p0_).dot(seg_) / seg_.length_squared))
            if (v.co - (p0_ + seg_ * tt_)).length < 9.5 and tt_ < 0.92:
                w = max(w, 0.3)
    if w > 0:
        pin.add([v.index], w, "REPLACE")

# ------------------------------------------------------------------ cloth: heavy wool
# simulate in metres (Blender's cloth defaults are physical): scale down now, back up after
SC = Matrix.Scale(0.01, 4)
collider.data.transform(SC)
cm.transform(SC)
col = collider.modifiers.new("Collision", "COLLISION")
collider.collision.thickness_outer = 0.004
collider.collision.cloth_friction = 8.0
cl = coat.modifiers.new("Cloth", "CLOTH")
c = cl.settings
c.quality = 6
c.mass = 4.0 / max(1, len(cm.vertices))   # kg per cloth point: the whole coat weighs ~4 kg
c.air_damping = 1.0
c.tension_stiffness = 80.0
c.compression_stiffness = 120.0
c.shear_stiffness = 20.0
c.bending_stiffness = 0.6         # wool coat: soft enough to fold, heavy enough to hang
c.vertex_group_mass = "pin"
c.pin_stiffness = 5.0
c.shrink_min = 0.0
cc = cl.collision_settings
cc.distance_min = 0.004
cc.use_self_collision = True
cc.self_distance_min = 0.003
cc.collision_quality = 4
cl.point_cache.frame_start = 1
cl.point_cache.frame_end = FRAMES
scn.gravity = (0.0, 0.0, -9.81)
scn.frame_start, scn.frame_end = 1, FRAMES
if FRAMES <= 0:
    coat.modifiers.remove(cl)
for f in range(1, FRAMES + 1):
    scn.frame_set(f)
    if f % 10 == 0:
        log("sim frame", f)
dg = bpy.context.evaluated_depsgraph_get()
cme = bpy.data.meshes.new_from_object(coat.evaluated_get(dg))
cme.transform(Matrix.Scale(100.0, 4))
collider.data.transform(Matrix.Scale(100.0, 4))
draped = bpy.data.objects.new("CoatDraped", cme)
scn.collection.objects.link(draped)
bpy.data.objects.remove(coat, do_unlink=True)
zs = [v.co.z for v in cme.vertices]
log("draped: z %.1f..%.1f" % (min(zs), max(zs)))

# thickness and smoothing for render
bpy.context.view_layer.objects.active = draped
for o in scn.objects:
    o.select_set(o is draped)
sm = draped.modifiers.new("Smooth", "SMOOTH")
sm.factor, sm.iterations = 0.2, 1
so = draped.modifiers.new("Solid", "SOLIDIFY")
so.thickness, so.offset = 0.7, 1.0
ss = draped.modifiers.new("Sub", "SUBSURF")
ss.levels = 2
for m in ("Smooth", "Solid", "Sub"):
    bpy.ops.object.modifier_apply(modifier=m)
for p in cme.polygons:
    p.use_smooth = True

# ------------------------------------------------------------------ helpers for the leather pieces
def add_box(name, size, loc, rot_z=0.0, bevel=0.3, mat="Leather", segs=3):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=(0, 0, math.radians(rot_z)))
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    b = o.modifiers.new("Bevel", "BEVEL")
    b.width, b.segments = bevel, segs
    bpy.ops.object.modifier_apply(modifier="Bevel")
    o["mat"] = mat
    return o


def add_cyl(name, r, depth, loc, rot, mat="Metal", verts=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    o["mat"] = mat
    return o


def surface_point(z, ang, out=0.0):
    """Point on the draped coat at height z in direction ang (radians, 0 = +X, pi/2 = front +Y)."""
    d = Vector((math.cos(ang), math.sin(ang), 0))
    best, bd = None, 1e9
    for v in cme.vertices:
        if abs(v.co.z - z) < 1.5:
            q = Vector((v.co.x, v.co.y, 0))
            if q.length < 1:
                continue
            k = 1.0 - q.normalized().dot(d)
            if k < bd:
                bd, best = k, v.co.copy()
    if best is None:
        return None
    return best + d * out


draped["mat"] = "Coat"
parts = [draped]

# buttons down the front (she faces +Y), double row like the painted coat
for i, z in enumerate((128, 116, 104, 92)):
    for side in (-1, 1):
        p = surface_point(z, math.pi / 2 + side * 0.28, 0.25)
        if p:
            parts.append(add_cyl("Button", 0.95, 0.35, p, (math.radians(90), 0, 0), "Metal"))

# belt round the waist, following the coat surface
WZ = 100.0
# per direction, the outermost coat point in a thin band at the waist (so the belt sits on the coat all the way round)
NB = 96
best_r = [None] * NB
for v in cme.vertices:
    if abs(v.co.z - WZ) < 1.2:
        q = Vector((v.co.x, v.co.y - spine_y(WZ), 0))
        k = int(((math.atan2(q.y, q.x) / (2 * math.pi)) % 1.0) * NB) % NB
        if best_r[k] is None or q.length > best_r[k]:
            best_r[k] = q.length
for _ in range(NB):
    if all(r is not None for r in best_r):
        break
    best_r = [r if r is not None else (best_r[k - 1] if best_r[k - 1] is not None else best_r[(k + 1) % NB]) for k, r in enumerate(best_r)]
for _ in range(4):
    best_r = [(best_r[k - 1] + 2 * best_r[k] + best_r[(k + 1) % NB]) / 4 for k in range(NB)]
ring = [Vector(((best_r[k] + 0.3) * math.cos(2 * math.pi * (k + 0.5) / NB), spine_y(WZ) + (best_r[k] + 0.3) * math.sin(2 * math.pi * (k + 0.5) / NB), WZ)) for k in range(NB)]
if len(ring) > 8:
    bm = bmesh.new()
    rows = []
    for p in ring:
        rows.append((bm.verts.new(p + Vector((0, 0, -2.0))), bm.verts.new(p + Vector((0, 0, 2.0)))))
    for (a0, b0), (a1, b1) in zip(rows, rows[1:] + rows[:1]):
        bm.faces.new((a0, a1, b1, b0))
    bme = bpy.data.meshes.new("Belt")
    bm.to_mesh(bme)
    belt = bpy.data.objects.new("Belt", bme)
    scn.collection.objects.link(belt)
    bpy.context.view_layer.objects.active = belt
    for o in scn.objects:
        o.select_set(o is belt)
    so = belt.modifiers.new("Solid", "SOLIDIFY")
    so.thickness = 0.4
    bpy.ops.object.modifier_apply(modifier="Solid")
    belt["mat"] = "Leather"
    parts.append(belt)
    bp = surface_point(WZ, math.pi / 2, 0.8)
    if bp:
        parts.append(add_box("Buckle", (4.6, 0.5, 4.6), bp, 0, 0.4, "Metal", 2))

# satchel on her right flank (-X side), flap facing out, as in the painting
side = surface_point(80.0, math.pi * 1.08, 4.8) or Vector((-26, -2, 80))
yaw = math.degrees(math.atan2(side.y, side.x)) + 90
bag = add_box("Bag", (8.0, 23.0, 18.0), side, yaw - 90, 2.2, "Leather", 4)
d_out = Vector((side.x, side.y, 0)).normalized()
flap = add_box("BagFlap", (1.2, 23.6, 12.0), side + d_out * 4.2 + Vector((0, 0, 3.5)), yaw - 90, 0.5, "Leather", 3)
for sgn in (-1, 1):
    tang = Vector((-d_out.y, d_out.x, 0)) * 6.0 * sgn
    parts.append(add_box("BagStrapTab", (0.5, 2.2, 9.0), side + d_out * 5.0 + tang + Vector((0, 0, 0.5)), yaw - 90, 0.15, "Leather", 2))
    parts.append(add_box("BagBuckle", (0.6, 2.8, 2.6), side + d_out * 5.3 + tang + Vector((0, 0, -3.2)), yaw - 90, 0.2, "Metal", 2))
parts += [bag, flap]

# cross-body strap: left shoulder, over her back, down to the bag
top = Vector((11.0, -3.0, 142.0))
end = side + Vector((0, 0, 9.0))
pts = []
for k in range(41):
    tt = k / 40
    p = top.lerp(end, tt)
    ang = math.atan2(p.y, p.x)
    sp = surface_point(p.z, -math.pi / 2 + 0.85 * (p.x / 25.0), 0.5)   # on her back
    if sp is not None and tt < 0.88:
        p = Vector((p.x, sp.y, p.z))
    pts.append(p)
bm = bmesh.new()
rows = []
for i, p in enumerate(pts):
    nx = (pts[min(i + 1, 40)] - pts[max(i - 1, 0)]).normalized()
    w = nx.cross(Vector((0, 1, 0))).normalized() * 1.9
    rows.append((bm.verts.new(p - w), bm.verts.new(p + w)))
for (a0, b0), (a1, b1) in zip(rows, rows[1:]):
    bm.faces.new((a0, b0, b1, a1))
sme = bpy.data.meshes.new("Strap")
bm.to_mesh(sme)
strap = bpy.data.objects.new("Strap", sme)
scn.collection.objects.link(strap)
bpy.context.view_layer.objects.active = strap
for o in scn.objects:
    o.select_set(o is strap)
so = strap.modifiers.new("Solid", "SOLIDIFY")
so.thickness = 0.35
bpy.ops.object.modifier_apply(modifier="Solid")
strap["mat"] = "Leather"
parts.append(strap)

# ------------------------------------------------------------------ UVs: constant texel scale (1 UV unit = 40 cm)
for o in parts:
    bpy.context.view_layer.objects.active = o
    for q in scn.objects:
        q.select_set(q is o)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.0, scale_to_bounds=False, correct_aspect=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    # rescale UVs to world size
    me_ = o.data
    if not me_.uv_layers:
        continue
    uv = me_.uv_layers.active.data
    area3 = sum(p.area for p in me_.polygons)
    import itertools  # noqa: F401
    area2 = 0.0
    for p in me_.polygons:
        lp = [uv[li].uv for li in p.loop_indices]
        for i in range(1, len(lp) - 1):
            a, b, c = lp[0], lp[i], lp[i + 1]
            area2 += abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
    k = math.sqrt(area3 / max(area2, 1e-9)) / 40.0
    for d in uv:
        d.uv = d.uv * k

# ------------------------------------------------------------------ write OBJ (component space, cm, Z up)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
groups = {"Coat": [], "Leather": [], "Metal": []}
with open(OUT, "w") as f:
    f.write("# Nysa's coat draped by cloth simulation in Blender (Scripts/blender_drape_coat.py); MetaHuman component space, cm, Z up\n")
    vo, to = 0, 0
    for o in parts:
        me_ = o.data
        mw = o.matrix_world
        for v in me_.vertices:
            p = mw @ v.co
            f.write("v %.3f %.3f %.3f\n" % (p.x, p.y, p.z))
        uvl = me_.uv_layers.active.data if me_.uv_layers else None
        lp0 = to
        if uvl:
            for d in uvl:
                f.write("vt %.5f %.5f\n" % (d.uv.x, d.uv.y))
        polys = []
        for p in me_.polygons:
            polys.append([(vo + me_.loops[li].vertex_index + 1, (to + li + 1) if uvl else None) for li in p.loop_indices])
        groups[o.get("mat", "Coat")].append(polys)
        vo += len(me_.vertices)
        to += len(uvl) if uvl else 0
    for mat, lst in groups.items():
        if not lst:
            continue
        f.write("usemtl %s\n" % mat)
        for polys in lst:
            for poly in polys:
                f.write("f " + " ".join(("%d/%d" % (v, t)) if t else str(v) for v, t in poly) + "\n")
log("wrote", OUT, {k: sum(len(p) for p in v) for k, v in groups.items()})
bpy.ops.wm.save_as_mainfile(filepath=SRC + "/blender/NysaCoat_drape.blend")
log("done")
