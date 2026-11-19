# -*- coding: utf-8 -*-
"""创建切菜特效所需的基础资产：白闪材质、碎屑材质、演示蓝图壳子。"""
import unreal
import traceback

LOG = r"D:\ue\vfx_log.txt"
_lines = []


def log(s):
    _lines.append(str(s))
    try:
        with open(LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(_lines))
    except Exception:
        pass


def step(name, fn):
    try:
        r = fn()
        log("[OK]   %s -> %s" % (name, r))
        return r
    except Exception as e:
        log("[FAIL] %s -> %s" % (name, e))
        log(traceback.format_exc())
        return None


log("=== VFX SETUP START ===")

AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

MAT_DIR = "/Game/Art/Materials"
FX_DIR = "/Game/FX"
BP_DIR = "/Game/Blueprints"

for d in (MAT_DIR, FX_DIR, BP_DIR):
    step("make_dir " + d, lambda d=d: EAL.make_directory(d))


def make_material(name, emissive_color, param_name, default_val):
    path = MAT_DIR + "/" + name
    if EAL.does_asset_exist(path):
        log("skip existing " + path)
        return None
    factory = unreal.MaterialFactoryNew()
    mat = AT.create_asset(name, MAT_DIR, unreal.Material, factory)
    if mat is None:
        raise RuntimeError("create_asset returned None")
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", True)

    param = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -520, 0)
    param.set_editor_property("parameter_name", param_name)
    param.set_editor_property("default_value", float(default_val))

    const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -520, 180)
    const.set_editor_property("constant", unreal.LinearColor(*emissive_color))

    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -280, 80)
    MEL.connect_material_expressions(param, "", mul, "A")
    MEL.connect_material_expressions(const, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return path


step("M_HitFlash", lambda: make_material("M_HitFlash", (1.0, 0.96, 0.88, 1.0), "Flash", 0.0))
step("M_FX_Debris", lambda: make_material("M_FX_Debris", (0.85, 0.68, 0.42, 1.0), "Tint", 1.0))


def make_mi(name, parent_path):
    path = MAT_DIR + "/" + name
    if EAL.does_asset_exist(path):
        log("skip existing " + path)
        return None
    parent = EAL.load_asset(parent_path)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = AT.create_asset(name, MAT_DIR, unreal.MaterialInstanceConstant, factory)
    MEL.set_material_instance_parent(mi, parent)
    EAL.save_loaded_asset(mi)
    return path


step("MI_HitFlash", lambda: make_mi("MI_HitFlash", MAT_DIR + "/M_HitFlash"))
step("MI_FX_Debris", lambda: make_mi("MI_FX_Debris", MAT_DIR + "/M_FX_Debris"))


def make_bp(name, parent_class):
    path = BP_DIR + "/" + name
    if EAL.does_asset_exist(path):
        log("skip existing " + path)
        return None
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    bp = AT.create_asset(name, BP_DIR, unreal.Blueprint, factory)
    EAL.save_loaded_asset(bp)
    return path


step("BP_ChopVFX_Demo", lambda: make_bp("BP_ChopVFX_Demo", unreal.Actor))

# ---- 能力探测：看能不能用脚本连蓝图节点 ----
log("--- capability probe ---")
for name in ("BlueprintEditorLibrary", "K2Node_CallFunction", "K2Node_Event",
             "NiagaraSystemFactoryNew", "NiagaraEditorUtilities", "NiagaraFunctionLibrary"):
    log("has %-26s = %s" % (name, hasattr(unreal, name)))

if hasattr(unreal, "BlueprintEditorLibrary"):
    fns = [f for f in dir(unreal.BlueprintEditorLibrary) if not f.startswith("_")]
    log("BlueprintEditorLibrary funcs: " + ", ".join(fns))

if hasattr(unreal, "NiagaraEditorUtilities"):
    fns = [f for f in dir(unreal.NiagaraEditorUtilities) if not f.startswith("_")]
    log("NiagaraEditorUtilities funcs: " + ", ".join(fns))

# 列出工程里现有的材质，确认路径
log("--- existing assets in /Game ---")
for root in ("/Game/Art", "/Game/FX", "/Game/Blueprints"):
    try:
        log("%s : %s" % (root, EAL.list_assets(root, recursive=True)))
    except Exception as e:
        log("%s err %s" % (root, e))

log("=== VFX SETUP DONE ===")
