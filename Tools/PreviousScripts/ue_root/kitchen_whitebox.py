# -*- coding: utf-8 -*-
"""按《烹膨嘭》后厨场景白盒设计图，在 UE 里搭建 10m x 8m x 3.2m 的白模关卡。

坐标系（单位 cm）：
    下面的数据表按【设计图平面坐标】书写：X 向右、Y 向上（后墙）、Z 向上。
    UE 是左手坐标系，从入口朝 +Y 看时玩家右手是 -X，因此构建时对 X 做一次
    镜像（x_world = 1000 - x_plan），这样玩家站在入口看到的左右关系与设计图一致。
    Y: 0 = 入口墙, 800 = 窗户所在的后墙
    Z: 0 = 地面, 320 = 层高
"""
import unreal
import traceback

LOG = r"D:\ue\kitchen_log.txt"
LEVEL_PATH = "/Game/Maps/L_Kitchen_Whitebox"
MAT_DIR = "/Game/Art/Materials"
CUBE = "/Engine/BasicShapes/Cube.Cube"
CYL = "/Engine/BasicShapes/Cylinder.Cube"  # placeholder, fixed below
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"

_lines = []


def log(s):
    _lines.append(str(s))
    try:
        with open(LOG, "w", encoding="utf-8") as f:
            f.write("\n".join(_lines) + "\n")
    except Exception:
        pass
    print(s)


def step(name, fn):
    try:
        r = fn()
        log("[OK]   %-26s -> %s" % (name, r))
        return r
    except Exception as e:
        log("[FAIL] %-26s -> %s" % (name, e))
        log(traceback.format_exc())
        return None


# ----------------------------------------------------------------------------
# 材质
# ----------------------------------------------------------------------------
PALETTE = {
    "floor":   ((0.58, 0.565, 0.535), 0.85),   # 地面 暖灰
    "wall":    ((0.84, 0.825, 0.79), 0.90),    # 墙面 浅米白
    "counter": ((0.70, 0.685, 0.65), 0.60),    # 台面/柜体 中灰
    "equip":   ((0.34, 0.345, 0.36), 0.45),    # 设备 深灰
    "glass":   ((0.86, 0.91, 0.97), 0.15),     # 窗户
    "accent":  ((0.82, 0.44, 0.22), 0.55),     # 门框 暖橙
}


def build_materials():
    AT = unreal.AssetToolsHelpers.get_asset_tools()
    MEL = unreal.MaterialEditingLibrary
    EAL = unreal.EditorAssetLibrary
    EAL.make_directory(MAT_DIR)
    out = {}
    for key, (rgb, rough) in PALETTE.items():
        name = "M_WB_" + key.capitalize()

        def mk(name=name, rgb=rgb, rough=rough):
            path = MAT_DIR + "/" + name
            if EAL.does_asset_exist(path):
                return path
            mat = AT.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
            if mat is None:
                raise RuntimeError("create_asset returned None")
            c = MEL.create_material_expression(
                mat, unreal.MaterialExpressionConstant3Vector, -420, -120)
            c.set_editor_property(
                "constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
            MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
            r = MEL.create_material_expression(
                mat, unreal.MaterialExpressionConstant, -420, 120)
            try:
                r.set_editor_property("r", float(rough))
            except Exception:
                r.set_editor_property("value", float(rough))
            MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
            MEL.recompile_material(mat)
            EAL.save_loaded_asset(mat)
            return path

        out[key] = step("material " + key, mk)
    return out


# ----------------------------------------------------------------------------
# 几何数据： (label, material, x0,x1, y0,y1, z0,z1)
# ----------------------------------------------------------------------------
BOXES = [
    # ---------------- 建筑 ----------------
    ("Floor",          "floor",  -20, 1020,  -20,  820,  -20,   0),
    ("Wall_Front_L",   "wall",   -20,  300,  -20,    0,    0, 320),
    ("Wall_Front_R",   "wall",   500, 1020,  -20,    0,    0, 320),
    ("Door_Lintel",    "wall",   300,  500,  -20,    0,  220, 320),
    ("Wall_Back",      "wall",   -20, 1020,  800,  820,    0, 320),
    ("Wall_Left",      "wall",   -20,    0,  -20,  820,    0, 320),
    ("Wall_Right",     "wall",  1000, 1020,  -20,  820,    0, 320),
    ("Door_Frame_L",   "accent", 282,  302,  -24,    4,    0, 224),
    ("Door_Frame_R",   "accent", 498,  518,  -24,    4,    0, 224),

    # ---------------- 后墙 两扇窗 ----------------
    ("Window_1",       "glass",  145,  295,  790,  808,  170, 290),
    ("Window_2",       "glass",  365,  515,  790,  808,  170, 290),

    # ---------------- 左墙：食材架 / 洗菜池 / 案板区 ----------------
    ("Shelf_Ingredient", "counter", 10,  85,  570,  790,   0, 200),
    ("Sink_Counter",     "counter", 10, 120,  370,  555,   0,  90),
    ("Sink_Basin_1",     "equip",   22,  62,  400,  455,  90,  93),
    ("Sink_Basin_2",     "equip",   68, 108,  400,  455,  90,  93),
    ("Sink_Faucet",      "equip",   55,  65,  545,  558,  90, 132),
    ("Chop_Counter",     "counter", 10, 120,  150,  350,   0,  90),
    ("Chop_Board",       "counter", 20, 110,  175,  325,  90,  96),
    ("Prep_Side",        "counter", 120, 185, 195,  305,   0,  85),

    # ---------------- 后墙：煮锅 / 铁板 / 烤箱 ----------------
    ("Stove_Counter",  "counter", 120, 330,  690,  795,   0,  90),
    ("Stove_Top",      "equip",   135, 315,  700,  785,  90,  96),
    ("Griddle_Counter","counter", 355, 590,  690,  795,   0,  90),
    ("Griddle_Plate",  "equip",   365, 580,  700,  785,  90,  98),
    ("Oven_Body",      "equip",   615, 760,  685,  795,   0, 205),
    ("Oven_Door",      "wall",    625, 750,  679,  686,  20, 150),
    ("Oven_Handle",    "counter", 630, 745,  672,  680, 150, 158),

    # ---------------- 右墙：调味台 / 装盘台 ----------------
    ("Season_Counter", "counter", 890, 995,  500,  700,   0,  90),
    ("Plate_Counter",  "counter", 890, 995,  280,  480,   0,  90),

    # ---------------- 前墙：出餐口 ----------------
    ("Pass_Counter",   "counter", 690, 900,   15,  150,   0, 105),

    # ---------------- 中央：操作岛 ----------------
    ("Island",         "counter", 330, 620,  300,  470,   0,  90),
]

# 圆柱： (label, material, cx, cy, z0, z1, radius)
CYLINDERS = [
    ("Pot",        "equip", 225, 742,  96, 158, 42),
    ("Pass_Dome",  "equip", 795,  82, 105, 132, 34),
    # 调味台上 6 个小料罐
    ("Season_1", "equip", 940, 520, 90, 104, 9),
    ("Season_2", "equip", 940, 552, 90, 104, 9),
    ("Season_3", "equip", 940, 584, 90, 104, 9),
    ("Season_4", "equip", 940, 616, 90, 104, 9),
    ("Season_5", "equip", 940, 648, 90, 104, 9),
    ("Season_6", "equip", 940, 680, 90, 104, 9),
    # 装盘台 3 个盘子
    ("Plate_A", "wall", 942, 320, 90, 95, 19),
    ("Plate_B", "wall", 942, 380, 90, 95, 19),
    ("Plate_C", "wall", 942, 440, 90, 95, 19),
    # 操作岛 4 个盘子
    ("Plate_I1", "wall", 380, 340, 90, 95, 17),
    ("Plate_I2", "wall", 430, 340, 90, 95, 17),
    ("Plate_I3", "wall", 380, 425, 90, 95, 17),
    ("Plate_I4", "wall", 430, 425, 90, 95, 17),
    # 煮锅旁的备料罐
    ("Pot_Jar", "equip", 130, 745, 96, 120, 12),
]

def build():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if eas is None or les is None:
        raise RuntimeError("editor subsystem missing")

    mats = build_materials()

    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        log("removing old level")
        ok = unreal.EditorAssetLibrary.delete_asset(LEVEL_PATH)
        if not ok:
            a = unreal.EditorAssetLibrary.load_asset(LEVEL_PATH)
            if a is not None:
                ok = unreal.EditorAssetLibrary.delete_loaded_asset(a)
        log("delete_asset -> %s" % ok)
    log("new_level -> %s" % les.new_level(LEVEL_PATH))

    cube = unreal.load_asset(CUBE)
    cyl = unreal.load_asset(CYL)
    if cube is None:
        raise RuntimeError("cube mesh not found")

    def mat_of(key):
        p = mats.get(key)
        return unreal.load_asset(p) if p else None

    def wx(x):
        """设计图平面 X -> UE 世界 X（左手系镜像）"""
        return 1000.0 - float(x)

    spawned = 0

    for label, mkey, x0, x1, y0, y1, z0, z1 in BOXES:
        cx, cy, cz = wx((x0 + x1) / 2.0), (y0 + y1) / 2.0, (z0 + z1) / 2.0
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        a = eas.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(cx, cy, cz), unreal.Rotator())
        a.set_actor_label(label)
        a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
        smc = a.static_mesh_component
        smc.set_static_mesh(cube)
        m = mat_of(mkey)
        if m:
            smc.set_material(0, m)
        try:
            a.set_folder_path("Kitchen/" + _folder_for(label))
        except Exception:
            pass
        spawned += 1

    for label, mkey, cx, cy, z0, z1, r in CYLINDERS:
        h = z1 - z0
        a = eas.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(wx(cx), cy, (z0 + z1) / 2.0), unreal.Rotator())
        a.set_actor_label(label)
        if cyl is None:
            log("cylinder mesh missing, skipped " + label)
            continue
        a.set_actor_scale3d(unreal.Vector(2 * r / 100.0, 2 * r / 100.0, h / 100.0))
        smc = a.static_mesh_component
        smc.set_static_mesh(cyl)
        m = mat_of(mkey)
        if m:
            smc.set_material(0, m)
        try:
            a.set_folder_path("Kitchen/" + _folder_for(label))
        except Exception:
            pass
        spawned += 1

    # ---- 灯光 ----
    sun = eas.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(500, 400, 900),
        unreal.Rotator(roll=0.0, pitch=-52.0, yaw=25.0))
    sun.set_actor_label("Sun")
    try:
        c = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if c:
            c.set_intensity(9.0)
    except Exception as e:
        log("sun intensity skip: %s" % e)

    sky = eas.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(500, 400, 300), unreal.Rotator())
    sky.set_actor_label("SkyLight")
    try:
        sc = sky.get_component_by_class(unreal.SkyLightComponent)
        if sc:
            sc.set_editor_property("real_time_capture", True)
            sc.set_intensity(2.2)
    except Exception as e:
        log("skylight skip: %s" % e)

    try:
        atm = eas.spawn_actor_from_class(
            unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator())
        atm.set_actor_label("SkyAtmosphere")
    except Exception as e:
        log("atmosphere skip: %s" % e)

    # ---- 出生点：入口内侧，面朝 +Y（正对后墙设备）----
    try:
        ps = eas.spawn_actor_from_class(
            unreal.PlayerStart, unreal.Vector(wx(400), 90, 100),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0))
        ps.set_actor_label("PlayerStart")
        log("PlayerStart at (%d,90,100) facing +Y" % wx(400))
    except Exception as e:
        log("PlayerStart failed: %s" % e)

    log("save -> %s" % les.save_current_level())
    log("spawned blocks: %d" % spawned)
    log("total actors: %d" % len(eas.get_all_level_actors()))
    log("=== BUILD OK ===")


def _folder_for(label):
    if label.startswith("Wall") or label.startswith("Floor") or label.startswith("Door") \
            or label.startswith("Window") or label == "Pass_Counter":
        return "Structure"
    if label.startswith("Sink") or label.startswith("Chop") or label.startswith("Prep") \
            or label.startswith("Shelf"):
        return "LeftWall"
    if label.startswith("Stove") or label.startswith("Griddle") or label.startswith("Oven") \
            or label in ("Pot", "Pot_Jar"):
        return "BackWall"
    if label.startswith("Season") or label.startswith("Plate_"):
        return "RightWall"
    if label.startswith("Island"):
        return "Center"
    return "Props"


build()
