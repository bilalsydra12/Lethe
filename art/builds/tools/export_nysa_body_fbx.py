"""
Exports Nysa's MetaHuman body (and face) with her lamp pose to FBX, so Blender can drape cloth on her exact posed body.
Writes SourceArt/Nysa/blender/NysaBody_pose.fbx (body mesh + AS_Nysa_LampPose) and NysaFace.fbx (face mesh, rest pose).
Run: LETHE_AUTORUN=C:/LETHE/Scripts/export_nysa_body_fbx.py   Log: Saved/export_nysa_body.log
"""
import os
import traceback
import unreal

LOG = "C:/LETHE/Saved/export_nysa_body.log"
OUT = "C:/LETHE/SourceArt/Nysa/blender"
BODY = "/Game/Lethe/MetaHumans/MH_Nysa/Body/SKM_MH_Nysa_BodyMesh"
ANIM = "/Game/Lethe/Characters/AS_Nysa_LampPose"
FACE = "/Game/Lethe/MetaHumans/Common/Face/SKM_Face"


def log(m):
    unreal.log("LETHE export-body: " + m)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(m + "\n")


def export(obj, path, opts):
    t = unreal.AssetExportTask()
    t.object = obj
    t.filename = path
    t.automated = True
    t.prompt = False
    t.replace_identical = True
    t.options = opts
    ok = unreal.Exporter.run_asset_export_task(t)
    log("%s -> %s : %s (%s bytes)" % (obj.get_path_name(), path, ok, os.path.getsize(path) if os.path.exists(path) else 0))
    for e in t.errors or []:
        log("   error: %s" % e)


def main():
    open(LOG, "w").close()
    os.makedirs(OUT, exist_ok=True)
    o = unreal.FbxExportOption()
    for k, v in (("ascii", False), ("export_morph_targets", False), ("export_preview_mesh", True),
                 ("level_of_detail", False), ("collision", False), ("vertex_color", False),
                 ("map_skeletal_motion_to_root", False), ("export_local_time", True)):
        try:
            o.set_editor_property(k, v)
        except Exception as e:  # noqa: BLE001
            log("option %s: %s" % (k, e))
    anim = unreal.load_asset(ANIM)
    body = unreal.load_asset(BODY)
    log("anim %s body %s" % (anim, body))
    if anim:
        try:
            anim.set_editor_property("preview_pose_asset", None)
        except Exception:  # noqa: BLE001
            pass
        try:
            anim.get_editor_property("skeleton").set_preview_mesh(body)
        except Exception as e:  # noqa: BLE001
            log("set preview mesh: %s" % e)
        export(anim, OUT + "/NysaBody_pose.fbx", o)
    if body:
        export(body, OUT + "/NysaBody_rest.fbx", o)
    face = unreal.load_asset(FACE)
    if face:
        export(face, OUT + "/NysaFace_rest.fbx", o)


try:
    main()
    log("done")
except Exception:  # noqa: BLE001
    log("ERROR\n" + traceback.format_exc())
unreal.SystemLibrary.quit_editor()
