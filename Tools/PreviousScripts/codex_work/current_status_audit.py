import unreal,json,traceback
out={'assets':{},'actors':[]}
try:
 bel=unreal.BlueprintEditorLibrary
 for name in ['BP_Ingredient','BP_IngredientSupply','BP_Sink','BP_ChoppingBoard','BP_RollingStation','BP_FillingBowl','BP_Pie','BP_FirstPersonCharacter','WBP_InteractPrompt','WBP_RollingProgress','WBP_Tray']:
  path=('/Game/FirstPerson/Blueprints/' if name=='BP_FirstPersonCharacter' else '/Game/FoodGameplay/')+name
  bp=unreal.EditorAssetLibrary.load_asset(path)
  d={'exists':bool(bp)};out['assets'][name]=d
  if not bp:continue
  d['vars']=[str(v) for v in bel.list_member_variable_names(bp) if not str(v).startswith('/Script/')]
  d['graphs']=[str(g.get_name()) for g in bel.list_graphs(bp)]
  d['errors']=[]
  for g in bel.list_graphs(bp):
   ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
   if ed:d['errors'] += [str(n.get_node_title()) for n in ed.list_nodes_with_errors()]
 for a in unreal.EditorLevelLibrary.get_all_level_actors():
  cls=a.get_class().get_name()
  if cls.startswith('BP_'):
   out['actors'].append({'label':a.get_actor_label(),'class':cls,'pos':str(a.get_actor_location())})
 out['dirty']=[str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]+[str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
except Exception:out['error']=traceback.format_exc()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/current_status_audit.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
