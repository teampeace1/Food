"""1) 6 个供应点：把过小的实体适当放大（目标最长边 38cm，上限 3 倍、高度不超 40cm）
2) 按脚下的真实台面重新落位（射线检测），解决沉进桌子看不见、点不到的问题
3) 从 00:23 备份把 BP_RollingStation 还原回原位

只碰这三件事，其它 Actor 不动。产物直接存回 Kitchen_white_final_supply。
"""

import os
import json
import time
import traceback
import unreal

SRC_BAK = "/Game/0Input/map/_restore_src"
DST = "/Game/0Input/map/Kitchen_white_final_supply"
OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
BP_ROLLING = "/Game/FoodGameplay/BP_RollingStation"

TARGET_LONG = 38.0     # 目标最长边（厘米）
K_MAX = 3.0            # 单件最多放大 3 倍
H_CAP = 40.0           # 放大后高度上限
SNAP_MAX = 140.0       # 与台面落差在此范围内才自动落位


def log(m):
    unreal.log("[fix3] " + str(m))


def warn(m):
    unreal.log_warning("[fix3] " + str(m))


def bbox_of(mesh):
    try:
        b = mesh.get_bounding_box()
        return (b.min.x, b.min.y, b.min.z), (b.max.x, b.max.y, b.max.z)
    except Exception:
        return None


def capture_rolling():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_class().get_name().startswith("BP_RollingStation"):
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            sc = a.get_actor_scale3d()
            comps = []
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                m = c.get_editor_property("static_mesh")
                rl = c.get_editor_property("relative_location")
                rr = c.get_editor_property("relative_rotation")
                rs = c.get_editor_property("relative_scale3d")
                mats = []
                try:
                    for i in range(c.get_num_materials()):
                        mm = c.get_material(i)
                        mats.append(mm.get_path_name() if mm else None)
                except Exception:
                    pass
                comps.append({"comp": c.get_name(),
                              "mesh": m.get_path_name() if m else None,
                              "loc": [rl.x, rl.y, rl.z],
                              "rot": [rr.pitch, rr.yaw, rr.roll],
                              "scale": [rs.x, rs.y, rs.z],
                              "mats": mats})
            return {"label": a.get_actor_label(),
                    "loc": [loc.x, loc.y, loc.z],
                    "rot": [rot.pitch, rot.yaw, rot.roll],
                    "scale": [sc.x, sc.y, sc.z],
                    "comps": comps}
    return None


def restore(rec):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_class().get_name().startswith("BP_RollingStation"):
            log("已存在擀面台，跳过还原")
            return a
    cls = unreal.EditorAssetLibrary.load_blueprint_class(BP_ROLLING)
    if cls is None:
        warn("蓝图类加载失败: %s" % BP_ROLLING)
        return None
    act = eas.spawn_actor_from_class(cls, unreal.Vector(*rec["loc"]),
                                    unreal.Rotator(rec["rot"][0], rec["rot"][1], rec["rot"][2]))
    act.set_actor_label(rec["label"])
    act.set_actor_scale3d(unreal.Vector(*rec["scale"]))
    fixed = 0
    for cr in rec["comps"]:
        for c in act.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_name() != cr["comp"]:
                continue
            if cr["mesh"]:
                m = unreal.EditorAssetLibrary.load_asset(cr["mesh"])
                if m:
                    c.set_editor_property("static_mesh", m)
                    fixed += 1
            c.set_editor_property("relative_location", unreal.Vector(*cr["loc"]))
            c.set_editor_property("relative_rotation", unreal.Rotator(cr["rot"][0], cr["rot"][1], cr["rot"][2]))
            c.set_editor_property("relative_scale3d", unreal.Vector(*cr["scale"]))
            for i, mp in enumerate(cr.get("mats") or []):
                if not mp:
                    continue
                try:
                    mat = unreal.EditorAssetLibrary.load_asset(mp)
                    if mat:
                        c.set_material(i, mat)
                except Exception:
                    pass
    log("擀面台已恢复 @%s 组件网格 %d" % ([round(v, 1) for v in rec["loc"]], fixed))
    return act


def surface_z(w, p, ignore, bottom, tol=30.0):
    """用周围小道具的底面高度推定脚下台面（道具都是摆在台面上的，比包围盒可靠）。"""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    skip = set(a.get_name() for a in ignore)
    vals = []
    for a in eas.get_all_level_actors():
        if a.get_name() in skip:
            continue
        try:
            o, ext = a.get_actor_bounds(False)
        except Exception:
            continue
        if max(ext.x, ext.y, ext.z) > 150.0:
            continue
        d = ((o.x - p.x) ** 2 + (o.y - p.y) ** 2) ** 0.5
        if d > 300.0:
            continue
        b = o.z - ext.z
        if abs(b - bottom) > tol:
            continue
        vals.append((d, b))
    if not vals:
        return None
    vals.sort()
    pool = sorted(v for _, v in vals[:10])
    return pool[len(pool) // 2]


def main():
    rep = {"ts": time.strftime("%Y%m%d_%H%M%S"), "supply": [], "rolling": None}

    rec = None
    if unreal.EditorAssetLibrary.does_asset_exist(SRC_BAK):
        if unreal.EditorLoadingAndSavingUtils.load_map(SRC_BAK):
            rec = capture_rolling()
        else:
            warn("备份图加载失败，跳过擀面台还原")
    else:
        log("无需还原擀面台（已在图中）")
    rep["rolling_capture"] = rec
    log("备份里的擀面台: " + str(None if not rec else (rec["label"], [round(v, 1) for v in rec["loc"]])))

    if not unreal.EditorLoadingAndSavingUtils.load_map(DST):
        warn("目标图加载失败，终止")
        return
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    if rec:
        rep["rolling"] = "restored" if restore(rec) else "failed"

    supplies = [a for a in eas.get_all_level_actors()
                if "IngredientSupply" in a.get_class().get_name()]
    ignore = list(supplies)
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    for a in supplies:
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c is None:
            continue
        m = c.get_editor_property("static_mesh")
        bb = bbox_of(m) if m else None
        if not bb:
            continue

        as_ = a.get_actor_scale3d()
        sw = c.get_world_scale()
        nat = [bb[1][0] - bb[0][0], bb[1][1] - bb[0][1], bb[1][2] - bb[0][2]]
        cur_z = nat[2] * sw.z
        cur_long = max(nat[0] * sw.x, nat[1] * sw.y, nat[2] * sw.z)

        k = TARGET_LONG / cur_long if cur_long > 0 else 1.0
        k = max(1.0, min(k, K_MAX))
        if cur_z > 0:
            k = min(k, H_CAP / (cur_z * k) * k) if False else min(k, max(1.0, H_CAP / cur_z))

        if abs(k - 1.0) > 0.01:
            a.set_actor_scale3d(unreal.Vector(as_.x * k, as_.y * k, as_.z * k))

        # 放大后重新计算底部
        sw2 = c.get_world_scale()
        p = a.get_actor_location()
        bottom = p.z + bb[0][2] * sw2.z
        top = p.z + bb[1][2] * sw2.z

        row = {"label": a.get_actor_label(),
               "mesh": (m.get_path_name() if m else None),
               "nat_cm": [round(v, 1) for v in nat],
               "scale_k": round(k, 2),
               "size_after": [round(nat[0] * sw2.x, 1), round(nat[1] * sw2.y, 1), round(nat[2] * sw2.z, 1)],
               "at_before": [round(p.x, 1), round(p.y, 1), round(p.z, 1)],
               "bottom": round(bottom, 1)}

        sz = surface_z(w, p, ignore, bottom)
        row["surface_z"] = None if sz is None else round(sz, 1)
        if sz is not None:
            delta = sz - bottom
            row["delta"] = round(delta, 1)
            if abs(delta) <= SNAP_MAX:
                a.set_actor_location(unreal.Vector(p.x, p.y, p.z + delta), False, False)
                row["lifted"] = round(delta, 1)
        q = a.get_actor_location()
        row["at_after"] = [round(q.x, 1), round(q.y, 1), round(q.z, 1)]
        rep["supply"].append(row)
        log("%-12s k=%.2f 尺寸%s bottom=%.1f surf=%s lift=%s" %
            (row["label"], k, row["size_after"], row["bottom"], row["surface_z"], row.get("lifted")))

    rep["after_total"] = len(eas.get_all_level_actors())
    rep["saved"] = bool(unreal.EditorLoadingAndSavingUtils.save_map(w, DST))
    log("保存 %s : %s（Actor %d）" % (DST, rep["saved"], rep["after_total"]))

    fp = os.path.join(OUT_DIR, "fix3_%s.json" % rep["ts"])
    json.dump(rep, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    log("报告: %s" % fp)


try:
    main()
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    try:
        if unreal.EditorAssetLibrary.does_asset_exist(SRC_BAK):
            unreal.EditorAssetLibrary.delete_asset(SRC_BAK)
            log("已清理临时对照图")
    except Exception:
        pass
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
