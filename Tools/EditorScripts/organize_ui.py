# -*- coding: utf-8 -*-
"""把散落在各处的 UI 资产归集到 /Game/UI 下，便于逐个打开调位置。

用法（编辑器关闭时）：
  UnrealEditor-Cmd.exe Food.uproject -run=pythonscript -script=organize_ui.py

默认 DRY_RUN = True，只打印计划；确认无误后改成 False 真正移动。
移动走 EditorAssetLibrary.rename_asset，引用会被自动修正。
"""
import json
import os

import unreal

DRY_RUN = False

ROOT = "/Game/UI"

# 目标目录 -> 资产
PLAN = {
    "/Game/UI/Widgets/Menus": [],
    "/Game/UI/Widgets/HUD": [
        "/Game/FoodGameplay/WBP_InstructionHUD",
        "/Game/FoodGameplay/WBP_InteractPrompt",
        "/Game/FirstPerson/Blueprints/WBP_GrabReticle",
    ],
    "/Game/UI/Widgets/Panels": [
        "/Game/FoodGameplay/WBP_RecipeGuide",
        "/Game/FoodGameplay/WBP_ChefIntro",
        "/Game/FoodGameplay/WBP_ChefEnding",
        "/Game/FoodGameplay/WBP_PauseBasic",
        "/Game/FoodGameplay/WBP_Tray",
    ],
    "/Game/UI/Widgets/Progress": [
        "/Game/FoodGameplay/WBP_BakingProgress",
        "/Game/FoodGameplay/WBP_RollingProgress",
    ],
    "/Game/UI/Art/Backgrounds": [
        "/Game/FoodGameplay/MenuAssets/T_MainMenuBackground",
        "/Game/FoodGameplay/MenuAssets/T_MenuTitlePlaque",
        "/Game/FoodGameplay/MenuAssets/T_MenuTitleText",
    ],
    "/Game/UI/Art/Buttons": [
        "/Game/FoodGameplay/MenuAssets/T_MenuButton",
        "/Game/FoodGameplay/MenuAssets/T_Label_start",
        "/Game/FoodGameplay/MenuAssets/T_Label_settings",
        "/Game/FoodGameplay/MenuAssets/T_Label_quit",
    ],
    "/Game/UI/Art/Frames": [
        "/Game/FoodGameplay/UI/T_WoodParchmentFrame",
        "/Game/UI/Textures/T_DialogFrame",
        "/Game/UI/Textures/T_SlotFrame",
    ],
    "/Game/UI/Art/Medals": [
        "/Game/FoodGameplay/AchievementMedals/achievement_dough_beginner",
        "/Game/FoodGameplay/AchievementMedals/achievement_knife_skills",
        "/Game/FoodGameplay/AchievementMedals/achievement_seven_fish_heads",
        "/Game/FoodGameplay/AchievementMedals/achievement_heat_master",
        "/Game/FoodGameplay/AchievementMedals/achievement_chef_approval",
        "/Game/FoodGameplay/AchievementMedals/achievement_shared_pie",
    ],
    "/Game/UI/Art/Icon": [
        "/Game/FoodGameplay/MenuAssets/T_GameIcon",
    ],
    "/Game/UI/Fonts": [
        "/Game/UI/Fonts/F_Butter",
        "/Game/UI/Fonts/F_Butter_Font",
        "/Game/UI/Fonts/F_KuaiLe",
        "/Game/UI/Fonts/F_KuaiLe_Font",
        "/Game/UI/Fonts/ZCOOLKuaiLe",
    ],
}

log = []


def name_of(path):
    return path.rsplit("/", 1)[-1]


def main():
    eal = unreal.EditorAssetLibrary
    for folder in PLAN:
        if not eal.does_directory_exist(folder):
            if DRY_RUN:
                log.append("MKDIR %s" % folder)
            else:
                eal.make_directory(folder)

    moved = 0
    missing = []
    for folder, assets in PLAN.items():
        for src in assets:
            if not eal.does_asset_exist(src):
                missing.append(src)
                continue
            dst = "%s/%s" % (folder, name_of(src))
            if src == dst:
                continue
            if eal.does_asset_exist(dst):
                log.append("SKIP-EXISTS %s -> %s" % (src, dst))
                continue
            if DRY_RUN:
                log.append("MOVE %s -> %s" % (src, dst))
            else:
                if eal.rename_asset(src, dst):
                    log.append("OK %s -> %s" % (src, dst))
                    moved += 1
                else:
                    log.append("FAIL %s -> %s" % (src, dst))
    if not DRY_RUN:
        eal.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

    out = {
        "dry_run": DRY_RUN,
        "moved": moved,
        "missing": missing,
        "log": log,
    }
    path = os.path.join(unreal.Paths.project_saved_dir(), "organize_ui.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    unreal.log("[organize_ui] wrote %s (moved=%d missing=%d)" % (path, moved, len(missing)))


main()
