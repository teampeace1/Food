import unreal,json,traceback
out={'checks':[]}
try:
 w=unreal.EditorLevelLibrary.get_pie_worlds(False)[0];p=unreal.GameplayStatics.get_player_character(w,0);sys=unreal.get_default_object(unreal.SystemLibrary);gs=unreal.get_default_object(unreal.GameplayStatics)
 actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor);bowl=next(a for a in actors if a.get_class().get_name()=='BP_FillingBowl_C');pie=next(a for a in actors if a.get_class().get_name()=='BP_Pie_C');cls=unreal.load_class(None,'/Game/FoodGameplay/BP_Ingredient.BP_Ingredient_C')
 def put(o,n,v):
  t='Bool' if isinstance(v,bool) else 'Int' if isinstance(v,int) else 'String' if isinstance(v,str) else 'Object';sys.call_method('Set'+t+'PropertyByName',args=(o,n,v))
 def spawn():
  t=unreal.Transform(location=unreal.Vector(0,0,2000));a=gs.call_method('BeginDeferredActorSpawnFromClass',args=(w,cls,t,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));gs.call_method('FinishSpawningActor',args=(a,t,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));return a
 def get(o,n):return o.get_editor_property(n)
 def ck(name,ok,detail):out['checks'].append({'name':name,'pass':bool(ok),'detail':detail})
 keep=spawn()
 for slot in (1,2,3):
  item=spawn();comp=item.get_component_by_class(unreal.StaticMeshComponent)
  for i in (1,2,3):put(p,'TraySlot'+str(i),None);put(p,'TraySlot'+str(i)+'Component',None)
  other=slot%3+1;put(p,'TraySlot'+str(other),keep);put(p,'TraySlot'+str(slot),item);put(p,'TraySlot'+str(slot)+'Component',comp);put(p,'HeldActor',item);put(p,'HeldComponent',comp);put(p,'bIsHolding',True);put(p,'SelectedSlot',slot)
  p.call_method('DropHeldItem')
  ck('drop slot '+str(slot),get(p,'TraySlot'+str(slot)) is None and get(p,'TraySlot'+str(slot)+'Component') is None and get(p,'TraySlot'+str(other))==keep and get(p,'HeldActor') is None,{'target_slot':str(get(p,'TraySlot'+str(slot))),'other_kept':get(p,'TraySlot'+str(other))==keep})
 # Actual filling consumption function, with another slot occupied.
 item=spawn();put(p,'TraySlot1',item);put(p,'TraySlot2',keep);put(p,'HeldActor',item);put(p,'HeldComponent',item.get_component_by_class(unreal.StaticMeshComponent));put(p,'bIsHolding',True);put(bowl,'PendingActor',item)
 bowl.call_method('ConsumeHeld');ck('filling consumes and clears only its slot',get(p,'TraySlot1') is None and get(p,'TraySlot2')==keep and get(p,'HeldActor') is None,{'slot1':str(get(p,'TraySlot1')),'other_kept':get(p,'TraySlot2')==keep})
 # Place all seven heads using the one held group.
 group=spawn();put(group,'Type','鱼头');put(group,'HeadCount',7);put(p,'TraySlot1',group);put(p,'TraySlot2',keep);put(p,'HeldActor',group);put(p,'HeldComponent',group.get_component_by_class(unreal.StaticMeshComponent));put(p,'bIsHolding',True);put(pie,'PendingActor',group);put(pie,'HeadsPlaced',0);put(pie,'bReadyToBake',False)
 records=[]
 for i in range(7):
  pie.call_method('PlaceHead');records.append({'placed':get(pie,'HeadsPlaced'),'held':str(get(p,'HeldActor')),'slot':str(get(p,'TraySlot1')),'ready':get(pie,'bReadyToBake')})
 ck('one group places seven and clears slot',all(records[i]['placed']==i+1 for i in range(7)) and all('None' not in records[i]['held'] for i in range(6)) and get(pie,'bReadyToBake') and get(p,'TraySlot1') is None and get(p,'TraySlot2')==keep,records)
except Exception:out['error']=traceback.format_exc()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/tray_cleanup_tests.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
