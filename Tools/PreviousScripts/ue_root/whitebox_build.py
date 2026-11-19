import unreal
import traceback

LOG_PATH = r"D:\ue\whitebox_log.txt"
LEVEL_PATH = "/Game/Maps/L_Whitebox"
CUBE = "/Engine/BasicShapes/Cube.Cube"
MAT = "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"

_state = {"ticks": 0, "done": False, "handle": None}


def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass
    print(msg)


def reset_log():
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write("=== WHITEBOX BUILD START ===\n")


# (label, cx, cy, cz, size_x, size_y, size_z)  unit: cm, z=0 is floor top surface
BOXES = [
    ("Floor",            750,    0,  -10, 1600, 2000,  20),
    # corridor north wall (y=150), gap 300..400 for doorway
    ("Wall_CorrN_A",     150,  150,  150,  300,   20, 300),
    ("Wall_CorrN_B",     900,  150,  150, 1000,   20, 300),
    ("DoorTop_N",        350,  150,  255,  100,   20,  90),
    # corridor south wall (y=-150), gap 1000..1100 for doorway
    ("Wall_CorrS_A",     500, -150,  150, 1000,   20, 300),
    ("Wall_CorrS_B",    1250, -150,  150,  300,   20, 300),
    ("DoorTop_S",       1050, -150,  255,  100,   20,  90),
    # corridor east end
    ("Wall_CorrEnd",    1400,    0,  150,   20,  320, 300),
    # room A  (x 0..900, y 150..950)
    ("Wall_A_West",        0,  550,  150,   20,  800, 300),
    ("Wall_A_North",     450,  950,  150,  900,   20, 300),
    ("Wall_A_East",      900,  550,  150,   20,  800, 300),
    # room B  (x 900..1500, y -950..-150)
    ("Wall_B_West",      900, -550,  150,   20,  800, 300),
    ("Wall_B_South",    1200, -950,  150,  600,   20, 300),
    ("Wall_B_East",     1500, -550,  150,   20,  800, 300),
    # steps in room A (20cm risers)
    ("Stair_1",          650,  900,   10,  500,  100,  20),
    ("Stair_2",          650,  800,   20,  500,  100,  40),
    ("Stair_3",          650,  700,   30,  500,  100,  60),
    # gameplay test props
    ("Cover_Corr",       700,  -40,   55,   80,  200, 110),
    ("Crate_B",         1200, -500,   60,  120,  120, 120),
]


def build():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

    if eas is None or les is None:
        raise RuntimeError("editor subsystem not available (EditorActorSubsystem / LevelEditorSubsystem)")

    # ---- new empty level -------------------------------------------------
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        log("removing old level %s" % LEVEL_PATH)
        unreal.EditorAssetLibrary.delete_asset(LEVEL_PATH)
    ok = les.new_level(LEVEL_PATH)
    log("new_level(%s) -> %s" % (LEVEL_PATH, ok))

    cube = unreal.load_asset(CUBE)
    mat = unreal.load_asset(MAT)
    if cube is None:
        raise RuntimeError("cube mesh not found: %s" % CUBE)

    # ---- blockout boxes --------------------------------------------------
    for label, cx, cy, cz, sx, sy, sz in BOXES:
        a = eas.spawn_actor_from_class(
            unreal.StaticMeshActor,
            unreal.Vector(float(cx), float(cy), float(cz)),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0),
        )
        a.set_actor_label(label)
        a.set_actor_scale3d(unreal.Vector(sx / 100.0, sy / 100.0, sz / 100.0))
        smc = a.static_mesh_component
        smc.set_static_mesh(cube)
        if mat is not None:
            smc.set_material(0, mat)
        try:
            a.set_folder_path("Whitebox")
        except Exception:
            pass
        log("  spawned %s  size=(%d,%d,%d)  at (%d,%d,%d)" % (label, sx, sy, sz, cx, cy, cz))

    # ---- lights ----------------------------------------------------------
    sun = eas.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0.0, 0.0, 800.0),
        unreal.Rotator(roll=0.0, pitch=-50.0, yaw=20.0),
    )
    sun.set_actor_label("Sun")
    try:
        comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            comp.set_intensity(8.0)
    except Exception as e:
        log("sun intensity skipped: %s" % e)

    sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 300.0), unreal.Rotator())
    sky.set_actor_label("SkyLight")
    try:
        sc = sky.get_component_by_class(unreal.SkyLightComponent)
        if sc:
            sc.set_editor_property("real_time_capture", True)
            sc.set_intensity(2.0)
    except Exception as e:
        log("skylight setup skipped: %s" % e)

    try:
        atm = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
        atm.set_actor_label("SkyAtmosphere")
    except Exception as e:
        log("sky atmosphere skipped: %s" % e)

    # ---- player start ----------------------------------------------------
    try:
        ps = eas.spawn_actor_from_class(
            unreal.PlayerStart,
            unreal.Vector(120.0, 0.0, 100.0),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0),
        )
        ps.set_actor_label("PlayerStart")
        log("PlayerStart spawned at (120,0,100) facing +X")
    except Exception as e:
        log("PlayerStart failed: %s" % e)

    # ---- save ------------------------------------------------------------
    saved = les.save_current_level()
    log("save_current_level -> %s" % saved)

    total = 0
    try:
        total = len(eas.get_all_level_actors())
    except Exception:
        pass
    log("total actors in level: %d" % total)
    log("=== BUILD OK ===")


def tick(delta_seconds):
    if _state["done"]:
        return
    _state["ticks"] += 1
    if _state["ticks"] < 4:
        return
    _state["done"] = True

    handle = _state["handle"]
    if handle is not None:
        try:
            unreal.unregister_slate_post_tick_callback(handle)
        except Exception:
            pass

    try:
        build()
    except Exception:
        log("=== BUILD FAILED ===")
        log(traceback.format_exc())


reset_log()

import os
if os.environ.get("WHITEBOX_IMMEDIATE") == "1":
    log("immediate mode: building now (commandlet)")
    try:
        build()
    except Exception:
        log("=== BUILD FAILED ===")
        log(traceback.format_exc())
else:
    log("interactive mode: waiting for editor to become ready ...")
    _state["handle"] = unreal.register_slate_post_tick_callback(tick)
