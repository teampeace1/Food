import unreal,json
out={}
for name in ('BP_Workstation','BP_Sink','BP_ChoppingBoard_Prototype'):
 bp=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/'+name)
 out[name]={}
 for graphname in ('Interact','EventGraph'):
  try:
   graph=unreal.BlueprintEditorLibrary.find_graph(bp,graphname)
   ed=unreal.BlueprintGraphEditor.get_graph_editor(graph) if graph else None
   out[name][graphname]=[{'name':n.get_name(),'title':str(n.get_node_title()),'pins':[{'name':str(p.get_pin_name()),'value':str(p.get_pin_value()),'links':[str(q.get_owning_node().get_name())+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]} for p in n.list_all_pins()]} for n in ed.list_all_nodes()] if ed else []
  except Exception as e:out[name][graphname]=repr(e)
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
