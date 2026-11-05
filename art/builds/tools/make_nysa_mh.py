"""
Builds Nysa as a MetaHuman (UE 5.8 MetaHuman Creator, Core Data required).
Run: launch the editor with env LETHE_AUTORUN=C:/LETHE/Scripts/make_nysa_mh.py
Steps: create /Game/Lethe/Characters/MH_Nysa, set skin, eyes, height, long dark curly hair, brows, lashes,
outfit; ask Epic's cloud service to rig the face and send the high-res textures (needs the editor's Epic
login); then build BP_MH_Nysa under /Game/Lethe/MetaHumans. Writes progress to Saved/mh_nysa.log.
Env: LETHE_MH_STAGE=edit stops before the cloud steps; LETHE_MH_KEEP=1 keeps the editor open at the end.
"""
import os
import traceback
import unreal

LOG = "C:/LETHE/Saved/mh_nysa.log"
PKG = "/Game/Lethe/Characters"
NAME = "MH_Nysa"
HAIR = os.environ.get("LETHE_MH_HAIR", "WI_Hair_L_AfroCurly")


def log(msg):
    unreal.log("LETHE nysa-mh: " + msg)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def load_or_create():
    path = "%s/%s.%s" % (PKG, NAME, NAME)
    if os.environ.get("LETHE_MH_FRESH") in ("1", "build"):
        for d_ in ("/Game/Lethe/MetaHumans",):
            if unreal.EditorAssetLibrary.does_directory_exist(d_):
                unreal.EditorAssetLibrary.delete_directory(d_)
        log("old build removed")
        if os.environ.get("LETHE_MH_FRESH") == "1" and unreal.EditorAssetLibrary.does_asset_exist(path):
            unreal.EditorAssetLibrary.delete_asset(path)
        log("fresh start: old character and build removed")
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        log("reusing " + path)
        return unreal.load_asset(path)
    ch = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=NAME, package_path=PKG, asset_class=unreal.MetaHumanCharacter,
        factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
    log("created " + path)
    return ch


def add_item(ch, slot, wi_path):
    wi = unreal.load_asset(wi_path)
    if not wi:
        log("missing wardrobe item " + wi_path)
        return None
    key = ch.internal_collection.try_add_item_from_wardrobe_item(slot, wi)
    ch.internal_collection.default_instance.try_add_slot_selection(
        unreal.MetaHumanPipelineSlotSelection(slot_name=slot, selected_item=key))
    log("added %s -> %s" % (slot, wi_path.rsplit("/", 1)[-1]))
    return key


def params_of(ch, key):
    return ch.internal_collection.default_instance.get_instance_parameters(
        item_path=unreal.MetaHumanPaletteItemPath(item_key=key))


def set_param(ch, key, name, kind, value):
    for p in params_of(ch, key):
        if str(p.name) == name:
            getattr(p, "set_" + kind)(value=value)
            log("  %s = %r" % (name, value))
            return True
    log("  no param %s (have: %s)" % (name, ", ".join(str(p.name) for p in params_of(ch, key))))
    return False


def edit(sub, ch):
    # skin: warm medium tone, a little rough (she's been out in the rain)
    sk = unreal.MetaHumanCharacterSkinProperties()
    sk.u, sk.v = float(os.environ.get("LETHE_MH_SKIN_U", "0.45")), float(os.environ.get("LETHE_MH_SKIN_V", "0.55"))
    sk.roughness = 0.9
    sk.show_top_underwear = True
    ss = unreal.MetaHumanCharacterSkinSettings()
    ss.skin = sk
    ch.preview_material_type = unreal.MetaHumanCharacterSkinPreviewMaterial.EDITABLE
    sub.commit_skin_settings(ch, ss)
    log("skin set")

    # eyes: dark brown
    try:
        es = ch.eyes_settings
        for eye in (es.eye_left, es.eye_right):
            eye.iris.primary_color_u, eye.iris.primary_color_v = 0.15, 0.2
        sub.commit_eyes_settings(ch, es)
        log("eyes set")
    except Exception as e:  # noqa: BLE001
        log("eyes skipped: %r" % e)

    # height about 1.70 m
    try:
        cons = sub.get_body_constraints(ch)
        for c in cons:
            if str(c.name).lower().replace(" ", "_") == "height":
                c.is_active = True
                c.target_measurement = float(os.environ.get("LETHE_MH_HEIGHT", "170"))
        sub.set_body_constraints(ch, cons)
        sub.commit_body_state(ch)
        log("height set")
    except Exception as e:  # noqa: BLE001
        log("height skipped: %r" % e)

    G = "/MetaHumanCharacter/Optional/Grooms/Bindings/"
    keys = {
        "Hair": add_item(ch, "Hair", G + "Hair/" + HAIR),
        "Eyebrows": add_item(ch, "Eyebrows", G + "Eyebrows/WI_Eyebrows_M_Natural"),
        "Eyelashes": add_item(ch, "Eyelashes", G + "Eyelashes/WI_Eyelashes_L_SlightCurl"),
        "Outfits": add_item(ch, "Outfits", "/MetaHumanCharacter/Optional/Clothing/WI_DefaultGarment"),
    }
    sub.assemble_for_preview(character=ch)
    for slot in ("Hair", "Eyebrows"):
        if keys[slot]:
            set_param(ch, keys[slot], "Melanin", "float", 0.92)
    if keys["Outfits"]:
        log("outfit params: " + ", ".join(str(p.name) for p in params_of(ch, keys["Outfits"])))
    unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
    log("edit stage saved")


def cloud_and_build(sub, ch):
    if os.environ.get("LETHE_MH_STAGE", "") == "build" and sub.can_build_meta_human(ch, False):
        return build_only(sub, ch)
    rq = unreal.MetaHumanCharacterAutoRiggingRequestParams()
    rq.blocking, rq.report_progress = True, False
    rq.rig_type = unreal.MetaHumanRigType.JOINTS_ONLY
    log("requesting auto-rig (Epic cloud)...")
    sub.request_auto_rigging(ch, rq)
    tq = unreal.MetaHumanCharacterTextureRequestParams()
    tq.blocking, tq.report_progress = True, False
    log("requesting texture sources (Epic cloud)...")
    sub.request_texture_sources(ch, tq)
    unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
    return build_only(sub, ch)


def build_only(sub, ch):
    if not sub.can_build_meta_human(ch, True):
        log("CANNOT BUILD: rig or textures missing (see LogMetaHuman lines in LETHE.log; likely needs the Epic login)")
        return False
    bp = unreal.MetaHumanCharacterEditorBuildParameters()
    bp.pipeline_type = unreal.MetaHumanDefaultPipelineType.CINEMATIC
    bp.pipeline_quality = unreal.MetaHumanQualityLevel.HIGH
    bp.absolute_build_path = "/Game/Lethe/MetaHumans"
    bp.common_folder_path = "/Game/Lethe/MetaHumans/Common"
    bp.enable_wardrobe_item_validation = False
    log("building...")
    try:
        sub.build_meta_human(character=ch, params=bp)
    except Exception as e:  # noqa: BLE001  (control-rig "cannot break link" log errors surface as exceptions)
        log("build raised (checking output anyway): %s" % str(e).splitlines()[0][:200])
    if not unreal.EditorAssetLibrary.does_asset_exist("/Game/Lethe/MetaHumans/%s/BP_%s" % (NAME, NAME)):
        log("no BP produced")
        return False
    unreal.EditorAssetLibrary.save_directory("/Game/Lethe/MetaHumans", only_if_is_dirty=False, recursive=True)
    log("BUILD DONE")
    return True


def run():
    open(LOG, "w").close()
    sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    ch = load_or_create()
    ok = False
    if not sub.try_add_object_to_edit(ch):
        log("could not open the character for editing")
    else:
        try:
            if os.environ.get("LETHE_MH_STAGE", "") != "build":
                edit(sub, ch)
            if os.environ.get("LETHE_MH_STAGE", "") != "edit":
                ok = cloud_and_build(sub, ch)
            else:
                ok = True
        except Exception:  # noqa: BLE001
            log("ERROR\n" + traceback.format_exc())
        finally:
            if sub.is_object_added_for_editing(ch):
                sub.remove_object_to_edit(ch)
    log("finished ok=%s" % ok)
    if ok and os.environ.get("LETHE_MH_KEEP", "") != "1":
        unreal.SystemLibrary.quit_editor()


_st = {"n": 0}


def _go(dt):
    _st["n"] += 1
    if _st["n"] == 120:  # let the editor finish starting up
        unreal.unregister_slate_post_tick_callback(_st["h"])
        run()


_st["h"] = unreal.register_slate_post_tick_callback(_go)
