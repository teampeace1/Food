import json, traceback, unreal
MAP = "/Game/0Input/map/Kitchen_white_final_supply"
def log(m): unreal.log("[props] " + str(m))
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    rows = []
    for a in eas.get_all_level_actors():
        if "IngredientSupply" in a.get_class().get_name():
            continue
        try:
            o, e = a.get_actor_bounds(False)
        except Exception:
            continue
        if not (1240 <= o.x <= 1560 and 2400 <= o.y <= 3000):
            continue
        if e.x > 300 or e.y > 300:
            continue
        rows.append((round(o.z - e.z, 1), round(o.z + e.z, 1), round(o.x), round(o.y),
                     a.get_actor_label()[:26], a.get_class().get_name()[:16]))
    rows.sort()
    log("该区域小物件 %d 个（bottom_z, top_z, x, y, label）" % len(rows))
    for r in rows[:45]:
        log("  b=%7.1f t=%7.1f (%5d,%5d) %-26s %s" % r)
    from collections import Counter
    log("bottom_z 分布: " + str(Counter(round(r[0]) for r in rows).most_common(8)))
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    try: unreal.SystemLibrary.quit_editor()
    except Exception: pass
