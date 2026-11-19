import unreal,json,traceback,time
world=unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
player=unreal.GameplayStatics.get_player_character(world,0)
sys=unreal.get_default_object(unreal.SystemLibrary)
actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
roll=next(a for a in actors if a.get_class().get_name()=='BP_RollingStation_C')
item=roll.get_editor_property('RollTarget')
def setp(o,n,v):
 typ='Bool' if isinstance(v,bool) else 'Int' if isinstance(v,int) else 'Double' if isinstance(v,float) else 'String' if isinstance(v,str) else 'Object'
 sys.call_method('Set'+typ+'PropertyByName',args=(o,n,v))
def reset():
 roll.call_method('CancelRolling')
 item.set_actor_location(roll.get_actor_location()+unreal.Vector(0,0,120),False,True)
 for c in item.get_components_by_class(unreal.PrimitiveComponent):c.set_simulate_physics(False)
 setp(item,'Type','Dough');setp(item,'State','Raw');setp(item,'RollProgress',0.);setp(player,'HeldActor',item)
 roll.call_method('BeginRolling')
out={'checks':[]}
def check(n,b,d):out['checks'].append({'test':n,'pass':bool(b),'details':d})
reset()
start=unreal.GameplayStatics.get_time_seconds(world)
phase=0
wall=time.monotonic()
def done():
 unreal.unregister_slate_post_tick_callback(handle)
 roll.call_method('CancelRolling')
 with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/processing_timed_tests.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
def tick(dt):
 global phase,start
 try:
  elapsed=unreal.GameplayStatics.get_time_seconds(world)-start
  if time.monotonic()-wall>30:raise RuntimeError('Timed checks exceeded 30 wall seconds')
  if phase==0 and elapsed>=1:
   progress=item.get_editor_property('RollProgress');widget=roll.get_editor_property('ProgressWidget');pct=widget.get_editor_property('RollBar').get_editor_property('percent')
   check('real tick advances at configured rate',abs(progress-elapsed*roll.get_editor_property('ProgressRate'))<2,{'elapsed':elapsed,'progress':progress,'rate':roll.get_editor_property('ProgressRate')})
   check('UI shows stored progress',abs(pct-progress/100)<0.0001,{'bar':pct,'stored':progress/100})
   setp(player,'HeldActor',None);phase=1;start=unreal.GameplayStatics.get_time_seconds(world)
  elif phase==1 and elapsed>.15:
   check('changing held item cancels',not roll.get_editor_property('bRolling') and item.get_editor_property('RollProgress')==0,{'running':roll.get_editor_property('bRolling'),'progress':item.get_editor_property('RollProgress')})
   check('cancel removes UI',not roll.get_editor_property('ProgressWidget').is_in_viewport(),'widget detached')
   reset();item.set_actor_location(roll.get_actor_location()+unreal.Vector(1000,0,120),False,True);phase=2;start=unreal.GameplayStatics.get_time_seconds(world)
  elif phase==2 and elapsed>.15:
   check('leaving station cancels',not roll.get_editor_property('bRolling') and item.get_editor_property('State')=='Raw',item.get_editor_property('State'))
   reset();setp(item,'RollProgress',70.);roll.call_method('FinishRolling');roll.call_method('FinishRolling');roll.call_method('BeginRolling')
   check('finished dough cannot be processed again',item.get_editor_property('State')=='PieBase' and item.get_editor_property('RollQuality')=='Perfect' and not roll.get_editor_property('bRolling'),'PieBase Perfect retained')
   reset();setp(item,'RollProgress',1.);roll.call_method('FinishRolling');roll.call_method('BeginRolling')
   check('failed dough requires replacement',item.get_editor_property('State')=='RollFailed' and not roll.get_editor_property('bRolling'),item.get_editor_property('State'))
   done()
 except Exception:
  out['error']=traceback.format_exc();done()
handle=unreal.register_slate_post_tick_callback(tick)
unreal.MCPythonHelper.submit_result(json.dumps({'started':True}))
