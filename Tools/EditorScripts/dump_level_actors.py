"""导出当前关卡全部 Actor 的身份与变换，用于合并前后比对。

用法（编辑器内）：
    Tools -> Execute Python Script...  选中本文件
或在 Output Log 的 Python 命令行执行：
    py "C:/Users/38606/Documents/GitHub/Food/Tools/EditorScripts/dump_level_actors.py"

输出：<Project>/Saved/LevelDumps/<Level>__<时间戳>.json
"""

import os
import json
import time
import unreal


def get_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def full_path(obj):
    try:
        return unreal.SystemLibrary.get_path_name(obj)
    except Exception:
        return str(obj)


def vec(v):
    return [round(v.x, 3), round(v.y, 3), round(v.z, 3)]


def dump_actor(a):
    try:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        scl = a.get_actor_scale3d()
    except Exception:
        loc = rot = scl = None

    cls = a.get_class()
    data = {
        "name": a.get_name(),
        "label": a.get_actor_label(),
        "class": cls.get_name() if cls else "?",
        "class_path": full_path(cls),
        "path": full_path(a),
        "level": a.get_outer().get_name() if a.get_outer() else "?",
        "folder": str(a.get_folder_path()),
        "location": vec(loc) if loc else None,
        "rotation": [round(rot.pitch, 3), round(rot.yaw, 3), round(rot.roll, 3)] if rot else None,
        "scale": vec(scl) if scl else None,
    }
    try:
        data["tags"] = [str(t) for t in a.get_editor_property("tags")]
    except Exception:
        data["tags"] = []
    return data


def main():
    world = get_world()
    if world is None:
        unreal.log_error("[dump] 没有打开的世界")
        return

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    rows = [dump_actor(a) for a in actors]

    # 统计：按类
    by_class = {}
    for r in rows:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1

    # 当前关卡的持久关卡名
    level_name = world.get_name()
    payload = {
        "level": level_name,
        "level_path": full_path(world.get_current_level().get_outer()) if world.get_current_level() else "",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(rows),
        "by_class": dict(sorted(by_class.items(), key=lambda kv: -kv[1])),
        "actors": rows,
    }

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "%s__%s.json" % (level_name, time.strftime("%m%d_%H%M%S")))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    unreal.log("[dump] %s: %d 个 Actor" % (level_name, len(rows)))
    for cls, cnt in payload["by_class"].items():
        unreal.log("[dump]   %-42s %d" % (cls, cnt))
    unreal.log("[dump] 已写出 %s" % out)


main()
