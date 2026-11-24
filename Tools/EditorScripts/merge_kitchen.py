"""把「料理交互 Actor」按类整体搬到队友场景上，生成一张新地图。

原则：
  * 以 Actor 身份（类）为准，不按数量凑；同一类的每个实例都搬，一个不落
  * 变换不重算：走 unreal 的 move_actors_to_level，世界坐标原样保留
  * 只新建地图，不覆盖任何现有 umap

用法（编辑器内，先关掉 PIE）：
    py "C:/Users/38606/Documents/GitHub/Food/Tools/EditorScripts/merge_kitchen.py"

改路径就改下面三个常量。
"""

import os
import json
import time
import unreal

BASE = "/Game/0Input/map/Kitchen_white_team_7e"   # 底图：队友最新场景
SRC = "/Game/0Input/map/Kitchen_white_new"        # 取料图：你的玩法布局
OUT = "/Game/0Input/map/Kitchen_white_merged"     # 产物：新地图

# 需要搬过去的玩法类（类名，不带 _C 后缀）。要加就加在这里。
ALLOW_CLASSES = {
    "BP_ChoppingBoard",
    "BP_Sink",
    "BP_IngredientSupply",
    "BP_RollingStation",
    "BP_FillingBowl",
    "BP_Oven",
    "BP_Pie",
    "BP_Workstation",
}

# 这些类即使出现在 SRC 里也不搬（场景装饰/角色，由底图或 GameMode 负责）
DENY_CLASSES = {
    "BP_ThirdPersonCharacter",
    "BP_Fantasy_Water",
    "BP_IndividualCloud",
    "BP_Lightweight_Ocean",
    "BP_StylizedWater",
}

CARRY_PLAYER_START = True   # 底图没有 PlayerStart 时，从 SRC 带一个过去


def log(msg):
    unreal.log("[merge] " + str(msg))


def warn(msg):
    unreal.log_warning("[merge] " + str(msg))


def editor_world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def class_key(actor):
    name = actor.get_class().get_name()
    return name[:-2] if name.endswith("_C") else name


def loc_of(actor):
    v = actor.get_actor_location()
    return {"x": round(v.x, 2), "y": round(v.y, 2), "z": round(v.z, 2)}


def hist(actors):
    h = {}
    for a in actors:
        h[class_key(a)] = h.get(class_key(a), 0) + 1
    return dict(sorted(h.items(), key=lambda kv: -kv[1]))


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # ---- 0. 打开底图 ----
    if not les.load_level(BASE):
        warn("底图打不开: %s" % BASE)
        return
    world = editor_world()
    base_actors = eas.get_all_level_actors()
    base_classes = hist(base_actors)
    log("底图 %s: %d 个 Actor" % (BASE, len(base_actors)))
    if sum(base_classes.get(c, 0) for c in ALLOW_CLASSES):
        warn("底图已含玩法类：%s —— 继续可能重复，请先确认"
             % {c: base_classes[c] for c in ALLOW_CLASSES if base_classes.get(c)})

    # ---- 1. 把 SRC 加成子关卡 ----
    sub = None
    for cls in ("LevelStreamingDynamic", "LevelStreamingKismet", "LevelStreaming"):
        try:
            if sub is None:
                sub = unreal.EditorLevelUtils.add_level_to_world(world, SRC, getattr(unreal, cls))
                log("子关卡已挂载: %s (streaming=%s)" % (SRC, cls))
        except Exception as e:
            warn("add_level_to_world(%s) 失败: %s" % (cls, e))
    if sub is None:
        warn("挂载子关卡失败，终止。")
        return

    sub_actors = [a for a in eas.get_all_level_actors() if a.get_outer() == sub]
    log("子关卡 %s: %d 个 Actor" % (SRC, len(sub_actors)))

    # ---- 2. 按类挑演员 ----
    picked = [a for a in sub_actors if class_key(a) in ALLOW_CLASSES]
    log("命中玩法类 %d 个: %s" % (len(picked), hist(picked)))

    if CARRY_PLAYER_START:
        base_has_ps = any(class_key(a) == "PlayerStart" for a in base_actors)
        src_ps = [a for a in sub_actors if class_key(a) == "PlayerStart"]
        if not base_has_ps and src_ps:
            picked.append(src_ps[0])
            log("底图无 PlayerStart，将从 SRC 带 1 个: %s @ %s"
                % (src_ps[0].get_name(), loc_of(src_ps[0])))
        elif not base_has_ps:
            warn("底图和 SRC 都没有 PlayerStart —— 合并后要在底图里补一个，否则 PIE 出生在原点")

    before = [{"name": a.get_name(), "class": class_key(a), "loc": loc_of(a)} for a in picked]

    # ---- 3. 搬到持久关卡 ----
    dest = world.get_current_level()
    try:
        unreal.EditorLevelUtils.move_actors_to_level(picked, dest)
        log("已搬运 %d 个 Actor 到持久关卡" % len(picked))
    except Exception as e:
        warn("move_actors_to_level 失败: %s" % e)
        return

    # ---- 4. 卸掉子关卡 ----
    try:
        unreal.EditorLevelUtils.remove_level_from_world(sub)
        log("子关卡已卸载")
    except Exception as e:
        warn("卸载子关卡失败（不影响已搬内容）: %s" % e)

    # ---- 5. 另存为新地图 ----
    out_path = OUT
    n = 2
    while unreal.EditorAssetLibrary.does_asset_exist(out_path):
        out_path = "%s_v%d" % (OUT, n)
        n += 1
    unreal.EditorLoadingAndSavingUtils.save_map(world, out_path)
    log("已另存: %s" % out_path)

    # ---- 6. 校验：每个搬运对象是否还在原位 ----
    after_actors = eas.get_all_level_actors()
    after_index = {a.get_name(): a for a in after_actors}
    drift = []
    for rec in before:
        a = after_index.get(rec["name"])
        if a is None:
            drift.append({"name": rec["name"], "issue": "丢失"})
            continue
        now = loc_of(a)
        d = max(abs(now[k] - rec["loc"][k]) for k in ("x", "y", "z"))
        if d > 0.01:
            drift.append({"name": rec["name"], "issue": "位移 %.3f" % d, "from": rec["loc"], "to": now})

    report = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base": BASE, "src": SRC, "out": out_path,
        "base_total": len(base_actors),
        "src_total": len(sub_actors),
        "moved": len(picked),
        "moved_by_class": hist(picked),
        "after_total": len(after_actors),
        "after_by_class": hist(after_actors),
        "allowed_after": {c: hist(after_actors).get(c, 0) for c in sorted(ALLOW_CLASSES)},
        "transform_drift": drift,
        "moved_list": before,
    }
    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
    os.makedirs(out_dir, exist_ok=True)
    rep = os.path.join(out_dir, "merge_report_%s.json" % time.strftime("%m%d_%H%M%S"))
    with open(rep, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    log("---- 结果 ----")
    log("底图 %d + 搬入 %d = %d" % (len(base_actors), len(picked), len(after_actors)))
    log("玩法类落位: %s" % report["allowed_after"])
    log("坐标漂移: %d 个" % len(drift))
    log("报告: %s" % rep)


main()
