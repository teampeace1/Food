import os, json, time, traceback, unreal

OLD = "/Game/0Input/map/_chk_old"
NEW = "/Game/0Input/map/Kitchen_white_final"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelDumps")

def log(m): unreal.log("[diff] " + str(m))

def snap():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    d = {}
    for a in eas.get_all_level_actors():
        p = a.get_actor_location()
        k = "%s|%s|%.0f_%.0f_%.0f" % (a.get_actor_label(), a.get_class().get_name(), p.x, p.y, p.z)
        d[k] = d.get(k, 0) + 1
    return d

try:
    unreal.EditorLoadingAndSavingUtils.load_map(OLD)
    a = snap()
    unreal.EditorLoadingAndSavingUtils.load_map(NEW)
    b = snap()
    miss = sorted(set(a) - set(b)); add = sorted(set(b) - set(a))
    log("old(00:26备份)=%d  final=%d" % (len(a), len(b)))
    log("final 少: %s" % miss)
    log("final 多: %s" % add)
    fp = os.path.join(OUT, "diff_%s.json" % time.strftime("%Y%m%d_%H%M%S"))
    json.dump({"old": a, "new": b, "missing": miss, "added": add}, open(fp, "w", encoding="utf-8"), ensure_ascii=False, default=str)
    log("报告: %s" % fp)
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    try:
        unreal.SystemLibrary.quit_editor()
    except Exception:
        pass
