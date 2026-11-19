import unreal,json,traceback
out={}
try:
 w=unreal.EditorLevelLibrary.get_pie_worlds(False)[0];p=unreal.GameplayStatics.get_player_character(w,0)
 def fmt(x):return str(x) if x else None
 def detail(a):
  if not a:return None
  mesh=a.get_component_by_class(unreal.StaticMeshComponent)
  d={'name':a.get_name(),'loc':str(a.get_actor_location()),'hidden':a.is_hidden(),'attach_parent':fmt(a.get_attach_parent_actor()),'root_parent':fmt(a.get_root_component().get_attach_parent())}
  if mesh:d.update({'component_visible':mesh.is_visible(),'simulating':mesh.is_simulating_physics(),'component_location':str(mesh.get_world_location()),'mesh':fmt(mesh.get_editor_property('static_mesh'))})
  for k in ['Type','State','HeldOffset']:
   try:d[k]=str(a.get_editor_property(k))
   except:pass
  return d
 out['player']={'location':str(p.get_actor_location()),'camera_location':str(p.get_component_by_class(unreal.CameraComponent).get_world_location()),'holding':p.get_editor_property('bIsHolding'),'selected':p.get_editor_property('SelectedSlot'),'held_component':fmt(p.get_editor_property('HeldComponent')),'held':detail(p.get_editor_property('HeldActor'))}
 for n in ['TraySlot1','TraySlot2','TraySlot3']:out['player'][n]=detail(p.get_editor_property(n))
 bp=unreal.load_object(None,'/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter')
 out['graphs']={}
 for name in ['DropHeldItem','EventGraph']:
  g=unreal.BlueprintEditorLibrary.find_graph(bp,name);ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
  selected=['K2Node_CallFunction_99','K2Node_CallFunction_101','K2Node_CallFunction_102','K2Node_CallFunction_103','K2Node_VariableSet_50','K2Node_VariableSet_51','K2Node_VariableSet_52','K2Node_VariableGet_39']
  out['graphs'][name]=[{'id':n.get_name(),'title':str(n.get_node_title()),'pins':[{'n':str(x.get_pin_name()),'v':str(x.get_pin_value()),'links':[q.get_owning_node().get_name()+'.'+str(q.get_pin_name()) for q in x.list_connected_pins()]} for x in n.list_all_pins()]} for n in ed.list_all_nodes() if name=='DropHeldItem' or n.get_name() in selected]
except Exception:out['error']=traceback.format_exc()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/hand_state_current.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
