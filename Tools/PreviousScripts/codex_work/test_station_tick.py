import unreal,json,traceback,time
w=unreal.EditorLevelLibrary.get_pie_worlds(False)[0];p=unreal.GameplayStatics.get_player_character(w,0);gs=unreal.get_default_object(unreal.GameplayStatics);sys=unreal.get_default_object(unreal.SystemLibrary);roll=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RollingStation_C');cls=unreal.load_class(None,'/Game/FoodGameplay/BP_Ingredient.BP_Ingredient_C')
tr=unreal.Transform(location=roll.get_actor_location()+unreal.Vector(0,0,120));item=gs.call_method('BeginDeferredActorSpawnFromClass',args=(w,cls,tr,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));gs.call_method('FinishSpawningActor',args=(item,tr,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
def setp(o,n,v):
 t='Bool' if isinstance(v,bool) else 'String' if isinstance(v,str) else 'Object';sys.call_method('Set'+t+'PropertyByName',args=(o,n,v))
setp(item,'Type','面团');setp(item,'State','Raw');setp(p,'HeldActor',item);setp(p,'HeldComponent',item.get_component_by_class(unreal.StaticMeshComponent));setp(p,'bIsHolding',True);setp(p,'TraySlot1',item);roll.call_method('PlaceStationItem');roll.call_method('BeginRolling');start=unreal.GameplayStatics.get_time_seconds(w);wall=time.monotonic()
def tick(dt):
 elapsed=unreal.GameplayStatics.get_time_seconds(w)-start
 if elapsed<1 and time.monotonic()-wall<20:return
 out={'elapsed':elapsed,'progress':item.get_editor_property('RollProgress'),'rate':roll.get_editor_property('ProgressRate'),'running':roll.get_editor_property('bRolling'),'on_station':roll.get_editor_property('StationItem')==item,'widget':str(roll.get_editor_property('ProgressWidget'))}
 out['pass']=out['running'] and out['on_station'] and abs(out['progress']-elapsed*out['rate'])<2
 roll.call_method('CancelRolling');unreal.unregister_slate_post_tick_callback(handle)
 with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/station_tick_test.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
handle=unreal.register_slate_post_tick_callback(tick)
unreal.MCPythonHelper.submit_result(json.dumps({'started':True}))
