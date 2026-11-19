import unreal
path='/Game/FoodGameplay/WBP_Tray'
bp=unreal.EditorAssetLibrary.load_asset(path)
if not bp:
    bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('WBP_Tray','/Game/FoodGameplay',unreal.WidgetBlueprint,unreal.WidgetBlueprintFactory())
    unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=False)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([bp])
