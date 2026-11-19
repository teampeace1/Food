import unreal,json
out={}
for name in ['BP_FillingBowl','BP_Pie','BP_Workstation','BP_FirstPersonCharacter']:
 path=('/Game/FirstPerson/Blueprints/' if name=='BP_FirstPersonCharacter' else '/Game/FoodGameplay/')+name
 bp=unreal.EditorAssetLibrary.load_asset(path);out[name]={}
 for gr in unreal.BlueprintEditorLibrary.list_graphs(bp):
  ed=unreal.BlueprintGraphEditor.get_graph_editor(gr)
  if not ed:continue
  out[name][gr.get_name()]=[{'id':n.get_name(),'title':str(n.get_node_title()),'pins':[{'n':str(p.get_pin_name()),'v':str(p.get_pin_value()),'l':[q.get_owning_node().get_name()+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]} for p in n.list_all_pins()]} for n in ed.list_all_nodes()]
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/audit_assembly.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps({'done':True}))
