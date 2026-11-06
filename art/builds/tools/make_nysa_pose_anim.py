"""
Makes a one-frame pose for the Nysa MetaHuman: right arm raised forward holding the UV lamp toward the post
(hand about chin height, elbow down), left arm hanging relaxed. Solves a two-bone arm in component space from
the body mesh's reference pose and writes the local rotations into /Game/Lethe/Characters/AS_Nysa_LampPose.
Also writes Saved/nysa_mh_pose.json with the posed hand/head positions in component space (feet at origin).
Run: LETHE_AUTORUN=C:/LETHE/Scripts/make_nysa_pose_anim.py
Env: LETHE_POSE_T = "fwd,up,side" hand offset from the right shoulder in cm (default 38,6,-4).
"""
import json
import math
import os
import unreal

BODY = "/Game/Lethe/MetaHumans/MH_Nysa/Body/SKM_MH_Nysa_BodyMesh"
OUT_PKG, OUT_NAME = "/Game/Lethe/Characters", "AS_Nysa_LampPose"
LOG = "C:/LETHE/Saved/nysa_mh_pose.log"
RCS = unreal.RelativeTransformSpace


def log(m):
    unreal.log("LETHE pose: " + m)
    with open(LOG, "a") as f:
        f.write(m + "\n")


# --- small quaternion / vector helpers (x, y, z, w), same product order as FQuat (A*B applies B first)
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qinv(q):
    return (-q[0], -q[1], -q[2], q[3])


def qrot(q, v):
    return qmul(qmul(q, (v[0], v[1], v[2], 0.0)), qinv(q))[:3]


def norm(v):
    l_ = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l_ for c in v)


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mulv(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))


def swing(u, v):
    """Shortest rotation taking direction u to direction v."""
    u, v = norm(u), norm(v)
    c = dot(u, v)
    if c < -0.9999:
        ax = norm(cross(u, (1, 0, 0) if abs(u[0]) < 0.9 else (0, 1, 0)))
        return (ax[0], ax[1], ax[2], 0.0)
    a = cross(u, v)
    q = (a[0], a[1], a[2], 1.0 + c)
    l_ = math.sqrt(sum(x * x for x in q))
    return tuple(x / l_ for x in q)


def rot_about_(axis, ang):
    s_ = math.sin(ang / 2)
    return (axis[0] * s_, axis[1] * s_, axis[2] * s_, math.cos(ang / 2))


def tq(t):
    r = t.rotation
    return (r.x, r.y, r.z, r.w)


def tv(t):
    p = t.translation
    return (p.x, p.y, p.z)


def run():
    open(LOG, "w").close()
    mesh = unreal.load_asset(BODY)
    skel = mesh.skeleton
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    act = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    comp = act.skeletal_mesh_component
    comp.set_skeletal_mesh_asset(mesh)
    cs = lambda b: comp.get_socket_transform(b, RCS.RTS_COMPONENT)
    ps = lambda b: comp.get_socket_transform(b, RCS.RTS_PARENT_BONE_SPACE)

    fwd, up = (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    side_r = 1.0 if tv(cs("hand_r"))[0] > 0 else -1.0
    right = (side_r, 0.0, 0.0)
    log("her right is %+.0f X" % side_r)

    new_cs = {}     # bone -> new component-space rotation
    ARMS = {}
    REF = {b: tv(cs(b)) for b in ("pelvis", "spine_01", "spine_02", "spine_03", "spine_04", "spine_05", "neck_01", "neck_02",
                                  "head", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "thigh_l", "thigh_r",
                                  "calf_l", "calf_r", "foot_l", "foot_r")}

    def solve_arm(sd, target_fn, pole_dir):
        U, L, H = "upperarm_" + sd, "lowerarm_" + sd, "hand_" + sd
        S, E, Hp = tv(cs(U)), tv(cs(L)), tv(cs(H))
        qU, qL, qH = tq(cs(U)), tq(cs(L)), tq(cs(H))
        L1, L2 = length(sub(E, S)), length(sub(Hp, E))
        T = target_fn(S)
        d_vec = sub(T, S)
        d = min(length(d_vec), L1 + L2 - 0.5)
        axis = norm(d_vec)
        T = add(S, mulv(axis, d))
        a = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
        h = math.sqrt(max(0.0, L1 * L1 - a * a))
        pole = norm(sub(pole_dir, mulv(axis, dot(pole_dir, axis))))
        E2 = add(add(S, mulv(axis, a)), mulv(pole, h))
        sU = swing(sub(E, S), sub(E2, S))
        dirL = qrot(sU, sub(Hp, E))
        sL = swing(dirL, sub(T, E2))
        new_cs[U] = qmul(sU, qU)
        new_cs[L] = qmul(sL, qmul(sU, qL))
        new_cs[H] = qmul(sL, qmul(sU, qH))
        ARMS[sd] = {"shoulder": S, "elbow": E2, "hand": T}
        log("%s: shoulder %s elbow %s hand %s (L1 %.1f L2 %.1f)" % (sd, [round(x) for x in S], [round(x) for x in E2],
                                                                 [round(x) for x in T], L1, L2))
        return T

    # the torch hand at chest height in front of her right shoulder, elbow down by her side (as painted), not reaching out
    t_ = [float(x) for x in os.environ.get("LETHE_POSE_T", "29,-11,-2").split(",")]
    hand_r = solve_arm("r", lambda S: add(S, add(add(mulv(fwd, t_[0]), mulv(up, t_[1])), mulv(right, t_[2]))),
                       add(add(mulv(up, -1.0), mulv(right, 0.35)), mulv(fwd, -0.15)))
    # her head turns toward the post (her right), so her face shows in profile as painted; neck and head share the turn
    HEAD_TURN = float(os.environ.get("LETHE_HEAD_TURN", "28"))
    pivot = tv(cs("neck_01"))
    up_ax = (0.0, 0.0, -side_r)             # positive turn swings her face toward her right (-X when her right is -X)
    acc_ = 0.0
    for b, share in (("neck_01", 0.3), ("neck_02", 0.3), ("head", 0.4)):
        acc_ += HEAD_TURN * share
        new_cs[b] = qmul(rot_about_(up_ax, math.radians(acc_)), tq(cs(b)))
    log("head turned %.0f deg toward her right" % HEAD_TURN)
    left = mulv(right, -1.0)
    hand_l = solve_arm("l", lambda S: add(S, add(add(mulv(up, -50.0), mulv(left, 9.0)), mulv(fwd, 12.0))),
                       add(add(mulv(fwd, -1.0), mulv(left, 0.4)), mulv(up, 0.0)))

    # ---- her right hand closes round the torch, and the wrist turns so the torch points at the letters
    TORCH = {}
    target = tuple(float(x) for x in os.environ.get("LETHE_POSE_TARGET", "-11.6,58.5,152").split(","))   # CROATOAN, component space

    def rot_about(axis, ang):
        s_ = math.sin(ang / 2)
        return (axis[0] * s_, axis[1] * s_, axis[2] * s_, math.cos(ang / 2))

    def grip(sd):
        H = "hand_" + sd
        P = lambda b: tv(cs(b))
        hp = P(H)
        D = qmul(new_cs[H], qinv(tq(cs(H))))                         # how the arm solve turned the hand
        i1, m1, r1, p1 = (P(f + "_01_" + sd) for f in ("index", "middle", "ring", "pinky"))
        n_ = norm(cross(sub(i1, hp), sub(p1, hp)))
        to_body = (-1.0 if hp[0] > 0 else 1.0, 0.0, 0.0)
        palm = n_ if dot(n_, to_body) > 0 else mulv(n_, -1.0)       # in the A-pose the palms face the thighs
        ref_rot = {}
        for f, angs in (("index", (68, 92, 55)), ("middle", (74, 95, 55)), ("ring", (80, 95, 55)), ("pinky", (86, 92, 55)),
                        ("thumb", (22, 34, 30))):
            chain = [f + "_01_" + sd, f + "_02_" + sd, f + "_03_" + sd]
            cur = [P(b) for b in chain]
            cur.append(add(cur[2], mulv(sub(cur[2], cur[1]), 0.8)))
            acc = (0.0, 0.0, 0.0, 1.0)
            for j in range(3):
                d_ = norm(sub(cur[j + 1], cur[j]))
                ax_ = norm(cross(d_, palm))
                R_ = rot_about(ax_, math.radians(angs[j]))
                for k_ in range(j + 1, 4):
                    cur[k_] = add(cur[j], qrot(R_, sub(cur[k_], cur[j])))
                acc = qmul(R_, acc)
                ref_rot[chain[j]] = qmul(acc, tq(cs(chain[j])))
        # wrist: turn the hand so the knuckle line (pinky to index: the torch's axis in a fist) points at the target
        k_ref = norm(sub(i1, p1))
        hand_pos = ARMS[sd]["hand"]
        W = swing(qrot(D, k_ref), sub(target, hand_pos))
        WD = qmul(W, D)
        new_cs[H] = qmul(W, new_cs[H])
        for b, q_ in ref_rot.items():
            new_cs[b] = qmul(WD, q_)
        for f in ("index", "middle", "ring", "pinky"):                # the palm bones ride with the hand
            mb = f + "_metacarpal_" + sd
            try:
                new_cs[mb] = qmul(WD, tq(cs(mb)))
            except Exception:  # noqa: BLE001
                pass
        # the torch sits in the fist: through the palm, a little inside it, along the knuckle line
        c_ref = add(mulv(add(add(i1, m1), add(r1, p1)), 0.25), mulv(palm, 2.6))
        c_ = add(hand_pos, qrot(WD, sub(c_ref, hp)))
        axis = norm(qrot(WD, k_ref))
        TORCH.update({"centre": c_, "axis": axis, "back": add(c_, mulv(axis, -6.5)), "front": add(c_, mulv(axis, 10.5))})
        log("grip %s: torch centre %s axis %s, front %s" % (sd, [round(x, 1) for x in c_], [round(x, 2) for x in axis],
                                                             [round(x, 1) for x in TORCH["front"]]))

    grip("r")

    # local rotations: parent's (possibly new) component rotation inverted, times the bone's new one
    keys = {}
    for b in new_cs:
        par = str(comp.get_parent_bone(b))
        qpar = new_cs.get(par, tq(cs(par)))
        keys[b] = (tv(ps(b)), qmul(qinv(qpar), new_cs[b]))

    path = "%s/%s" % (OUT_PKG, OUT_NAME)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    fac = unreal.AnimSequenceFactory()
    fac.set_editor_property("target_skeleton", skel)
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(OUT_NAME, OUT_PKG, unreal.AnimSequence, fac)
    seq.set_editor_property("preview_pose_asset", None) if hasattr(seq, "preview_pose_asset") else None
    ctrl = seq.get_editor_property("controller")
    ctrl.open_bracket(unreal.Text("Nysa lamp pose"), False)
    if hasattr(ctrl, "initialize_model"): ctrl.initialize_model()
    ctrl.set_frame_rate(unreal.FrameRate(30, 1), False)
    ctrl.set_number_of_frames(unreal.FrameNumber(1), False)
    for b, (p, q) in keys.items():
        ctrl.add_bone_curve(b, False)
        pv = [unreal.Vector(*p)] * 2
        qv = [unreal.Quat(q[0], q[1], q[2], q[3])] * 2
        sv = [unreal.Vector(1, 1, 1)] * 2
        ok = ctrl.set_bone_track_keys(b, pv, qv, sv, False)
        log("keyed %s ok=%s" % (b, ok))
    if hasattr(ctrl, "notify_populated"): ctrl.notify_populated()
    ctrl.close_bracket(False)
    unreal.EditorAssetLibrary.save_loaded_asset(seq, False)

    # check: play it on the spare actor and read where the hands ended up
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    comp.set_animation(seq)
    comp.set_position(0.0, False)
    for fn_ in ("tick_animation", "refresh_bone_transforms"):
        if hasattr(comp, fn_):
            getattr(comp, fn_)(*((0.0, False) if fn_ == "tick_animation" else ()))
    got_r, got_l, head = tv(cs("hand_r")), tv(cs("hand_l")), tv(cs("head"))
    log("posed hand_r %s (wanted %s), hand_l %s, head %s" % ([round(x, 1) for x in got_r], [round(x, 1) for x in hand_r],
                                                            [round(x, 1) for x in got_l], [round(x, 1) for x in head]))
    json.dump({"hand_r": hand_r, "hand_l": hand_l, "head": REF["head"], "side_r": side_r, "wanted_r": hand_r,
               "arms": ARMS, "bones": REF, "torch": TORCH,
               "head_turn": HEAD_TURN, "head_axis": up_ax, "head_pivot": pivot},
              open("C:/LETHE/Saved/nysa_mh_pose.json", "w"), indent=1)
    act.destroy_actor()
    log("done")


_st = {"n": 0}


def _go(dt):
    _st["n"] += 1
    if _st["n"] == 90:
        unreal.unregister_slate_post_tick_callback(_st["h"])
        try:
            run()
        except Exception:  # noqa: BLE001
            import traceback
            log("ERROR\n" + traceback.format_exc())
        unreal.SystemLibrary.quit_editor()


_st["h"] = unreal.register_slate_post_tick_callback(_go)
