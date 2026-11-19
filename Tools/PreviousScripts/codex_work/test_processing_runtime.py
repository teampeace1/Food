import unreal,json,traceback
out={'checks':[]}
try:
 world=unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
 player=unreal.GameplayStatics.get_player_character(world,0)
 sys=unreal.get_default_object(unreal.SystemLibrary);gs=unreal.get_default_object(unreal.GameplayStatics)
 def setp(o,n,v):
  typ='Bool' if isinstance(v,bool) else 'Int' if isinstance(v,int) else 'Double' if isinstance(v,float) else 'String' if isinstance(v,str) else 'Object'
  sys.call_method('Set'+typ+'PropertyByName',args=(o,n,v))
 def check(name,condition,details):out['checks'].append({'test':name,'pass':bool(condition),'details':details})
 actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
 chop=next(a for a in actors if a.get_class().get_name()=='BP_ChoppingBoard_C')
 roll=next(a for a in actors if a.get_class().get_name()=='BP_RollingStation_C')
 icls=unreal.load_class(None,'/Game/FoodGameplay/BP_Ingredient.BP_Ingredient_C')
 transform=unreal.Transform(location=roll.get_actor_location()+unreal.Vector(0,0,120))
 item=gs.call_method('BeginDeferredActorSpawnFromClass',args=(world,icls,transform,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
 gs.call_method('FinishSpawningActor',args=(item,transform,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
 item.set_actor_enable_collision(False)
 setp(player,'HeldActor',item)
 for typ,required in [('鱼',3),('洋葱',3),('欧芹',2),('Fish',3),('Onion',3),('Parsley',2)]:
  setp(item,'Type',typ);setp(item,'State','Washed');setp(item,'bWashed',True);setp(item,'CutCount',0)
  counts=[];states=[]
  for i in range(required+1):
   chop.call_method('Interact');counts.append(item.get_editor_property('CutCount'));states.append(item.get_editor_property('State'))
  check('cuts '+typ,counts==list(range(1,required+1))+[required] and states[-1]=='Cut' and all(s=='Washed' for s in states[:required-1]),{'counts':counts,'states':states})
 setp(item,'Type','鱼');setp(item,'State','Raw');setp(item,'bWashed',False);setp(item,'CutCount',0);chop.call_method('Interact')
 check('raw fish rejected',item.get_editor_property('CutCount')==0,item.get_editor_property('State'))
 setp(item,'Type','面团');setp(item,'State','Raw');chop.call_method('Interact');check('dough cannot chop',item.get_editor_property('CutCount')==0,'CutCount='+str(item.get_editor_property('CutCount')))
 setp(player,'HeldActor',None);chop.call_method('Interact');check('empty hand rejected',item.get_editor_property('CutCount')==0,'no mutation');setp(player,'HeldActor',item)
 out['roll_defaults']={n:roll.get_editor_property(n) for n in ['ProgressRate','AcceptMin','AcceptMax','PerfectMin','PerfectMax','MaxUseDistance']}
 for progress,quality,state in [(0.,'Failed','RollFailed'),(49.,'Failed','RollFailed'),(50.,'Normal','PieBase'),(64.,'Normal','PieBase'),(65.,'Perfect','PieBase'),(70.,'Perfect','PieBase'),(75.,'Perfect','PieBase'),(76.,'Normal','PieBase'),(90.,'Normal','PieBase'),(91.,'Failed','RollFailed'),(100.,'Failed','RollFailed')]:
  setp(item,'Type','面团');setp(item,'State','Raw');setp(item,'RollProgress',0.);setp(item,'RollQuality','')
  roll.call_method('BeginRolling');setp(item,'RollProgress',progress);roll.call_method('FinishRolling')
  got={'state':item.get_editor_property('State'),'quality':item.get_editor_property('RollQuality'),'running':roll.get_editor_property('bRolling')}
  check('release '+str(progress),got['state']==state and got['quality']==quality and not got['running'],got)
 # Leave one active session for an actual tick-time progression check.
 setp(item,'State','Raw');setp(item,'Type','Dough');setp(item,'RollProgress',0.);roll.call_method('BeginRolling')
 out['active']={'item':item.get_name(),'running':roll.get_editor_property('bRolling'),'widget':str(roll.get_editor_property('ProgressWidget'))}
except Exception:out['error']=traceback.format_exc()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/processing_runtime_tests.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
