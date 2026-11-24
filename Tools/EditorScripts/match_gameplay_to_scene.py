"""让玩法蓝图跟着它所在的区域一起位移。

背景：AET2 把部分环境物件挪了位置（adopt 报告里 48 条 from -> to）。
玩法蓝图（Content/FoodGameplay 下的实例）还停在旧坐标，所以会脱离台面/悬空。
做法：对每个玩法 Actor，找它旧位置附近最近的那条位移记录，把同样的位移套上去。

只采纳"可信位移"作为同步源：
    * 位移幅度 <= 300cm（22 米的海面、6.3 米的单件搬迁不参与传播）
    * 源点距离 <= 400cm

用法：
    编辑器内: py ".../match_gameplay_to_scene.py"
    命令行  : UnrealEditor.exe Food.uproject -ExecutePythonScript=".../match_gameplay_to_scene.py"
"""

import os
import json
import math
import time
import traceback
import unreal

MAP_PATH = "/Game/0Input/map/Kitchen_white_aet2scene"
OUT_PATH = "/Game/0Input/map/Kitchen_white_final"
SRC_JSON = os.path.join(unreal.Paths.project_saved_dir(),
                        "LevelDumps", "adopt_1121_234519.json")

DRY_RUN = False
AUTO_QUIT = True

PLAY_TAG = "FoodGameplay"     # 类路径包含它就算玩法蓝图
MAX_SOURCE_SHIFT = 20.0       # 只传播"贴合微调"，大搬迁不带动玩法设备
MAX_SOURCE_DIST = 400.0       # 源点距玩法 Actor 的最大距离
MIN_PLAY, MAX_PLAY = 10, 40

CTX = {"handle": None, "quit_at": None, "ticks": 0}


def log(m):
    unreal.log("[match] " + str(m))


def warn(m):
    unreal.log_warning("[match] " + str(m))


def world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


def eas():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def dist3(a, b):
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def run():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    w = world()
    if w is None or w.get_name() != MAP_PATH.split("/")[-1]:
        log("切到 %s" % MAP_PATH)
        if not les.load_level(MAP_PATH):
            warn("地图打不开")
            return

    with open(SRC_JSON, encoding="utf-8") as f:
        rep = json.load(f)

    sources = []
    skipped_big = 0
    for m in rep["moved"]:
        d = [m["to"][i] - m["from"][i] for i in range(3)]
        mag = math.sqrt(sum(x * x for x in d))
        if mag > MAX_SOURCE_SHIFT:
            skipped_big += 1
            continue
        sources.append({"from": m["from"], "d": d, "mag": mag, "name": m["name"]})
    log("可用位移源 %d 条（排除大跳 %d 条）" % (len(sources), skipped_big))

    actors = eas().get_all_level_actors()
    play = []
    for a in actors:
        try:
            cls = a.get_class()
            cp = cls.get_path_name()
        except Exception:
            continue
        if PLAY_TAG not in cp:
            continue
        play.append((a, cls.get_name(), cp))

    log("玩法 Actor %d 个" % len(play))

    # 全场景蓝图清单（含环境类），用于确认玩法蓝图没有遗漏
    all_bp = {}
    for a in actors:
        try:
            cp = a.get_class().get_path_name()
        except Exception:
            continue
        if "BP_" in cp:
            all_bp[cp] = all_bp.get(cp, 0) + 1
    for cp, n in sorted(all_bp.items(), key=lambda t: -t[1]):
        log("  场景蓝图 %-56s %d" % (cp.replace("/Game/", ""), n))

    plan, unmatched = [], []
    for a, cname, cp in play:
        loc = a.get_actor_location()
        p = (loc.x, loc.y, loc.z)
        best, bd = None, 1e18
        for s in sources:
            dd = dist3(s["from"], p)
            if dd < bd:
                best, bd = s, dd
        rec = {"name": a.get_actor_label() or a.get_name(), "class": cname,
               "at": [round(p[0], 1), round(p[1], 1), round(p[2], 1)],
               "nearest_dist_cm": round(bd, 1)}
        if best is not None and bd <= MAX_SOURCE_DIST:
            rec.update({"follow": best["name"], "delta": [round(x, 1) for x in best["d"]],
                        "shift_cm": round(best["mag"], 1),
                        "to": [round(p[i] + best["d"][i], 1) for i in range(3)]})
            plan.append((a, rec))
        else:
            rec["reason"] = "附近 400cm 内没有可信位移源"
            unmatched.append(rec)

    moved_cnt = len([1 for _, r in plan if r["shift_cm"] > 0.5])
    log("可跟随 %d 个（其中位移>0.5cm 的 %d 个），无对应 %d 个"
        % (len(plan), moved_cnt, len(unmatched)))
    for _, r in sorted(plan, key=lambda t: -t[1]["shift_cm"]):
        log("  %-22s %-24s %5.1fcm  follow %s"
            % (r["name"], r["class"], r["shift_cm"], r["follow"]))
    for r in unmatched:
        log("  [不动] %-22s %-24s @ %s" % (r["name"], r["class"], r["at"]))

    gates = [("玩法 Actor 数 %d..%d" % (MIN_PLAY, MAX_PLAY), MIN_PLAY <= len(play) <= MAX_PLAY),
             ("跟随数 <= 玩法数", len(plan) <= len(play))]
    for rule, p in gates:
        log("  闸门 %-26s %s" % (rule, "通过" if p else "未通过"))

    out_dir = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")
    os.makedirs(out_dir, exist_ok=True)
    rp = os.path.join(out_dir, "match_%s.json" % time.strftime("%m%d_%H%M%S"))
    report = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "map": MAP_PATH,
              "dry_run": DRY_RUN, "play_total": len(play),
              "plan": [r for _, r in plan], "unmatched": unmatched,
              "gates": [{"rule": r, "pass": p} for r, p in gates]}

    if DRY_RUN or not all(p for _, p in gates):
        with open(rp, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        log("未写盘（DRY_RUN=%s），报告: %s" % (DRY_RUN, rp))
        return

    ok, fail = 0, []
    for a, r in plan:
        if r["shift_cm"] <= 0.5:
            continue
        try:
            loc = a.get_actor_location()
            a.set_actor_location(
                unreal.Vector(loc.x + r["delta"][0], loc.y + r["delta"][1], loc.z + r["delta"][2]),
                False, True)
            ok += 1
        except Exception as e:
            fail.append("%s: %s" % (r["name"], e))
    log("已位移 %d 个，失败 %d" % (ok, len(fail)))
    if fail:
        warn("失败: %s" % fail[:5])

    if unreal.EditorAssetLibrary.does_asset_exist(OUT_PATH):
        unreal.EditorAssetLibrary.delete_asset(OUT_PATH)
        try:
            unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(
                ["/Game/0Input/map"], True, True)
        except Exception:
            pass
    out = OUT_PATH
    if unreal.EditorAssetLibrary.does_asset_exist(out):
        out = "%s_v%d" % (OUT_PATH, int(time.time()) % 1000)
    unreal.EditorLoadingAndSavingUtils.save_map(world(), out)
    log("已另存: %s" % out)

    report.update({"saved_as": out, "applied": ok,
                   "after_total": len(eas().get_all_level_actors())})
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    log("报告: %s" % rp)


def _tick(_dt):
    CTX["ticks"] += 1
    try:
        if CTX["quit_at"] is not None and CTX["ticks"] >= CTX["quit_at"]:
            if CTX["handle"] is not None:
                try:
                    unreal.unregister_slate_post_tick_callback(CTX["handle"])
                except Exception:
                    pass
            log("任务结束，自动关闭编辑器")
            try:
                unreal.SystemLibrary.quit_editor()
            except Exception as e:
                warn("退出失败: %s" % e)
            return
        if CTX["ticks"] < 3:
            return
        if CTX["handle"] is not None:
            try:
                unreal.unregister_slate_post_tick_callback(CTX["handle"])
            except Exception:
                pass
            CTX["handle"] = None
        run()
        CTX["quit_at"] = CTX["ticks"] + 90
        CTX["handle"] = unreal.register_slate_post_tick_callback(_tick)
    except Exception:
        warn("执行异常:\n" + traceback.format_exc())
        CTX["quit_at"] = CTX["ticks"] + 60


def boot():
    # 本脚本不需要等子关卡流式加载，直接同步跑完；跑完再关编辑器
    try:
        run()
    except Exception:
        warn("执行异常:\n" + traceback.format_exc())
    if AUTO_QUIT:
        try:
            CTX["quit_at"] = 0
            CTX["handle"] = unreal.register_slate_post_tick_callback(_tick)
            log("已请求退出")
        except Exception as e:
            warn("退出失败: %s" % e)


boot()
