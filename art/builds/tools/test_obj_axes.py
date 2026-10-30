"""One-off probe: how does the OBJ importer map axes, winding and material groups? Logs and quits."""
import os
import unreal

SRC = "C:/LETHE/SourceArt/Test"
os.makedirs(SRC, exist_ok=True)
with open(SRC + "/AxisProbe.obj", "w") as f:
    f.write("v 10 0 0\nv 0 20 0\nv 0 0 30\nv 10 0 30\n")
    f.write("vt 0.1 0.2\nvt 0.3 0.4\nvt 0.5 0.6\nvt 0.7 0.8\n")
    f.write("usemtl Panel\nf 1/1 2/2 3/3\n")          # counter-clockwise seen from +(1,1,1) in OBJ space
    f.write("usemtl Bark\nf 1/1 3/3 4/4\n")

dest = "/Game/Lethe/Test/AxisProbe"
eal = unreal.EditorAssetLibrary
if eal.does_directory_exist(dest):
    eal.delete_directory(dest)
t = unreal.AssetImportTask()
t.set_editor_property("filename", SRC + "/AxisProbe.obj")
t.set_editor_property("destination_path", dest)
t.set_editor_property("automated", True)
t.set_editor_property("save", True)
t.set_editor_property("replace_existing", True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
sm = None
for p in eal.list_assets(dest, recursive=True):
    a = unreal.load_asset(p)
    if isinstance(a, unreal.StaticMesh):
        sm = a
out = []
if sm is None:
    out.append("no mesh imported")
else:
    out.append("slots: " + ", ".join(str(m.material_slot_name) for m in sm.static_materials))
    bb = sm.get_bounding_box()
    out.append("bounds min (%.2f, %.2f, %.2f) max (%.2f, %.2f, %.2f)" % (bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z))
    out.append("OBJ verts were (10,0,0) (0,20,0) (0,0,30) (10,0,30): extents 10 on x, 20 on y, 30 on z")
for line in out:
    unreal.log("LETHE probe: " + line)
with open("C:/LETHE/Saved/obj_probe.txt", "w") as f:
    f.write("\n".join(out))
unreal.SystemLibrary.quit_editor()
