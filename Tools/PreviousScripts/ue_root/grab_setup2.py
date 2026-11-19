# -*- coding: utf-8 -*-
"""Food 工程抓取交互 —— 第二批：真正的修改

  1. 用 5.8 的新结构 default_key_mappings 绑定 IA_Interact -> E / 鼠标左键
  2. 清掉误写到废弃字段 mappings 的内容
  3. 校验角色蓝图里的 PhysicsHandle
  4. 关卡里补 PlayerStart + 3 个可抓取测试方块
"""
import math
import traceback

import unreal

LOG = r"D:\ue\grab2_log.txt"
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
        log("[OK]   %-26s -> %r" % (name, r))
        return r
    except Exception as e:
        log("[FAIL] %-26s -> %s" % (name, e))
        log(traceback.format_exc())
        return None


EAL = unreal.EditorAssetLibrary
IA_PATH = "/Game/Input/Actions/IA_Interact"
IMC_PATH = "/Game/Input/IMC_Default"
CH_PATH = "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter"
LEVEL_PATH = "/Game/0Input/map/Kitchen_white"
CUBE = "/Engine/BasicShapes/Cube.Cube"

log("===== GRAB SETUP 2 =====")


# ------------------------------------------------------------------ 1. IMC
def bind_keys():
    imc = EAL.load_asset(IMC_PATH)
    ia = EAL.load_asset(IA_PATH)

    data = imc.get_editor_property("default_key_mappings")
    arr = data.mappings
    log("现有真实映射 %d 条" % len(arr))

    existing = []
    for m in arr:
        a = m.get_editor_property("action")
        k = m.get_editor_property("key")
        if a is not None:
            existing.append((a.get_name(), str(k.get_editor_property("key_name"))))
    for e in existing:
        log("    %-14s -> %s" % e)

    wanted = ["E", "LeftMouseButton"]
    have = set(k for (a, k) in existing if a == "IA_Interact")

    for key_name in wanted:
        if key_name in have:
            log("  已存在: IA_Interact -> %s" % key_name)
            continue
        m = unreal.EnhancedActionKeyMapping()
        m.set_editor_property("action", ia)
        k = unreal.Key()
        k.set_editor_property("key_name", key_name)
        m.set_editor_property("key", k)
        arr.append(m)
        log("  添加: IA_Interact -> %s" % key_name)

    data.set_editor_property("mappings", arr)
    imc.set_editor_property("default_key_mappings", data)

    # 清掉上一轮误写进废弃字段的内容
    try:
        legacy = imc.get_editor_property("mappings")
        if len(legacy) > 0:
            imc.set_editor_property("mappings", [])
            log("  已清空废弃字段 mappings（原有 %d 条脏数据）" % len(legacy))
    except Exception as e:
        log("  清理废弃字段失败: %s" % e)

    EAL.save_loaded_asset(imc)

    # 落盘后重新加载校验
    imc2 = EAL.load_asset(IMC_PATH)
    d2 = imc2.get_editor_property("default_key_mappings")
    n_ia = 0
    for m in d2.mappings:
        a = m.get_editor_property("action")
        if a is not None and a.get_name() == "IA_Interact":
            n_ia += 1
            log("  校验: IA_Interact -> %s" %
                m.get_editor_property("key").get_editor_property("key_name"))
    return "总映射 %d 条, IA_Interact %d 条" % (len(d2.mappings), n_ia)


# -------------------------------------------------------- 2. 角色组件校验
def check_character():
    bp = EAL.load_asset(CH_PATH)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    props = [p for p in dir(cdo) if "hysics" in p.lower()]
    log("CDO 上与 physics 相关的属性: %s" % props)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    roots = sds.k2_gather_subobject_data_for_blueprint(bp)
    log("根组件句柄数 = %d" % len(roots))
    return props


# --------------------------------------------------------------- 3. 关卡
def build_level():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(LEVEL_PATH)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = eas.get_all_level_actors()

    meshes = [a for a in actors if a.get_class().get_name() == "StaticMeshActor"]
    rects = []
    for a in meshes:
        try:
            org, ext = a.get_actor_bounds(False)
        except Exception:
            continue
        if ext.x * ext.y < 100:      # 忽略细杆
            continue
        rects.append((org.x - ext.x, org.x + ext.x, org.y - ext.y, org.y + ext.y, a.get_actor_label()))
    log("参与占位计算的 actor: %d" % len(rects))

    xs = [r[0] for r in rects] + [r[1] for r in rects]
    ys = [r[2] for r in rects] + [r[3] for r in rects]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    log("场景 XY 包围盒: x %.0f~%.0f  y %.0f~%.0f" % (minx, maxx, miny, maxy))

    def blocked(x, y, pad):
        for (x0, x1, y0, y1, _lab) in rects:
            if x0 - pad <= x <= x1 + pad and y0 - pad <= y <= y1 + pad:
                return True
        return False

    def clearance(x, y):
        best = 1e9
        for (x0, x1, y0, y1, _lab) in rects:
            dx = max(x0 - x, 0, x - x1)
            dy = max(y0 - y, 0, y - y1)
            d = math.hypot(dx, dy)
            best = min(best, d)
        return best

    # 在房间里按 50cm 网格找最空旷的点
    best_pt, best_c = None, -1
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    x = minx
    while x <= maxx:
        y = miny
        while y <= maxy:
            c = clearance(x, y)
            if c > best_c:
                best_c, best_pt = c, (x, y)
            y += 50
        x += 50
    log("最空旷点 (%.0f, %.0f) 净空 %.0f cm" % (best_pt[0], best_pt[1], best_c))

    # 朝向场景中心
    sx, sy = best_pt
    yaw = math.degrees(math.atan2(cy - sy, cx - sx))

    # 已有 PlayerStart 就复用，没有就新建
    ps = None
    for a in actors:
        if a.get_class().get_name() == "PlayerStart":
            ps = a
            log("已有 PlayerStart: %s" % a.get_actor_label())
            break
    loc = unreal.Vector(sx, sy, 110.0)
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw)
    if ps is None:
        ps = eas.spawn_actor_from_class(unreal.PlayerStart, loc, rot)
        ps.set_actor_label("PlayerStart")
        log("已新建 PlayerStart @ (%.0f, %.0f, 110) yaw %.0f" % (sx, sy, yaw))
    else:
        ps.set_actor_location(loc, False, False)
        ps.set_actor_rotation(rot, False)

    # 出生点前方 3 个测试方块
    cube = unreal.load_asset(CUBE)
    fwd = unreal.Vector(math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0)
    right = unreal.Vector(-fwd.y, fwd.x, 0.0)
    made = []
    for i, (d, side) in enumerate([(160, 0), (220, -70), (220, 70)]):
        px = sx + fwd.x * d + right.x * side
        py = sy + fwd.y * d + right.y * side
        if blocked(px, py, 20):
            px, py = sx + fwd.x * (d + 120), sy + fwd.y * (d + 120)
            if blocked(px, py, 20):
                log("  跳过 TestProp_%02d（位置被占）" % (i + 1))
                continue
        a = eas.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(px, py, 45.0), unreal.Rotator())
        a.set_actor_label("TestProp_%02d" % (i + 1))
        a.set_actor_scale3d(unreal.Vector(0.22, 0.22, 0.22))
        comp = a.static_mesh_component
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_static_mesh(cube)
        a.set_actor_location(unreal.Vector(px, py, 45.0), False, False)
        comp.set_simulate_physics(True)
        try:
            comp.set_mass_override_in_kg(1.5)
        except Exception as e:
            log("  mass override 失败: %s" % e)
        made.append((a.get_actor_label(), round(px), round(py)))
        log("  TestProp_%02d @ (%.0f, %.0f)" % (i + 1, px, py))

    ok = les.save_current_level()
    log("save_current_level -> %s" % ok)
    return "props=%d save=%s" % (len(made), ok)


step("bind_keys", bind_keys)
step("check_character", check_character)
step("build_level", build_level)
log("===== DONE =====")
