import unreal, json
out={}
for name in ('K2Node_DynamicCast','K2Node_CallFunction','K2Node_VariableGet','K2Node_VariableSet','BlueprintGraphPin','BlueprintGraphEditor','BlueprintEditorLibrary'):
    out[name]=str(getattr(unreal,name,None))
bp=unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
g=unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
out['graph_methods']=[x for x in dir(g) if 'node' in x.lower() or 'add' in x.lower()]
out['editor_methods']=[x for x in dir(ed) if 'node' in x.lower() or 'pin' in x.lower() or 'connect' in x.lower()]
out['cast_properties']=[str(x) for x in dir(unreal.K2Node_DynamicCast) if 'target' in x.lower() or 'cast' in x.lower()]
out['cast_methods']=[str(x) for x in dir(unreal.K2Node_DynamicCast) if 'pin' in x.lower() or 'node' in x.lower()]
out['pin_methods']=[x for x in dir(unreal.BlueprintGraphPin) if 'connect' in x.lower() or 'link' in x.lower() or 'default' in x.lower()]
out['all_pin_methods']=[x for x in dir(unreal.BlueprintGraphPin) if not x.startswith('_')]
out['editor_add_call_doc']=str(ed.add_call_function_node.__doc__)
out['editor_add_get_doc']=str(ed.add_get_member_variable_node.__doc__)
out['editor_branch_doc']=str(ed.add_branch_node.__doc__)
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_api_probe.json','w') as f: json.dump(out,f,indent=2)
