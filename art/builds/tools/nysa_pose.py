"""Poses the Fab 'Free Medieval Assassin Girl' (CC BY 4.0, Dimentrius3dArtist) as Nysa and writes a static glTF.

Reads the converted glTF (joints at identity, bind pose in the inverse bind matrices), drops the hood, mask and
weapons, rotates the arm joints, re-skins every vertex (linear blend) and writes plain static meshes that share
the original materials and textures. glTF space here: +Y up, +Z the way she faces, -X her right, centimetres.
"""
import json, re, struct, sys, math
sys.path.insert(0, "C:/LETHE/Saved/lethe_tmp")
from mat4 import *

SRC = "C:/LETHE/SourceArt/Nysa/gltf/"
j = json.load(open(SRC + "scene.gltf"))
bin_ = open(SRC + "scene.bin", "rb").read()
nodes = j["nodes"]
par = {c: i for i, n in enumerate(nodes) for c in n.get("children", [])}
base = lambda k: re.sub(r"_\d+$", "", nodes[k].get("name", ""))


def acc(ai):
    a = j["accessors"][ai]; bv = j["bufferViews"][a["bufferView"]]
    comp = {5126: "f", 5123: "H", 5121: "B", 5125: "I"}[a["componentType"]]
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", ncomp * struct.calcsize(comp))
    out = [struct.unpack_from("<%d%s" % (ncomp, comp), bin_, off + k * stride) for k in range(a["count"])]
    if a.get("normalized") and comp in "BH":
        d = 255.0 if comp == "B" else 65535.0
        out = [tuple(x / d for x in v) for v in out]
    return out


# bind pose (world) of every joint, from any skin that lists it
B = {}
for sk in j["skins"]:
    for k, M in zip(sk["joints"], acc(sk["inverseBindMatrices"])):
        B.setdefault(k, inv(from_gltf(M)))
# joints that carry no vertices (upperarm, lowerarm, spine_05...) get their position from their corrective bones
kids = {}
for c, pp_ in par.items():
    kids.setdefault(pp_, []).append(c)
def desc(k):
    for c in kids.get(k, []):
        yield c
        yield from desc(c)
root = next(i for i in range(len(nodes)) if base(i) == "root")
JOINTS = {root} | set(desc(root))
for k in JOINTS:
    if k in B:
        continue
    nm = base(k); side = nm[-2:] if nm[-2:] in ("_l", "_r") else ""
    stem = nm[:-2] if side else nm
    cor = [d for d in desc(k) if d in B and re.fullmatch(stem + r"_(in|out|fwd|bck)" + side, base(d))]
    near = cor or [d for d in kids.get(k, []) if d in B] or [d for d in desc(k) if d in B][:1]
    if near:
        M = eye()
        for r in range(3):
            M[r][3] = sum(pos(B[d])[r] for d in near) / len(near)
        B[k] = M
byname = {base(k): k for k in B}

DROP = ("mask", "weapons", "sword", "knife", "biggin")
POSE = {     # bone -> direction (glTF space) its child should point along
    "upperarm_r": (-0.30, 0.25, 0.92),
    "lowerarm_r": (0.0, 0.45, 0.89),
    "upperarm_l": (0.20, -0.975, 0.10),
    "lowerarm_l": (0.12, -0.92, 0.37),
}
CHILD = {"upperarm_r": "lowerarm_r", "lowerarm_r": "hand_r", "upperarm_l": "lowerarm_l", "lowerarm_l": "hand_l"}
# Delta per joint: posed world = D * bind world. Walk from the root so parents are done first.
D = {}
def delta(k):
    if k in D:
        return D[k]
    p = par.get(k)
    Dp = delta(p) if p in JOINTS else eye()
    nm = base(k)
    if nm in POSE and k in B:
        piv = pt(Dp, pos(B[k]))
        ch = byname[CHILD[nm]]
        cur = [a - b for a, b in zip(pt(Dp, pos(B[ch])), piv)]
        R = between(cur, POSE[nm])
        T1 = eye(); T1[0][3], T1[1][3], T1[2][3] = piv
        T2 = eye(); T2[0][3], T2[1][3], T2[2][3] = [-x for x in piv]
        D[k] = mul(T1, mul(R, mul(T2, Dp)))
    else:
        D[k] = Dp
    return D[k]
for k in JOINTS:
    delta(k)

out_pos, out_nrm, out_uv, out_idx = bytearray(), bytearray(), bytearray(), bytearray()
meshes, accessors, views, gnodes = [], [], [], []
lo = [1e9] * 3; hi = [-1e9] * 3


def add_view(data, target):
    views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), "target": target})
    blob.extend(data)
    while len(blob) % 4:
        blob.append(0)
    return len(views) - 1


blob = bytearray()
for ni, n in enumerate(nodes):
    if "mesh" not in n:
        continue
    m = j["meshes"][n["mesh"]]
    if any(d in m["name"] for d in DROP):
        continue
    sk = j["skins"][n["skin"]]
    prims = []
    for pr in m["primitives"]:
        at = pr["attributes"]
        P, N, UV = acc(at["POSITION"]), acc(at["NORMAL"]), acc(at["TEXCOORD_0"])
        J, Wt = acc(at["JOINTS_0"]), acc(at["WEIGHTS_0"])
        I = acc(pr["indices"])
        pp, nn = bytearray(), bytearray()
        for v in range(len(P)):
            px = [0.0, 0.0, 0.0]; nx = [0.0, 0.0, 0.0]
            for c in range(4):
                w = Wt[v][c]
                if w <= 0:
                    continue
                Dm = D[sk["joints"][J[v][c]]]
                a = pt(Dm, P[v]); b = vec(Dm, N[v])
                for r in range(3):
                    px[r] += w * a[r]; nx[r] += w * b[r]
            ln = math.sqrt(sum(x * x for x in nx)) or 1.0
            nx = [x / ln for x in nx]
            for r in range(3):
                lo[r] = min(lo[r], px[r]); hi[r] = max(hi[r], px[r])
            pp += struct.pack("<3f", *px); nn += struct.pack("<3f", *nx)
        uv = b"".join(struct.pack("<2f", *t) for t in UV)
        ix = b"".join(struct.pack("<I", i[0]) for i in I)
        vp = add_view(pp, 34962); vn = add_view(nn, 34962); vu = add_view(uv, 34962); vi = add_view(ix, 34963)
        xs = [struct.unpack_from("<3f", pp, k * 12) for k in range(len(P))]
        accessors.append({"bufferView": vp, "componentType": 5126, "count": len(P), "type": "VEC3",
                          "min": [min(x[r] for x in xs) for r in range(3)], "max": [max(x[r] for x in xs) for r in range(3)]})
        accessors.append({"bufferView": vn, "componentType": 5126, "count": len(P), "type": "VEC3"})
        accessors.append({"bufferView": vu, "componentType": 5126, "count": len(P), "type": "VEC2"})
        accessors.append({"bufferView": vi, "componentType": 5125, "count": len(I), "type": "SCALAR"})
        a0 = len(accessors) - 4
        prims.append({"attributes": {"POSITION": a0, "NORMAL": a0 + 1, "TEXCOORD_0": a0 + 2}, "indices": a0 + 3,
                      "material": pr.get("material", 0)})
    meshes.append({"name": "Nysa_" + m["name"].replace("_M_", "_").rstrip("_0"), "primitives": prims})
    gnodes.append({"name": meshes[-1]["name"], "mesh": len(meshes) - 1})

# Long curly hair: three curved card layers wrapped round the back of the head and hanging down her back,
# textured by Scripts/make_curl_texture.ps1 (alpha-cut ringlets). The model's own hair is short and tied back.
import random as _r
_rng = _r.Random(5)
def _rad(y):          # head radius at the crown, widening over the shoulders
    if y > 168: return 11.6
    if y > 145: return 10.8 + (168 - y) / 23.0 * 6.5
    return 17.3 + (145 - y) / 40.0 * 1.5
cprims, mat_c = [], len(j["materials"])
for layer, (dr, th0, th1, u0) in enumerate(((0.0, -112, 112, 0.0), (1.6, -96, 100, 0.37), (3.0, -80, 86, 0.71))):
    NT, NY_, Y0, Y1 = 26, 22, 171.0 - layer * 2.0, 106.0 - layer * 3.0
    pp, nn, uv, ix = bytearray(), bytearray(), bytearray(), bytearray()
    xs = []
    for iy in range(NY_ + 1):
        y = Y0 + (Y1 - Y0) * iy / NY_
        for it in range(NT + 1):
            sp_ = 0.55 + 0.45 * min(1.0, max(0.0, (Y0 - y) / 22.0))      # behind the skull only at the top
            th = math.radians((th0 + (th1 - th0) * it / NT) * sp_)
            r = _rad(y) + dr + _rng.uniform(-0.4, 0.4)
            p = (r * math.sin(th) - 0.8, y, -r * math.cos(th) - 0.5)
            xs.append(p)
            pp += struct.pack("<3f", *p); nn += struct.pack("<3f", math.sin(th), 0.0, -math.cos(th))
            uv += struct.pack("<2f", u0 + 1.7 * it / NT, iy / NY_)
    for iy in range(NY_):
        for it in range(NT):
            a0 = iy * (NT + 1) + it; b0 = a0 + 1; c0 = a0 + NT + 1; d0 = c0 + 1
            ix += struct.pack("<6I", a0, c0, b0, b0, c0, d0)
    n_ = len(xs); ni = NY_ * NT * 6
    vp = add_view(pp, 34962); vn = add_view(nn, 34962); vu = add_view(uv, 34962); vi = add_view(ix, 34963)
    for r_ in (lo, hi):
        pass
    for p in xs:
        for k in range(3):
            lo[k] = min(lo[k], p[k]); hi[k] = max(hi[k], p[k])
    accessors.append({"bufferView": vp, "componentType": 5126, "count": n_, "type": "VEC3",
                      "min": [min(x[k] for x in xs) for k in range(3)], "max": [max(x[k] for x in xs) for k in range(3)]})
    accessors.append({"bufferView": vn, "componentType": 5126, "count": n_, "type": "VEC3"})
    accessors.append({"bufferView": vu, "componentType": 5126, "count": n_, "type": "VEC2"})
    accessors.append({"bufferView": vi, "componentType": 5125, "count": ni, "type": "SCALAR"})
    a0 = len(accessors) - 4
    cprims.append({"attributes": {"POSITION": a0, "NORMAL": a0 + 1, "TEXCOORD_0": a0 + 2}, "indices": a0 + 3, "material": mat_c})
meshes.append({"name": "Nysa_Curls", "primitives": cprims})
gnodes.append({"name": "Nysa_Curls", "mesh": len(meshes) - 1})
j["materials"] = j["materials"] + [{"name": "M_curls", "doubleSided": True}]

hand = pt(D[byname["hand_r"]], pos(B[byname["hand_r"]]))
head = pt(D[byname["head"]], pos(B[byname["head"]]))
out = {"asset": {"version": "2.0", "generator": "LETHE nysa_pose.py"},
       "scene": 0, "scenes": [{"nodes": [len(gnodes)]}],
       "nodes": gnodes + [{"name": "Nysa", "scale": [0.01, 0.01, 0.01], "children": list(range(len(gnodes)))}],
       "meshes": meshes, "accessors": accessors, "bufferViews": views,
       "buffers": [{"uri": "NysaPosed.bin", "byteLength": len(blob)}],
       "materials": j["materials"], "textures": j.get("textures", []), "images": j.get("images", []),
       "samplers": j.get("samplers", [])}
open(SRC + "NysaPosed.bin", "wb").write(blob)
json.dump(out, open(SRC + "NysaPosed.gltf", "w"))
json.dump({"hand_r": hand, "head": head, "lo": lo, "hi": hi}, open(SRC + "NysaPosed_info.json", "w"))
print("parts", len(meshes), "bbox", [round(x, 1) for x in lo], [round(x, 1) for x in hi], "hand_r", [round(x, 1) for x in hand], "head", [round(x, 1) for x in head])
