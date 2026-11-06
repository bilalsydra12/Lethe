"""
Sets Nysa's hair and eyebrow colour on the MetaHuman character (Melanin / Redness instance parameters, which only
exist once the preview collection has been assembled, a few frames after asking for it), then rebuilds BP_MH_Nysa.
Run: LETHE_AUTORUN=C:/LETHE/Scripts/make_nysa_mh_hair.py   Log: Saved/mh_nysa_hair.log
Env: LETHE_HAIR_MELANIN (default 0.92), LETHE_HAIR_RED (default 0.25)
"""
import os
import traceback
import unreal

LOG = "C:/LETHE/Saved/mh_nysa_hair.log"
CH = "/Game/Lethe/Characters/MH_Nysa.MH_Nysa"
WANT = {"Melanin": float(os.environ.get("LETHE_HAIR_MELANIN", "0.92")), "Redness": float(os.environ.get("LETHE_HAIR_RED", "0.25"))}
eal = unreal.EditorAssetLibrary


def log(m):
    unreal.log("LETHE nysa-hair: " + m)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(m + "\n")


st = {"n": 0, "keys": {}, "done": set(), "ch": None, "sub": None}


def start():
    open(LOG, "w").close()
    sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    ch = unreal.load_asset(CH)
    if not sub.try_add_object_to_edit(ch):
        raise RuntimeError("cannot edit character")
    swap = os.environ.get("LETHE_MH_HAIR_ITEM", "")
    if swap:
        # change the hairstyle: add the wardrobe item and make it the Hair slot's one selection
        wi = unreal.load_asset("/MetaHumanCharacter/Optional/Grooms/Bindings/Hair/" + swap)
        key = ch.internal_collection.try_add_item_from_wardrobe_item("Hair", wi)
        ch.internal_collection.default_instance.set_single_slot_selection(slot_name="Hair", item_key=key)
        log("hair swapped to %s" % swap)
    sub.assemble_for_preview(character=ch)
    for sd in ch.internal_collection.default_instance.get_slot_selection_data():
        s = sd.selection
        if str(s.slot_name) in ("Hair", "Eyebrows"):
            st["keys"][str(s.slot_name)] = s.selected_item
    log("slots found: %s" % list(st["keys"]))
    st["ch"], st["sub"] = ch, sub


def instances():
    ch, sub = st["ch"], st["sub"]
    out = [("internal", ch.internal_collection.default_instance)]
    try:
        pc = sub.get_preview_collection(ch)
        if pc:
            out.append(("preview", pc.default_instance))
    except Exception as e:  # noqa: BLE001
        log("no preview collection: %s" % e)
    return out


def try_params():
    ch = st["ch"]
    if st["n"] % 200 == 0:
        for nm, inst in instances():
            try:
                paths = inst.get_instance_parameter_item_paths()
                log("%s instance: assembled %s, parameter item paths %s" % (nm, inst.is_assembled(), [str(p) for p in paths]))
            except Exception as e:  # noqa: BLE001
                log("%s instance query failed: %s" % (nm, e))
    if "Hair" not in st["done"]:
        # the hair's parameters can sit under an item path we did not key: find it by its ombre controls (only hair has them)
        for nm, inst in instances():
            for ip in inst.get_instance_parameter_item_paths():
                ps = inst.get_instance_parameters(item_path=ip)
                if any(str(p.name) == "bUseOmbre" for p in ps):
                    for p in ps:
                        if str(p.name) in WANT:
                            p.set_float(value=WANT[str(p.name)])
                            log("  Hair.%s = %s (found by its ombre controls on the %s instance)" % (p.name, WANT[str(p.name)], nm))
                    st["done"].add("Hair")
                    break
            if "Hair" in st["done"]:
                break
    for slot, key in st["keys"].items():
        if slot in st["done"]:
            continue
        ps = []
        for nm, inst in instances():
            ps = inst.get_instance_parameters(item_path=unreal.MetaHumanPaletteItemPath(item_key=key))
            if ps:
                log("%s: parameters found on the %s instance" % (slot, nm))
                break
        if not ps:
            continue
        log("%s params: %s" % (slot, ", ".join(str(p.name) for p in ps)))
        for p in ps:
            if str(p.name) in WANT:
                p.set_float(value=WANT[str(p.name)])
                log("  %s.%s = %s" % (slot, p.name, WANT[str(p.name)]))
        st["done"].add(slot)


def finish():
    ch, sub = st["ch"], st["sub"]
    eal.save_loaded_asset(ch, only_if_is_dirty=False)
    if len(st["done"]) < len(st["keys"]):
        log("WARNING: parameters never appeared for %s" % [k for k in st["keys"] if k not in st["done"]])
    if eal.does_directory_exist("/Game/Lethe/MetaHumans"):
        eal.delete_directory("/Game/Lethe/MetaHumans")
    bp = unreal.MetaHumanCharacterEditorBuildParameters()
    bp.pipeline_type = unreal.MetaHumanDefaultPipelineType.CINEMATIC
    bp.pipeline_quality = unreal.MetaHumanQualityLevel.HIGH
    bp.absolute_build_path = "/Game/Lethe/MetaHumans"
    bp.common_folder_path = "/Game/Lethe/MetaHumans/Common"
    bp.enable_wardrobe_item_validation = False
    try:
        sub.build_meta_human(character=ch, params=bp)
    except Exception as e:  # noqa: BLE001  (control-rig link warnings surface as exceptions; the build still completes)
        log("build raised: %s" % str(e).splitlines()[0][:160])
    eal.save_directory("/Game/Lethe/MetaHumans", only_if_is_dirty=False, recursive=True)
    log("built: %s" % eal.does_asset_exist("/Game/Lethe/MetaHumans/MH_Nysa/BP_MH_Nysa"))
    if sub.is_object_added_for_editing(ch):
        sub.remove_object_to_edit(ch)


def tick(dt):
    st["n"] += 1
    n = st["n"]
    try:
        if n == 120:
            start()
        elif n > 120 and n % 20 == 0 and st["ch"]:
            try_params()
            if len(st["done"]) == len(st["keys"]) or n > 1500:
                unreal.unregister_slate_post_tick_callback(st["h"])
                finish()
                log("finished")
                unreal.SystemLibrary.quit_editor()
    except Exception:  # noqa: BLE001
        log("ERROR\n" + traceback.format_exc())
        unreal.unregister_slate_post_tick_callback(st["h"])


st["h"] = unreal.register_slate_post_tick_callback(tick)
