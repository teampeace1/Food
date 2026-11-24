# -*- coding: utf-8 -*-
"""隐藏 BP_FillingBowl 的 Table（方块底座）渲染，保留碰撞；派壳落到真实台面。"""
import json
import os
import time
import traceback

import unreal

MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT_DIR = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
SNAP_MIN, SNAP_MAX = 5.0, 120.0
EXCL = ("Light", "Sky", "Decal", "PlayerStart", "Character", "Ocean",
        "Camera", "Fog", "Volume", "PostProcess", "Effect")


def log(m):
    unreal.log("[hide] " + str(m))


def warn(m):
    unreal.log_warning("[hide] " + str(m))


def vec(v):
    return [round(float(v.x), 1), round(float(v.y), 1), round(float(v.z), 1)]


def mesh_of(comp):
    try:
        m = comp.get_editor_property("static_mesh")
        return m.get_path_name() if m else None
    except Exception:
        return None


def surface_z(acts, skip, ref_bottom, radius=320.0):
    """用周边小道具的底面中位数推定脚下台面高度（这些道具都是摆在台面上的）。"""
    vals = []
    for a in acts:
        if a.get_name() in skip:
            continue
        cn = a.get_class().get_name()
        if any(k in cn for k in EXCL):
            continue
        try:
            o, e = a.get_actor_bounds(False)
        except Exception:
            continue
        if max(e.x, e.y, e.z) > 120.0:
            continue
        if ((o.x - P[0]) ** 2 + (o.y - P[1]) ** 2) ** 0.5 > radius:
            continue
        b = o.z - e.z
        if not (ref_bottom - 120.0 <= b <= ref_bottom + 10.0):
            continue
        vals.append(round(b, 1))
    if not vals:
        return None, []
    vals.sort()
    return vals[len(vals) // 2], vals


P = [1110.0, 3550.0]
rep = {"ts": time.strftime("%Y%m%d_%H%M%S"), "hidden": [], "shell": None, "props": []}

try:
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        warn("地图加载失败")
    else:
        log("地图已加载 %s" % MAP)
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        acts = eas.get_all_level_actors()
        bowls = [a for a in acts if "FillingBowl" in a.get_class().get_name()]
        shells = [a for a in acts if a.get_actor_label().endswith("_壳")]
        log("馅料碗 %d，壳 %d，总 Actor %d" % (len(bowls), len(shells), len(acts)))

        skip = set(a.get_name() for a in bowls) | set(a.get_name() for a in shells)

        for b in bowls:
            P = [b.get_actor_location().x, b.get_actor_location().y]
            for c in b.get_components_by_class(unreal.StaticMeshComponent):
                n = c.get_name()
                rep.setdefault("comps", []).append({"name": n, "mesh": mesh_of(c)})
                if "Table" not in n:
                    continue
                try:
                    c.set_visibility(False, True)
                    rep["hidden"].append(n)
                    log("%s 的 %s(%s) 已隐藏渲染（碰撞保留）" % (b.get_actor_label(), n, mesh_of(c)))
                except Exception:
                    warn("隐藏 %s 失败: %s" % (n, traceback.format_exc()))

        for sh in shells:
            o, e = sh.get_actor_bounds(False)
            bottom = o.z - e.z
            sz, vals = surface_z(acts, skip, bottom)
            rep["props"] = vals
            log("壳 %s 底面 %.1f，周边道具底面 %d 个，中位数 %s" %
                (sh.get_actor_label(), bottom, len(vals), sz))
            if sz is None:
                warn("没找到参照道具，壳保持原位")
                rep["shell"] = {"label": sh.get_actor_label(), "bottom": round(bottom, 1), "dropped": 0.0}
                continue
            gap = bottom - sz
            if SNAP_MIN < gap <= SNAP_MAX:
                p = sh.get_actor_location()
                sh.set_actor_location(unreal.Vector(p.x, p.y, p.z - gap), False, True)
                o2, e2 = sh.get_actor_bounds(False)
                log("派壳落到台面 %.1f（下降 %.1f cm），新底面 %.1f" % (sz, gap, o2.z - e2.z))
                rep["shell"] = {"label": sh.get_actor_label(), "bottom_before": round(bottom, 1),
                                "surface": round(sz, 1), "dropped": round(gap, 1),
                                "bottom_after": round(o2.z - e2.z, 1), "at": vec(o2)}
            else:
                log("缺口 %.1f cm 不在 %.0f~%.0f 区间，保持原位" % (gap, SNAP_MIN, SNAP_MAX))
                rep["shell"] = {"label": sh.get_actor_label(), "bottom": round(bottom, 1),
                                "surface": round(sz, 1), "dropped": 0.0}

        after = eas.get_all_level_actors()
        rep["total_after"] = len(after)
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        rep["saved"] = bool(unreal.EditorLoadingAndSavingUtils.save_map(w, MAP))
        log("保存 %s : %s（Actor %d）" % (MAP, rep["saved"], len(after)))
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    fp = os.path.join(OUT_DIR, "hide_table_%s.json" % rep["ts"])
    try:
        json.dump(rep, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        log("报告: %s" % fp)
    except Exception:
        pass
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
