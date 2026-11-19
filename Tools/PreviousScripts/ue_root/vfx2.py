# -*- coding: utf-8 -*-
"""重建 BP_ChopVFX_Demo 为正常蓝图，并预置 StaticMesh 组件（Cube + 白闪材质）。"""
import unreal
import traceback

LOG = r"D:\ue\vfx2_log.txt"
_lines = []


def log(s):
    _lines.append(str(s))
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(_lines))


def step(name, fn):
    try:
        r = fn()
        log("[OK]   %-28s -> %s" % (name, r))
        return r
    except Exception as e:
        log("[FAIL] %-28s -> %s" % (name, e))
        log(traceback.format_exc())
        return None


log("=== REBUILD START ===")
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
BP_DIR = "/Game/Blueprints"
BP_NAME = "BP_ChopVFX_Demo"
BP_PATH = BP_DIR + "/" + BP_NAME
MESH_PATH = "/Engine/BasicShapes/Cube.Cube"
MI_PATH = "/Game/Art/Materials/MI_HitFlash.MI_HitFlash"

# 1. 删掉旧的（纯数据蓝图）
step("delete old bp", lambda: EAL.delete_asset(BP_PATH))

# 2. 用正确方式重建：asset_class 传 None，让 factory 决定
def create_bp():
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor)
    bp = AT.create_asset(BP_NAME, BP_DIR, None, factory)
    if bp is None:
        raise RuntimeError("create_asset returned None")
    EAL.save_loaded_asset(bp)
    return bp


bp = step("create bp", create_bp)

# 3. 加 StaticMesh 组件
comp = None
if bp:
    def add_comp():
        sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        roots = sds.k2_gather_subobject_data_for_blueprint(bp)
        log("root handles: %d" % len(roots))
        root = roots[0]
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("parent_handle", root)
        params.set_editor_property("new_class", unreal.StaticMeshComponent)
        params.set_editor_property("blueprint_context", bp)
        handle, fail = sds.add_new_subobject(params)
        log("fail_reason: %s" % fail)
        return handle

    handle = step("add StaticMeshComponent", add_comp)

    if handle:
        def get_obj():
            sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            data = sds.k2_find_subobject_data_from_handle(handle)
            obj = None
            for fn_name in ("get_associated_object", "get_object", "get_object_for_blueprint"):
                if hasattr(unreal.SubobjectDataBlueprintFunctionLibrary, fn_name):
                    try:
                        obj = getattr(unreal.SubobjectDataBlueprintFunctionLibrary, fn_name)(data)
                        log("used %s -> %s" % (fn_name, obj))
                        if obj:
                            break
                    except Exception as e:
                        log("  %s err %s" % (fn_name, e))
            return obj

        comp = step("resolve component object", get_obj)

    if comp:
        step("set static mesh", lambda: comp.set_editor_property(
            "static_mesh", EAL.load_asset(MESH_PATH)))
        step("set material", lambda: comp.set_material(0, EAL.load_asset(MI_PATH)))
        step("set mobility movable", lambda: comp.set_editor_property(
            "mobility", unreal.ComponentMobility.MOVABLE))
        step("set collision profile", lambda: comp.set_collision_profile_name("BlockAll"))

    step("compile bp", lambda: unreal.BlueprintEditorLibrary.compile_blueprint(bp))
    step("save bp", lambda: EAL.save_loaded_asset(bp))

    # 确认它不再是纯数据蓝图
    def check_type():
        info = unreal.BlueprintEditorLibrary.get_blueprint_parent_class(bp)
        graphs = unreal.BlueprintEditorLibrary.list_graph_names(bp)
        return "parent=%s graphs=%s" % (info, graphs)
    step("check bp", check_type)

# 4. 检查材质节点是否连对
def check_mat():
    m = EAL.load_asset("/Game/Art/Materials/M_HitFlash.M_HitFlash")
    n = unreal.MaterialEditingLibrary.get_num_material_expressions(m)
    names = []
    for i in range(n):
        names.append(str(i))
    return "num_exprs=%s" % names


step("inspect M_HitFlash", check_mat)

log("=== REBUILD DONE ===")
