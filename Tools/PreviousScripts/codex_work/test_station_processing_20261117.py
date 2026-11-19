import unreal,json,traceback
out={'checks':[]}
try:
 w=unreal.EditorLevelLibrary.get_pie_worlds(False)[0];p=unreal.GameplayStatics.get_player_character(w,0);sys=unreal.get_default_object(unreal.SystemLibrary);gs=unreal.get_default_object(unreal.GameplayStatics)
 actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor);chop=next(a for a in actors if a.get_class().get_name()=='BP_ChoppingBoard_C');sink=next(a for a in actors if a.get_class().get_name()=='BP_Sink_C');roll=next(a for a in actors if a.get_class().get_name()=='BP_RollingStation_C');cls=unreal.load_class(None,'/Game/FoodGameplay/BP_Ingredient.BP_Ingredient_C')
 def put(o,n,v):
  typ='Bool' if isinstance(v,bool) else 'Int' if isinstance(v,int) else 'String' if isinstance(v,str) else 'Object';sys.call_method('Set'+typ+'PropertyByName',args=(o,n,v))
 def spawn(typ,state):
  tr=unreal.Transform(location=unreal.Vector(0,0,2000));a=gs.call_method('BeginDeferredActorSpawnFromClass',args=(w,cls,tr,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));gs.call_method('FinishSpawningActor',args=(a,tr,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));put(a,'Type',typ);put(a,'State',state);return a
 def carry(a):
  comp=a.get_component_by_class(unreal.StaticMeshComponent);put(p,'HeldActor',a);put(p,'HeldComponent',comp);put(p,'bIsHolding',True);put(p,'TraySlot1',a);put(p,'TraySlot1Component',comp);put(p,'SelectedSlot',1)
 def get(o,n):return o.get_editor_property(n)
 def ck(name,ok,info):out['checks'].append({'test':name,'pass':bool(ok),'detail':info})
 fish=spawn('鱼','Washed');put(fish,'bWashed',True);put(fish,'bWashable',True);carry(fish);chop.call_method('PlaceStationItem')
 ck('place fish releases slot and stores item',get(chop,'StationItem')==fish and get(p,'HeldActor') is None and get(p,'TraySlot1') is None,{'station':str(get(chop,'StationItem')),'item_loc':str(fish.get_actor_location())})
 for i in range(3):chop.call_method('Interact')
 ck('station chopping',get(fish,'CutCount')==3 and get(fish,'State')=='Cut',{'count':get(fish,'CutCount'),'state':get(fish,'State')})
 chop.call_method('TakeStationItem');ck('take visible item and slot',get(p,'HeldActor')==fish and get(p,'TraySlot1')==fish and get(chop,'StationItem') is None and fish.get_editor_property('root_component').get_attach_parent()==p.get_component_by_class(unreal.CameraComponent),{'relative':str(fish.get_actor_transform()),'hidden':fish.get_editor_property('hidden')})
 # Wrong ingredient must remain held and leave station empty.
 roll.call_method('PlaceStationItem');ck('wrong station rejects fish',get(p,'HeldActor')==fish and get(roll,'StationItem') is None,'fish held')
 for n in ['HeldActor','HeldComponent','TraySlot1','TraySlot1Component']:put(p,n,None)
 put(p,'bIsHolding',False)
 dough=spawn('面团','Raw');carry(dough);roll.call_method('PlaceStationItem');ck('place dough',get(roll,'StationItem')==dough and get(p,'HeldActor') is None,'placed')
 roll.call_method('BeginRolling');ck('roll starts on station item',get(roll,'bRolling') and get(roll,'RollTarget')==dough,{'rolling':get(roll,'bRolling')})
 # Finish with a known accepted value while the item is on the station.
 sys.call_method('SetDoublePropertyByName',args=(dough,'RollProgress',95.));roll.call_method('FinishRolling');ck('finish thin pie on station',get(dough,'State')=='PieBase' and get(dough,'RollQuality')=='Thin',{'state':get(dough,'State'),'quality':get(dough,'RollQuality')})
 roll.call_method('TakeStationItem');ck('take rolled pie base',get(p,'HeldActor')==dough and get(roll,'StationItem') is None,'retrieved')
 for n in ['HeldActor','HeldComponent','TraySlot1','TraySlot1Component']:put(p,n,None)
 put(p,'bIsHolding',False)
 onion=spawn('洋葱','Raw');put(onion,'bWashable',True);carry(onion);sink.call_method('PlaceStationItem');sink.call_method('Interact');ck('start wash on station',get(sink,'bRunning') and get(sink,'WashTarget')==onion,{'running':get(sink,'bRunning')})
except Exception:out['error']=traceback.format_exc()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/station_processing_tests.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))


