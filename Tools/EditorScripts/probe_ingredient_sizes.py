# -*- coding: utf-8 -*-
"""核对：子系统类是否注册；六个食材网格赋给 BP_Ingredient 后的实际渲染尺寸与缩放。"""
import json
import os
import traceback

import unreal

MESHES = {
    "欧芹": "/Game/modularkitchen/modular-kitchen/kitchen/props/parsley",
    "洋葱": "/Game/modularkitchen/modular-kitchen/kitchen/props/onion",
    "调料": "/Game/modularkitchen/modular-kitchen/kitchen/props/condiment-bottle",
    "面团": "/Game/modularkitchen/modular-kitchen/kitchen/props/sourdough",
    "鱼头": "/Game/Food/Meshes/SM_Sardine_Half_1",
    "鱼": "/Game/Food/Meshes/SM_Sardine",
}
VARS = ["MeshRaw", "MeshWashed", "MeshCut", "MeshPieBase"]
rep = {"subsystem_class": None, "vars_writable": {}, "rows": [], "errors": []}


def log(m):
    unreal.log("[probe] " + str(m))


def main():
    try:
        k = unreal.load_class(None, "/Script/FoodAchievements.FoodIngredientVisualSubsystem")
        rep["subsystem_class"] = k.get_name() if k else "NOT_FOUND"
    except Exception:
        rep["subsystem_class"] = "ERR:" + traceback.format_exc()[-120:]
    log("子系统类: %s（Python 属性可见=%s）" %
        (rep["subsystem_class"], hasattr(unreal, "FoodIngredientVisualSubsystem")))

    bp = unreal.EditorAssetLibrary.load_asset("/Game/FoodGameplay/BP_Ingredient")
    cls = bp.generated_class()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    probe = eas.spawn_actor_from_class(cls, unreal.Vector(0, 0, 8000), unreal.Rotator(0, 0, 0))
    try:
        smc = probe.get_editor_property("static_mesh_component")
        rep["smc"] = {"name": smc.get_name() if smc else None,
                      "is_root": bool(smc and probe.get_editor_property("root_component") == smc)}
        log("StaticMeshComponent 属性 = %s（是根组件：%s）" % (rep["smc"]["name"], rep["smc"]["is_root"]))
        for v in VARS:
            try:
                probe.set_editor_property(v, None)
                rep["vars_writable"][v] = True
            except Exception as e:
                rep["vars_writable"][v] = str(e)[-70:]
        log("四个网格变量可写: %s" % rep["vars_writable"])
    finally:
        eas.destroy_actor(probe)

    for i, (name, path) in enumerate(MESHES.items()):
        a = eas.spawn_actor_from_class(cls, unreal.Vector(0, 150.0 * i, 8000), unreal.Rotator(0, 0, 0))
        if a is None:
            rep["rows"].append({"name": name, "error": "spawn 失败"})
            continue
        row = {"name": name, "mesh_path": path}
        try:
            mesh = unreal.EditorAssetLibrary.load_asset(path)
            comp = a.get_editor_property("static_mesh_component")
            raw = mesh.get_bounding_box()
            ext = raw.max - raw.min
            largest = max(ext.x, ext.y, ext.z)
            desired = min(max(largest, 8.0), 35.0)
            scale = desired / largest
            comp.set_editor_property("static_mesh", mesh)
            comp.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
            o, e = a.get_actor_bounds(False)
            row.update({"raw_size": [round(ext.x, 1), round(ext.y, 1), round(ext.z, 1)],
                        "scale": round(scale, 3),
                        "final_size": [round(e.x * 2, 1), round(e.y * 2, 1), round(e.z * 2, 1)],
                        "mesh_now": comp.get_editor_property("static_mesh").get_path_name().split("/")[-1]})
            log("%-4s 原始 %-22s scale=%.2f -> 渲染 %s cm" %
                (name, row["raw_size"], scale, row["final_size"]))
        except Exception:
            row["error"] = traceback.format_exc()[-200:]
            log("%-4s 失败: %s" % (name, row["error"]))
        rep["rows"].append(row)
        eas.destroy_actor(a)

    fp = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps", "probe_ingredient.json")
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
