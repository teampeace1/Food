import unreal,json
path='/Game/FoodGameplay/TempCharacterProbe'
if unreal.EditorAssetLibrary.does_asset_exist(path):unreal.EditorAssetLibrary.delete_asset(path)
unreal.EditorAssetLibrary.duplicate_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter',path)
bp=unreal.EditorAssetLibrary.load_asset(path)
ed=unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
ingredient=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_Ingredient')
unreal.BlueprintEditorLibrary.compile_blueprint(ingredient)
n=ed.create_node_from_name('游戏|从类生成Actor',unreal.Vector2D(13000,0),[])
p=next(x for x in n.list_all_pins() if str(x.get_pin_name())=='Class')
out={}
for value in [ingredient.generated_class().get_path_name(),ingredient.generated_class().get_name()]:
    try:out[value]=[p.set_pin_value(value),str(p.get_pin_value())]
    except Exception as e:out[value]=repr(e)
out['compile']=str(unreal.BlueprintEditorLibrary.compile_blueprint(bp))
out['errors']=[str(x.get_node_title()) for x in ed.list_nodes_with_errors()]
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_spawn_probe.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
