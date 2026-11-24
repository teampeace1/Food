# -*- coding: utf-8 -*-
"""只读核对：BP_Ingredient 的继承链、四个网格变量、显示组件，以及 6 个目标食材网格的尺寸与最终缩放。"""
import json
import os
import traceback

import unreal

BP_PATH = "/Game/FoodGameplay/BP_Ingredient"
MESHES = {
    "欧芹": "/Game/modularkitchen/modular-kitchen/kitchen/props/parsley",
    "洋葱": "/Game/modularkitchen/modular-kitchen/kitchen/props/onion",
    "调料": "/Game/modularkitchen/modular-kitchen/kitchen/props/condiment-bottle",
    "面团": "/Game/modularkitchen/modular-kitchen/kitchen/props/sourdough",
    "鱼头": "/Game/Food/Meshes/SM_Sardine_Half_1",
    "鱼": "/Game/Food/Meshes/SM_Sardine",
}
VARS = ["MeshRaw", "MeshWashed", "MeshCut", "MeshPieBase"]


def log(m):
    unreal.log("[ing] " + str(m))


def brief(v):
    return str(v)[:120]


def main():
    rep = {"chain": [], "props": {}, "comps": [], "meshes": {}, "errors": []}

    bp = unreal.EditorAssetLibrary.load_asset(BP_PATH)
    if bp is None:
        log("找不到 %s" % BP_PATH)
        return
    cls = bp.generated_class()
    log("BP 生成类名: %s" % cls.get_name())
    c = cls
    while c is not None:
        rep["chain"].append(c.get_name())
        log("  继承: %s" % c.get_name())
        try:
            c = c.get_parent_class()
        except Exception:
            break

    cdo = unreal.get_default_object(cls)
    for p in ["IngredientName"] + VARS:
        try:
            rep["props"][p] = brief(cdo.get_editor_property(p))
        except Exception as e:
            rep["props"][p] = "MISSING(%s)" % str(e)[:60]
        log("  属性 %-14s = %s" % (p, rep["props"][p]))

    try:
        root = cdo.get_editor_property("root_component")
        if root:
            log("  根组件: %s (%s)" % (root.get_name(), root.get_class().get_name()))
            rep["root"] = {"name": root.get_name(), "cls": root.get_class().get_name()}
    except Exception:
        rep["errors"].append("root: " + traceback.format_exc()[-200:])

    for comp in cdo.get_components_by_class(unreal.StaticMeshComponent):
        try:
            m = comp.get_editor_property("static_mesh")
            mp = m.get_path_name() if m else None
        except Exception:
            mp = None
        try:
            sc = comp.get_editor_property("relative_scale3d")
            scl = [round(sc.x, 3), round(sc.y, 3), round(sc.z, 3)]
        except Exception:
            scl = None
        rep["comps"].append({"name": comp.get_name(), "cls": comp.get_class().get_name(),
                             "mesh": mp, "scale": scl})
        log("  组件 %-10s %-26s mesh=%s scale=%s" % (comp.get_name(), comp.get_class().get_name(), mp, scl))

    for name, path in MESHES.items():
        a = unreal.EditorAssetLibrary.load_asset(path)
        row = {"path": path}
        if a is None:
            row["error"] = "load_asset 返回 None"
            log("  网格 %-4s 载入失败 %s" % (name, path))
        else:
            row["class"] = a.get_class().get_name()
            try:
                b = a.get_bounding_box()
                ext = b.max - b.min
                largest = max(ext.x, ext.y, ext.z)
                desired = min(max(largest, 8.0), 35.0)
                row.update({"size_cm": [round(ext.x, 1), round(ext.y, 1), round(ext.z, 1)],
                            "largest": round(largest, 1), "scale": round(desired / largest, 3),
                            "final_size": [round(ext.x * desired / largest, 1),
                                           round(ext.y * desired / largest, 1),
                                           round(ext.z * desired / largest, 1)]})
                log("  网格 %-4s %-11s 原始 %s cm -> scale %.2f -> 成品 %s" %
                    (name, row["class"], row["size_cm"], row["scale"], row["final_size"]))
            except Exception:
                row["error"] = traceback.format_exc()[-200:]
                log("  网格 %-4s 包围盒失败" % name)
        rep["meshes"][name] = row

    fp = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps", "ingredient_visual_check.json")
    json.dump(rep, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    log("报告: %s" % fp)


try:
    main()
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
