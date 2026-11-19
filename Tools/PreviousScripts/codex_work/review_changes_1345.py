import unreal,json,traceback
out={'assets':{},'actors':[]}
try:
 bel=unreal.BlueprintEditorLibrary
 for name in ['BP_FirstPersonCharacter','BP_Ingredient','BP_IngredientSupply','BP_RollingStation','BP_FillingBowl','BP_Pie','WBP_InteractPrompt']:
  path=('/Game/FirstPerson/Blueprints/' if name=='BP_FirstPersonCharacter' else '/Game/FoodGameplay/')+name
  bp=unreal.load_object(None,path+'.'+name);d={'vars':[str(v) for v in bel.list_member_variable_names(bp)],'graphs':{}};out['assets'][name]=d
  for gr in bel.list_graphs(bp):
   ed=unreal.BlueprintGraphEditor.get_graph_editor(gr)
   if not ed:continue
   d['graphs'][gr.get_name()]=[{'id':n.get_name(),'title':str(n.get_node_title()),'class':n.get_class().get_name(),'pins':[{'n':str(p.get_pin_name()),'v':str(p.get_pin_value()),'l':[q.get_owning_node().get_name()+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]} for p in n.list_all_pins()]} for n in ed.list_all_nodes()]
 world=unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
 for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor):
  cls=a.get_class().get_name()
  if cls in ['BP_IngredientSupply_C','BP_Ingredient_C','BP_Pie_C','BP_FillingBowl_C','BP_RollingStation_C','BP_FirstPersonCharacter_C']:
   d={'name':a.get_name(),'class':cls}
   for k in ['IngredientName','Type','State','Stock','HeadsPlaced','FilledCount','bReadyToBake','SelectedSlot','Heat','AcceptMax','PerfectMax']:
    try:d[k]=a.get_editor_property(k)
    except:pass
   out['actors'].append(d)
except Exception:out['error']=traceback.format_exc()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/review_1345.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2,default=str)
unreal.MCPythonHelper.submit_result(json.dumps({'done':True,'error':out.get('error'),'actors':out['actors']},ensure_ascii=False))
