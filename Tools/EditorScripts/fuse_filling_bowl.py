"""把 BP_FillingBowl（馅料碗）的碗体换成 pie_panzi 派壳外观。

- 只隐藏 `Bowl` 这个圆柱组件（底下的 `Table` 方盒保留当底座）
- 派壳按圆柱的**真实外径/高度**缩放，底面贴住圆柱底面，关闭碰撞
- 外壳 attach 到碗 Actor 上，碗动它跟着动
"""

import os
import json
import time
import traceback
import unreal

MAP = "/Game/0Input/map/Kitchen_white_final_supply"
SHELL = "/Game/0Input/mesh/pie_panzi"
OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")


def log(m):
    unreal.log("[bowl2] " + str(m))


def warn(m):
    unreal.log_warning("[bowl2] " + str(m))


def set_mesh(comp, path):
    m = unreal.EditorAssetLibrary.load_asset(path)
    if m is None:
        return False
    for prop in ("skeletal_mesh_asset", "skeletal_mesh"):
        try:
            comp.set_editor_property(prop, m)
            return True
        except Exception:
            continue
    return False


def world_loc(actor, comp):
    rel = comp.get_editor_property("relative_location")
    try:
        return actor.get_actor_transform().transform_location(rel)
    except Exception:
        p = actor.get_actor_location()
        return unreal.Vector(p.x + rel.x, p.y + rel.y, p.z + rel.z)


def main():
    rep = {"ts": time.strftime("%Y%m%d_%H%M%S"), "items": []}
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        warn("地图加载失败")
        return

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    before = [x.get_actor_label() for x in eas.get_all_level_actors()]
    log("动手前 Actor %d" % len(before))

    bowls = [a for a in eas.get_all_level_actors() if "FillingBowl" in a.get_class().get_name()]
    log("馅料碗实例 %d 个" % len(bowls))

    for a in bowls:
        row = {"label": a.get_actor_label(), "hidden": [], "shell": None, "comps": []}
        bowl_comp = None
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property("static_mesh")
            ws = c.get_world_scale()
            info = {"name": c.get_name(), "mesh": m.get_path_name() if m else None,
                    "world_scale": [round(ws.x, 2), round(ws.y, 2), round(ws.z, 2)]}
            if m:
                bb = m.get_bounding_box()
                info["size"] = [round((bb.max.x - bb.min.x) * ws.x, 1),
                                round((bb.max.y - bb.min.y) * ws.y, 1),
                                round((bb.max.z - bb.min.z) * ws.z, 1)]
            row["comps"].append(info)
            if c.get_name().lower().startswith("bowl"):
                bowl_comp = c
        if bowl_comp is None:
            warn("%s 找不到 Bowl 组件，跳过" % row["label"])
            rep["items"].append(row)
            continue

        m = bowl_comp.get_editor_property("static_mesh")
        bb = m.get_bounding_box()
        ws = bowl_comp.get_world_scale()
        dia = max((bb.max.x - bb.min.x) * ws.x, (bb.max.y - bb.min.y) * ws.y)
        hgt = (bb.max.z - bb.min.z) * ws.z
        ctr = world_loc(a, bowl_comp)
        bottom = ctr.z + bb.min.z * ws.z
        log("碗: 直径%.1f 高%.1f 中心(%.1f,%.1f,%.1f) 底面%.1f" % (dia, hgt, ctr.x, ctr.y, ctr.z, bottom))

        act = eas.spawn_actor_from_class(unreal.SkeletalMeshActor,
                                         unreal.Vector(ctr.x, ctr.y, bottom),
                                         a.get_actor_rotation())
        act.set_actor_label(a.get_actor_label() + "_壳")
        comp = act.get_component_by_class(unreal.SkeletalMeshComponent)
        if comp is None or not set_mesh(comp, SHELL):
            warn("派壳赋值失败，回滚本次")
            eas.destroy_actor(act)
            row["shell"] = "failed"
            rep["items"].append(row)
            continue

        o0, e0 = act.get_actor_bounds(False)
        nat_xy = max(e0.x * 2.0, e0.y * 2.0)
        k = dia / nat_xy if nat_xy > 0 else 1.0
        k = max(0.2, min(k, 6.0))
        act.set_actor_scale3d(unreal.Vector(k, k, k))

        o2, e2 = act.get_actor_bounds(False)
        dz = bottom - (o2.z - e2.z)
        p = act.get_actor_location()
        act.set_actor_location(unreal.Vector(p.x, p.y, p.z + dz), False, False)
        try:
            act.set_actor_enable_collision(False)
        except Exception:
            pass
        try:
            act.attach_to_actor(a, "", unreal.AttachmentRule.KEEP_WORLD,
                                unreal.AttachmentRule.KEEP_WORLD,
                                unreal.AttachmentRule.KEEP_WORLD, False)
            row["attached"] = True
        except Exception:
            warn("attach 失败: %s" % traceback.format_exc())

        try:
            bowl_comp.set_visibility(False, True)
            row["hidden"].append(bowl_comp.get_name())
        except Exception:
            warn("隐藏碗体失败")

        row["shell"] = {"scale": round(k, 2),
                        "size_cm": [round(e2.x * 2 * k, 1), round(e2.y * 2 * k, 1), round(e2.z * 2 * k, 1)],
                        "at": [round(p.x, 1), round(p.y, 1), round(bottom, 1)]}
        rep["items"].append(row)
        log("%-16s 隐藏%s 派壳 scale=%.2f 尺寸%s 位置%s" %
            (row["label"], row["hidden"], k, row["shell"]["size_cm"], row["shell"]["at"]))

    after = [x.get_actor_label() for x in eas.get_all_level_actors()]
    rep["total_before"] = len(before)
    rep["total_after"] = len(after)
    rep["diff"] = [x for x in after if x not in before]
    if rep["diff"]:
        log("新增 Actor: %s" % rep["diff"])

    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rep["saved"] = bool(unreal.EditorLoadingAndSavingUtils.save_map(w, MAP))
    log("保存 %s : %s（Actor %d）" % (MAP, rep["saved"], len(after)))
    fp = os.path.join(OUT_DIR, "bowl2_%s.json" % rep["ts"])
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
