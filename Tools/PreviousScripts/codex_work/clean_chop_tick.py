import unreal,json
bp=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_ChoppingBoard_Test')
ed=unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
nodes={n.get_name():n for n in ed.list_all_nodes()}
tick=nodes['K2Node_Event_3']
next(p for p in tick.list_all_pins() if str(p.get_pin_name())=='then').break_pin_links()
ok=unreal.BlueprintEditorLibrary.compile_blueprint(bp)
saved=unreal.EditorAssetLibrary.save_asset('/Game/FoodGameplay/BP_ChoppingBoard_Test',only_if_is_dirty=False) if ok else False
unreal.MCPythonHelper.submit_result(json.dumps({'compiled':ok,'saved':saved}))
