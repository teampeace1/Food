import unreal

# 烹膨嘭 后厨白模生成器
# 在 UE 编辑器启用 Python Editor Script Plugin 后，于 Output Log 执行：
# py "绝对路径/烹膨嘭_后厨白模.py"
# 尺寸单位 cm；场景以西南角为 (0,0,0)，房间范围 X=0..1000, Y=0..800。

E = unreal.EditorLevelLibrary
SPAWN = unreal.EditorLevelLibrary.spawn_actor_from_class
CUBE = unreal.Cube

# 生成物统一命名 WM_，便于在 World Outliner 搜索并整体选择。
def box(name, x, y, z, sx, sy, sz, color=None):
    actor = SPAWN(CUBE, unreal.Vector(x, y, z), unreal.Rotator())
    actor.set_actor_label("WM_" + name)
    actor.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
    if color:
        # 简易纯色材质通过引擎基础材质尝试赋值；失败不影响白模生成。
        try:
            mat = unreal.MaterialEditingLibrary.create_material_instance_constant(
                unreal.Material.get_default_object(), "")
        except Exception:
            pass
    return actor

# 地面、墙体：墙高 320；南侧留 180 cm 入口。
box("Floor_1000x800", 500, 400, -10, 1000, 800, 20)
box("Wall_North", 500, 800, 160, 1000, 20, 320)
box("Wall_West", 0, 400, 160, 20, 800, 320)
box("Wall_East", 1000, 400, 160, 20, 800, 320)
box("Wall_South_Left", 200, 0, 160, 400, 20, 320)
box("Wall_South_Right", 800, 0, 160, 400, 20, 320)

# 台面统一高度 90 cm，模块尺寸按俯视图比例近似；位置尽量留出 >=150 cm 主通道。
def counter(name, x, y, sx, sy, h=90):
    box(name + "_Body", x, y, h/2, sx, sy, h)
    box(name + "_Top", x, y, h+2, sx+4, sy+4, 4)

def station(name, x, y, sx=120, sy=70):
    counter(name, x, y, sx, sy)
    # 可交互占位区（窄高柱），在 Outliner 中可独立定位替换
    box(name + "_Interact", x, y, 115, 35, 35, 50)

# 西侧：食材架、洗菜池、案板区
counter("Ingredient_Shelf", 100, 680, 170, 70, 180)
for yy in (620, 470, 320):
    station("Sink", 55, yy, 90, 100)
counter("Cutting_Board", 185, 155, 170, 100)
box("Cutting_Board_Surface", 185, 155, 93, 130, 65, 3)

# 北侧烹饪线：水槽/煮锅、灶台、烤箱、调味区
station("Boiling_Pot", 430, 660, 130, 90)
box("Pot_Prop", 430, 660, 130, 65, 65, 55)
station("Griddle", 575, 660, 130, 90)
box("Griddle_Surface", 575, 660, 96, 105, 60, 5)
station("Oven", 725, 660, 110, 100)
box("Oven_Door", 725, 608, 105, 85, 8, 55)
station("Seasoning", 880, 660, 100, 90)

# 东侧碗碟/装盘台
counter("Plating_Counter", 940, 400, 90, 500)
for yy in (220, 350, 480, 610):
    box("Plate_Prop", 940, yy, 96, 55, 55, 5)

# 中央临时操作岛
counter("Center_Island", 515, 385, 260, 110)
for xx, yy in ((430,400),(480,400),(530,400),(580,400),(455,360),(520,360)):
    box("Bowl_Prop", xx, yy, 98, 35, 35, 12)

# 南东出餐口；南侧中央出生点，面向北。
counter("Serving_Window", 830, 120, 190, 90, 105)
box("Serving_Interact", 830, 165, 145, 40, 35, 55)
box("Player_Start_Marker", 500, 90, 4, 50, 50, 8)

# 窗户占位（北墙内侧的浅色块），两扇窗。
for wx in (350, 700):
    box("Window_Opening_Visual", wx, 786, 205, 140, 4, 85)

unreal.log("烹膨嘭白模已生成。搜索 WM_ 可选中全部生成物；场景尺寸 10m x 8m，台面高 0.9m。")
