import unreal,json
path='/Game/FoodGameplay/TempCharacterProbe'
if unreal.EditorAssetLibrary.does_asset_exist(path):unreal.EditorAssetLibrary.delete_asset(path)
unreal.EditorAssetLibrary.duplicate_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter',path)
bp=unreal.EditorAssetLibrary.load_asset(path)
ed=unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
a=ed.add_branch_node();b=ed.add_branch_node();p=ed.create_node_from_name('开发|PrintString',unreal.Vector2D(0,0),[])
def pin(n,x):return next(v for v in n.list_all_pins() if str(v.get_pin_name())==x)
out=[pin(a,'then').try_create_connection(pin(p,'execute')),pin(b,'then').try_create_connection(pin(p,'execute'))]
out.append([str(x.get_owning_node().get_name()) for x in pin(p,'execute').list_connected_pins()])
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_exec_probe.json','w') as f:json.dump(out,f)
