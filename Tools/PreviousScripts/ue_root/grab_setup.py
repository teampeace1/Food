# -*- coding: utf-8 -*-
"""Food 工程：抓取交互的第一批基础设施

做四件事：
  1. 检查/修正 IA_Interact 的值类型（必须是 Boolean）
  2. 在 IMC_Default 里把 IA_Interact 绑到 E 和鼠标左键
  3. 给 BP_FirstPersonCharacter 加 PhysicsHandle 组件（已存在则跳过）
  4. 打开 Kitchen_white 关卡，打印所有 actor，供下一步摆出生点/道具
"""
import unreal
import traceback

LOG = r"D:\ue\food_grab_log.txt"
_l = []


def log(s):
    s = str(s)
    _l.append(s)
    try:
        with open(LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(_l) + "\n")
    except Exception:
        pass
    print(s)


def step(name, fn):
    try:
        r = fn()
        log("[OK]   %-30s -> %r" % (name, r))
        return r
    except Exception as e:
        log("[FAIL] %-30s -> %s" % (name, e))
        log(traceback.format_exc())
        return None


EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

IA_PATH = "/Game/Input/Actions/IA_Interact"
IMC_PATH = "/Game/Input/IMC_Default"
CH_PATH = "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter"
LEVEL_PATH = "/Game/0Input/map/Kitchen_white"


# ---------------------------------------------------------------- 1. 输入动作
def fix_ia():
    ia = EAL.load_asset(IA_PATH)
    if ia is None:
        log("IA_Interact 不存在，创建")
        ia = AT.create_asset("IA_Interact", "/Game/Input/Actions",
                             unreal.InputAction, unreal.InputActionFactory())
    cur = ia.get_editor_property("value_type")
    log("IA_Interact value_type = %s" % cur)
    if cur != unreal.InputActionValueType.BOOLEAN:
        ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
        log("  已改为 BOOLEAN")
        EAL.save_loaded_asset(ia)
    return ia


# ------------------------------------------------------------- 2. 输入映射
def add_mapping(imc, action, key_name):
    arr = imc.get_editor_property("mappings")
    # 已经绑过的键直接跳过
    for m in arr:
        a = m.get_editor_property("action")
        k = m.get_editor_property("key")
        kn = k.get_editor_property("key_name")
        if a == action and str(kn) == key_name:
            log("  映射已存在: %s -> %s" % (a.get_name(), kn))
            return False
    new = unreal.EnhancedActionKeyMapping()
    new.set_editor_property("action", action)
    key = unreal.Key()
    key.set_editor_property("key_name", key_name)
    new.set_editor_property("key", key)
    arr.append(new)
    imc.set_editor_property("mappings", arr)
    log("  已添加映射: %s -> %s" % (action.get_name(), key_name))
    return True


def fix_imc():
    imc = EAL.load_asset(IMC_PATH)
    ia = EAL.load_asset(IA_PATH)
    arr = imc.get_editor_property("mappings")
    log("=== IMC_Default 现有 %d 条映射 ===" % len(arr))
    for m in arr:
        a = m.get_editor_property("action")
        k = m.get_editor_property("key")
        an = a.get_name() if a else "<None>"
        kn = str(k.get_editor_property("key_name"))
        log("    %-14s -> %s" % (an, kn))
    changed = add_mapping(imc, ia, "E")
    changed = add_mapping(imc, ia, "LeftMouseButton") or changed
    if changed:
        EAL.save_loaded_asset(imc)
    return changed


# ------------------------------------------------------- 3. 角色加物理手柄
def ensure_physics_handle():
    bp = EAL.load_asset(CH_PATH)
    if bp is None:
        raise RuntimeError("角色蓝图没找到")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    gc = bp.generated_class()
    cdo = unreal.get_default_object(gc)
    try:
        comp = cdo.get_editor_property("PhysicsHandle")
        if comp is not None:
            log("PhysicsHandle 已存在，跳过创建")
            return "exists"
    except Exception:
        pass

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    roots = sds.k2_gather_subobject_data_for_blueprint(bp)
    log("root handles = %d" % len(roots))

    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", roots[0])
    params.set_editor_property("new_class", unreal.PhysicsHandleComponent)
    params.set_editor_property("blueprint_context", bp)
    res = sds.add_new_subobject(params)
    log("add_new_subobject -> %r" % (res,))
    handle = res[0] if isinstance(res, (list, tuple)) else res
    try:
        sds.rename_subobject(handle, "PhysicsHandle")
    except Exception as e:
        log("  rename 跳过: %s" % e)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp)

    cdo = unreal.get_default_object(bp.generated_class())
    try:
        comp = cdo.get_editor_property("PhysicsHandle")
        log("验证: PhysicsHandle = %r" % (comp,))
        return "created"
    except Exception as e:
        return "created-but-unverified(%s)" % e


# ---------------------------------------------------------------- 4. 关卡
def dump_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    ok = les.load_level(LEVEL_PATH)
    log("load_level(%s) -> %s" % (LEVEL_PATH, ok))
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()
    log("=== 关卡 actor 数量: %d ===" % len(actors))
    types = {}
    for a in actors:
        cn = a.get_class().get_name()
        types[cn] = types.get(cn, 0) + 1
    for k, v in sorted(types.items(), key=lambda x: -x[1]):
        log("    %-34s x %d" % (k, v))

    log("=== 主要 actor 位置（前 40 个，按类过滤） ===")
    skip = ("WorldSettings", "Brush", "LevelScriptActor", "DefaultPhysicsVolume")
    n = 0
    for a in actors:
        cn = a.get_class().get_name()
        if any(s in cn for s in skip):
            continue
        if n >= 40:
            break
        loc = a.get_actor_location()
        log("    %-30s %-26s (%.0f, %.0f, %.0f)" % (cn, a.get_actor_label(), loc.x, loc.y, loc.z))
        n += 1

    has_ps = any(a.get_class().get_name() == "PlayerStart" for a in actors)
    log("has PlayerStart: %s" % has_ps)
    return has_ps


log("===== FOOD GRAB SETUP =====")
step("fix_ia", fix_ia)
step("fix_imc", fix_imc)
step("physics_handle", ensure_physics_handle)
step("dump_level", dump_level)
log("===== DONE =====")
