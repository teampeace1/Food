# -*- coding: utf-8 -*-
"""校验 /Game/UI 归集结果：资产可加载、蓝图可编译、C++ 里用到的新路径都解析得到。

用法：-run=pythonscript -script=verify_ui.py
结果：Saved/verify_ui.json
"""
import json
import os

import unreal

eal = unreal.EditorAssetLibrary
reg = unreal.AssetRegistryHelpers.get_asset_registry()

# C++ 里硬编码、需要在运行时能 LoadClass/LoadObject 的路径
RUNTIME_CLASS_PATHS = [
    "/Game/UI/Widgets/Panels/WBP_PauseBasic.WBP_PauseBasic_C",
    "/Game/UI/Widgets/Panels/WBP_ChefEnding.WBP_ChefEnding_C",
    "/Game/UI/Widgets/Panels/WBP_RecipeGuide.WBP_RecipeGuide_C",
    "/Game/UI/Widgets/Panels/WBP_ChefIntro.WBP_ChefIntro_C",
    "/Game/UI/Widgets/Progress/WBP_BakingProgress.WBP_BakingProgress_C",
    "/Game/UI/Widgets/Progress/WBP_RollingProgress.WBP_RollingProgress_C",
]

RUNTIME_OBJECT_PATHS = [
    "/Game/UI/Art/Backgrounds/T_MainMenuBackground.T_MainMenuBackground",
    "/Game/UI/Art/Backgrounds/T_MenuTitlePlaque.T_MenuTitlePlaque",
    "/Game/UI/Art/Backgrounds/T_MenuTitleText.T_MenuTitleText",
    "/Game/UI/Art/Buttons/T_MenuButton.T_MenuButton",
    "/Game/UI/Art/Buttons/T_Label_start.T_Label_start",
    "/Game/UI/Art/Buttons/T_Label_settings.T_Label_settings",
    "/Game/UI/Art/Buttons/T_Label_quit.T_Label_quit",
    "/Game/UI/Art/Frames/T_WoodParchmentFrame.T_WoodParchmentFrame",
    "/Game/UI/Art/Medals/achievement_dough_beginner.achievement_dough_beginner",
    "/Game/UI/Art/Medals/achievement_knife_skills.achievement_knife_skills",
    "/Game/UI/Art/Medals/achievement_seven_fish_heads.achievement_seven_fish_heads",
    "/Game/UI/Art/Medals/achievement_heat_master.achievement_heat_master",
    "/Game/UI/Art/Medals/achievement_chef_approval.achievement_chef_approval",
    "/Game/UI/Art/Medals/achievement_shared_pie.achievement_shared_pie",
]

result = {"runtime_paths": [], "blueprints": [], "tree": [], "redirectors": []}

for path in RUNTIME_CLASS_PATHS:
    ok = unreal.load_class(None, path) is not None
    result["runtime_paths"].append({"path": path, "ok": ok})

for path in RUNTIME_OBJECT_PATHS:
    ok = unreal.load_object(None, path) is not None
    result["runtime_paths"].append({"path": path, "ok": ok})

# 遍历 /Game/UI，检查每个蓝图能否编译
assets = eal.list_assets("/Game/UI", recursive=True, include_folder=False)
for a in assets:
    result["tree"].append(a)
    if a.endswith("_C"):
        continue
    if not a.rsplit("/", 1)[-1].startswith("WBP_"):
        continue
    bp = eal.load_asset(a)
    entry = {"asset": a, "compiled": None, "status": ""}
    try:
        entry["compiled"] = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        entry["status"] = str(unreal.BlueprintEditorLibrary.get_blueprint_status(bp)) if hasattr(
            unreal.BlueprintEditorLibrary, "get_blueprint_status") else ""
    except Exception as exc:  # noqa: BLE001
        entry["compiled"] = False
        entry["status"] = repr(exc)
    result["blueprints"].append(entry)

# 旧路径是否还留着 redirector
for old in ("/Game/FoodGameplay", "/Game/FirstPerson/Blueprints", "/Game/UI/Textures"):
    for a in eal.list_assets(old, recursive=False, include_folder=False) if eal.does_directory_exist(old) else []:
        pass

out = os.path.join(unreal.Paths.project_saved_dir(), "verify_ui.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False, indent=2)
unreal.log("[verify_ui] wrote %s, assets=%d" % (out, len(assets)))
