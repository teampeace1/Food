"""把上一次的产物改成正名，并做一次"读回验证"：重新打开文件、数一遍 Actor 与道具。

    py ".../finalize_props_map.py"
"""

import unreal

OLD = "/Game/0Input/map/Kitchen_white_new_plus_props_v71"
NEW = "/Game/0Input/map/Kitchen_white_new_props"
JUNK = ["/Game/0Input/map/Kitchen_white_new_plus_props_v2"]


def log(m):
    unreal.log("[fin] " + str(m))


def ckey(a):
    n = a.get_class().get_name()
    return n[:-2] if n.endswith("_C") else n


def main():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    if not les.load_level(OLD):
        unreal.log_error("[fin] 打不开 %s" % OLD)
        return

    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = eas.get_all_level_actors()
    by_class = {}
    for a in actors:
        by_class[ckey(a)] = by_class.get(ckey(a), 0) + 1
    log("读回 %s: %d 个 Actor" % (OLD.split('/')[-1], len(actors)))
    for k in sorted(by_class, key=lambda x: -by_class[x])[:8]:
        log("   %-28s %d" % (k, by_class[k]))

    if unreal.EditorAssetLibrary.does_asset_exist(NEW):
        unreal.EditorAssetLibrary.delete_asset(NEW)
        log("已删除同名旧文件: %s" % NEW)

    unreal.EditorLoadingAndSavingUtils.save_map(w, NEW)
    log("已另存为正名: %s" % NEW)

    if unreal.EditorAssetLibrary.does_asset_exist(OLD):
        unreal.EditorAssetLibrary.delete_asset(OLD)
        log("已删除临时名: %s" % OLD)
    for j in JUNK:
        if unreal.EditorAssetLibrary.does_asset_exist(j):
            unreal.EditorAssetLibrary.delete_asset(j)
            log("已删除垃圾文件: %s" % j)

    log("完成")


main()
