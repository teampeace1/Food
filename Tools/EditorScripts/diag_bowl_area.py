# -*- coding: utf-8 -*-
"""只读：列出 (1110,3550) 周边物件的包围盒，判断馅料碗脚下真实支撑面。"""
import json
import os
import traceback

import unreal

MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps", "diag_bowl_area.json")
CX, CY = 1110.0, 3550.0
R = 260.0


def log(m):
    unreal.log("[area] " + str(m))


def v(x):
    return [round(float(x.x), 1), round(float(x.y), 1), round(float(x.z), 1)]


try:
    if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
        log("地图加载失败")
    else:
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        rows = []
        for a in eas.get_all_level_actors():
            try:
                o, e = a.get_actor_bounds(False)
            except Exception:
                continue
            if abs(o.x - CX) > R + e.x or abs(o.y - CY) > R + e.y:
                continue
            rows.append({
                "label": a.get_actor_label(), "cls": a.get_class().get_name(),
                "center": v(o), "ext": v(e),
                "bottom": round(o.z - e.z, 1), "top": round(o.z + e.z, 1),
                "size": [round(e.x * 2, 1), round(e.y * 2, 1), round(e.z * 2, 1)],
            })
        rows.sort(key=lambda r: -r["top"])
        log("周边 %d 个物件（按顶面从高到低）" % len(rows))
        for r in rows[:40]:
            log("  top=%7.1f bot=%7.1f 横%5.1f纵%5.1f高%6.1f  (%5.0f,%5.0f) %-26s %s" % (
                r["top"], r["bottom"], r["size"][0], r["size"][1], r["size"][2],
                r["center"][0], r["center"][1], r["label"][:26], r["cls"][:18]))
        json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        log("报告: " + OUT)
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
