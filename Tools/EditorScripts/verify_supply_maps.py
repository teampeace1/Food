"""对比 final 与 final_supply 的 Actor 名单，并检查供应点的碰撞/名称字段。"""

import os
import json
import time
import traceback
import unreal

A = "/Game/0Input/map/Kitchen_white_final"
B = "/Game/0Input/map/Kitchen_white_final_supply"
OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")


def log(m):
    unreal.log("[verify] " + str(m))


def snap():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    out = {}
    for a in eas.get_all_level_actors():
        out[a.get_actor_label()] = a.get_class().get_name()
    return out


def supply_info():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rows = []
    for a in eas.get_all_level_actors():
        n = a.get_class().get_name()
        if "IngredientSupply" not in n:
            continue
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        row = {"label": a.get_actor_label()}
        try:
            row["ingredient_name"] = str(a.get_editor_property("ingredient_name"))
        except Exception:
            row["ingredient_name"] = None
        if c:
            m = c.get_editor_property("static_mesh")
            row["mesh"] = m.get_path_name() if m else None
            try:
                row["profile"] = c.get_collision_profile_name()
            except Exception:
                row["profile"] = None
            try:
                row["collision_enabled"] = str(c.get_collision_enabled())
            except Exception:
                row["collision_enabled"] = None
            try:
                row["simple_collision"] = bool(m.get_editor_property("has_simple_collision"))
            except Exception:
                row["simple_collision"] = None
        rows.append(row)
    return rows


def main():
    rep = {"ts": time.strftime("%Y%m%d_%H%M%S")}
    unreal.EditorLoadingAndSavingUtils.load_map(A)
    sa = snap()
    rep["a_count"] = len(sa)
    rep["a_supply"] = supply_info()

    unreal.EditorLoadingAndSavingUtils.load_map(B)
    sb = snap()
    rep["b_count"] = len(sb)
    rep["b_supply"] = supply_info()

    rep["missing_in_b"] = sorted(set(sa) - set(sb))
    rep["added_in_b"] = sorted(set(sb) - set(sa))

    fp = os.path.join(OUT_DIR, "verify_%s.json" % rep["ts"])

    log("final=%d  supply=%d" % (len(sa), len(sb)))
    log("B 缺失: %s" % rep["missing_in_b"])
    log("B 新增: %s" % rep["added_in_b"])
    for r in rep["b_supply"]:
        log("  %-14s name=%-8s prof=%-14s simple=%s mesh=%s" %
            (r["label"], r.get("ingredient_name"), r.get("profile"),
             r.get("simple_collision"), (r.get("mesh") or "").split("/")[-1]))
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, default=str)
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
