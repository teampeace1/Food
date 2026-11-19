import unreal, json
path='/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter'
bp=unreal.EditorAssetLibrary.load_asset(path)
ed=unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
nodes={n.get_name():n for n in ed.list_all_nodes()}
def p(n,name):return next(x for x in nodes[n].list_all_pins() if str(x.get_pin_name())==name)
dest=p('K2Node_IfThenElse_2','execute')
sources=list(dest.list_connected_pins())
dest.break_pin_links()
valid=ed.add_call_function_node('/Script/Engine.KismetSystemLibrary:IsValid')
branch=ed.add_branch_node()
valid.set_node_pos(unreal.IntPoint(3100,850));branch.set_node_pos(unreal.IntPoint(3300,850))
def q(n,name):return next(x for x in n.list_all_pins() if str(x.get_pin_name())==name)
assert p('K2Node_CallFunction_15','HitComponent').try_create_connection(q(valid,'Object'))
assert q(valid,'ReturnValue').try_create_connection(q(branch,'Condition'))
for source in sources:assert source.try_create_connection(q(branch,'execute'))
assert q(branch,'then').try_create_connection(dest)
ok=unreal.BlueprintEditorLibrary.compile_blueprint(bp)
errors=[str(n.get_node_title()) for n in ed.list_nodes_with_errors()]
saved=unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=False) if ok and not errors else False
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_fix_hit_component_result.json','w',encoding='utf-8') as f:json.dump({'compiled':ok,'errors':errors,'saved':saved},f)
