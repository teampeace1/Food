import unreal,json
out={}
for name in ['BP_Sink','BP_Ingredient','BP_Workstation']:
 bp=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/'+name)
 out[name]={'variables':[str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp) if not str(x).startswith('/Script/')], 'graphs':{}}
 graphs=unreal.BlueprintEditorLibrary.get_all_graphs(bp) if hasattr(unreal.BlueprintEditorLibrary,'get_all_graphs') else [unreal.BlueprintEditorLibrary.find_event_graph(bp)]
 for g in graphs:
  if not g:continue
  ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
  if not ed:continue
  out[name]['graphs'][g.get_name()]=[{'name':n.get_name(),'title':str(n.get_node_title()),'pins':[{'name':str(p.get_pin_name()),'value':str(p.get_pin_value()),'links':[str(q.get_owning_node().get_name())+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]} for p in n.list_all_pins()]} for n in ed.list_all_nodes()]
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/audit_sink.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
