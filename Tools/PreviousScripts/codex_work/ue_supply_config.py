import unreal,json
path='/Game/FoodGameplay/BP_IngredientSupply'
bp=unreal.EditorAssetLibrary.load_asset(path)
bel=unreal.BlueprintEditorLibrary
for name in ('IngredientName','Stock'):
    bel.set_blueprint_variable_instance_editable(bp,name,True)
bel.compile_blueprint(bp)
cdo=unreal.get_default_object(bp.generated_class())
cdo.set_editor_property('Stock',2)
result={'vars':[str(x) for x in bel.list_member_variable_names(bp)],'stock':cdo.get_editor_property('Stock'),'save':unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=False)}
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_supply_config.json','w',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
