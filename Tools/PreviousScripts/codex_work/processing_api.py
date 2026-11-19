import unreal,json
bel=unreal.BlueprintEditorLibrary
out={x:str(getattr(bel,x).__doc__) for x in ['add_function_graph','add_function_override','list_graphs','list_graph_names','rename_graph']}
out['dirty']=[x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
bp=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_RollingStation'); ed=unreal.BlueprintGraphEditor.get_graph_editor(bel.find_event_graph(bp))
out['nodes']=[x for x in ed.list_available_nodes([]) if any(s in x for s in ['LeftMouse','左键','CreateWidget','创建控件'])][:20]
out['addpin']=str(ed.add_node_pin.__doc__)
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/processing_api.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps({'done':True}))
