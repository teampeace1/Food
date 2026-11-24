import traceback, unreal
MAP = "/Game/0Input/map/Kitchen_white_final_supply"
def log(m): unreal.log("[chk] " + str(m))
try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    acts = eas.get_all_level_actors()
    for a in acts:
        cn = a.get_class().get_name()
        if "FillingBowl" not in cn and not a.get_actor_label().endswith("_壳"):
            continue
        if "FillingBowl" in cn and a.get_actor_label().endswith("_壳"):
            pass
        try:
            o, e = a.get_actor_bounds(False)
        except Exception:
            o = e = None
        comps = []
        if "FillingBowl" in cn:
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                comps.append("%s:visible=%s" % (c.get_name(), c.is_visible()))
        log("%-24s %-22s bot=%s comps=%s" % (a.get_actor_label(), cn, (round(o.z - e.z, 1) if o else None), comps))
    log("总 Actor %d" % len(acts))
except Exception:
    log("异常:\n" + traceback.format_exc())
finally:
    try: unreal.SystemLibrary.quit_editor()
    except Exception: pass
