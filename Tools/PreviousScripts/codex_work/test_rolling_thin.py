import unreal,json,traceback
out=[]
try:
 w=unreal.EditorLevelLibrary.get_pie_worlds(False)[0];p=unreal.GameplayStatics.get_player_character(w,0);s=unreal.get_default_object(unreal.SystemLibrary);gs=unreal.get_default_object(unreal.GameplayStatics)
 roll=next(a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor) if a.get_class().get_name()=='BP_RollingStation_C');cls=unreal.load_class(None,'/Game/FoodGameplay/BP_Ingredient.BP_Ingredient_C')
 tr=unreal.Transform(location=roll.get_actor_location()+unreal.Vector(0,0,120));item=gs.call_method('BeginDeferredActorSpawnFromClass',args=(w,cls,tr,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));gs.call_method('FinishSpawningActor',args=(item,tr,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
 def setp(o,n,v):
  typ='Bool' if isinstance(v,bool) else 'Double' if isinstance(v,float) else 'String' if isinstance(v,str) else 'Object';s.call_method('Set'+typ+'PropertyByName',args=(o,n,v))
 for x in [89.,90.,91.,100.]:
  setp(item,'State','Raw');setp(item,'RollProgress',x);setp(roll,'RollTarget',item);setp(roll,'bRolling',True);setp(p,'HeldActor',item);roll.call_method('FinishRolling')
  state=item.get_editor_property('State');quality=item.get_editor_property('RollQuality');out.append({'progress':x,'state':state,'quality':quality,'pass':state=='PieBase' and quality==('Thin' if x>90 else 'Normal')})
except Exception:out.append({'error':traceback.format_exc()})
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
