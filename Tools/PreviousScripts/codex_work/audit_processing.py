import unreal,json
out={}
bel=unreal.BlueprintEditorLibrary
out['api']=[x for x in dir(bel) if 'graph' in x or 'function' in x]
for name in ['BP_ChoppingBoard','BP_RollingStation','BP_Ingredient','BP_Workstation','BP_FirstPersonCharacter']:
 path='/Game/FirstPerson/Blueprints/'+name if name=='BP_FirstPersonCharacter' else '/Game/FoodGameplay/'+name
 bp=unreal.EditorAssetLibrary.load_asset(path)
 out[name]={'vars':[str(x) for x in bel.list_member_variable_names(bp) if not str(x).startswith('/Script/')],'graphs':{}}
 for gn in ['EventGraph','Interact','RefreshLook','StartProcessing','StopProcessing','Process','BeginRoll','EndRoll']:
  g=bel.find_graph(bp,gn)
  if not g:continue
  ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
  out[name]['graphs'][gn]=[{'name':n.get_name(),'title':str(n.get_node_title()),'pins':[{'name':str(p.get_pin_name()),'v':str(p.get_pin_value()),'links':[q.get_owning_node().get_name()+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]} for p in n.list_all_pins()]} for n in ed.list_all_nodes()]
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/audit_processing.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps({'done':True}))
