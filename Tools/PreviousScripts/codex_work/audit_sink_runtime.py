import unreal,json,time,traceback
w=unreal.EditorLevelLibrary.get_pie_worlds(False)[0];p=unreal.GameplayStatics.get_player_character(w,0);s=unreal.get_default_object(unreal.SystemLibrary)
actors=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor);sink=next(a for a in actors if a.get_class().get_name()=='BP_Sink_C');item=next(a for a in actors if a.get_name()=='BP_Ingredient_C_1')
def setp(o,n,v):
 typ='Bool' if isinstance(v,bool) else 'Double' if isinstance(v,float) else 'String' if isinstance(v,str) else 'Object';s.call_method('Set'+typ+'PropertyByName',args=(o,n,v))
setp(p,'HeldActor',item);setp(item,'Type','鱼');setp(item,'State','Raw');setp(item,'bWashable',True);setp(item,'bWashed',False);setp(item,'WashProgress',0.)
sink.call_method('Interact');out={'start':{'running':sink.get_editor_property('bRunning'),'state':item.get_editor_property('State')}};start=unreal.GameplayStatics.get_time_seconds(w)
def tick(dt):
 if unreal.GameplayStatics.get_time_seconds(w)-start<6:return
 try:
  out['after']={'running':sink.get_editor_property('bRunning'),'state':item.get_editor_property('State'),'wash':item.get_editor_property('WashProgress'),'washed':item.get_editor_property('bWashed')};sink.call_method('Interact');out['closed']=not sink.get_editor_property('bRunning')
 except Exception:out['error']=traceback.format_exc()
 with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/current_sink_test.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
 unreal.unregister_slate_post_tick_callback(handle)
handle=unreal.register_slate_post_tick_callback(tick)
unreal.MCPythonHelper.submit_result(json.dumps({'started':True}))
