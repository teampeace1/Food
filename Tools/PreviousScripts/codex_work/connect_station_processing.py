import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 base=EAL.load_asset(ROOT+'BP_Workstation');chop=EAL.load_asset(ROOT+'BP_ChoppingBoard');sink=EAL.load_asset(ROOT+'BP_Sink');roll=EAL.load_asset(ROOT+'BP_RollingStation');char=EAL.load_asset(CHAR)
 for bp,graph,oldid in [(chop,'Interact','K2Node_VariableGet_0'),(sink,'Interact','K2Node_VariableGet_2'),(roll,'BeginRolling','K2Node_VariableGet_5'),(roll,'StartRolling','K2Node_VariableGet_0'),(roll,'EventGraph','K2Node_VariableGet_14')]:
  g=G(bp,graph);nodes={n.get_name():n for n in g.ed.list_all_nodes()};old=p(nodes[oldid],'HeldActor');consumers=list(old.list_connected_pins());old.break_pin_links();fresh=g.get('StationItem')
  for target in consumers:assert p(fresh,'StationItem').try_create_connection(target)
 # When washing finishes, stop the water and retain the item until E takes it back.
 g=G(sink,'EventGraph');ns={n.get_name():n for n in g.ed.list_all_nodes()};refresh=ns['K2Node_CallFunction_10'];msg=ns['K2Node_CallFunction_9'];p(refresh,'then').break_pin_links();stop=g.call(sink.generated_class().get_path_name()+':Interact');link(refresh,'then',stop,'execute');link(stop,'then',msg,'execute');val(msg,'InString','洗好了，按 E 取回')
 # On E, a washed, stationary item is retrieved. Otherwise use the existing sink on/off operation.
 g=G(sink,'Interact');ns={n.get_name():n for n in g.ed.list_all_nodes()};entry=g.entry;old=ns['K2Node_IfThenElse_0'];p(entry,'then').break_pin_links();item=g.get('StationItem');has=g.branch((entry,'then'),g.valid((item,'StationItem')));link(has,'else',old,'execute')
 washed=g.get('bWashed',EAL.load_asset(ROOT+'BP_Ingredient').generated_class().get_path_name());link(item,'StationItem',washed,'self');b=g.branch((has,'then'),(washed,'bWashed'));link(b,'else',old,'execute')
 running=g.get('bRunning');b2=g.branch((b,'then'),(running,'bRunning'));link(b2,'then',old,'execute');take=g.call(base.generated_class().get_path_name()+':TakeStationItem');link(b2,'else',take,'execute')
 # Retarget completion text used for instructions.
 g=G(chop,'Interact');ns={n.get_name():n for n in g.ed.list_all_nodes()};
 for n in ns.values():
  for pin in n.list_all_pins():
   if str(pin.get_pin_name())=='InString' and '手上' in str(pin.get_pin_value()):pin.set_pin_value('请先按 G 将食材放在案板上')
 save(chop);save(sink);save(roll)
 # G traces from the same camera ray as E; workstations receive the placed item.
 g=G(char,'EventGraph');g.i=100;ns={n.get_name():n for n in g.ed.list_all_nodes()};key=ns['K2Node_InputKey_4'];drop=ns['K2Node_CallFunction_106'];old=ns['K2Node_CallFunction_14'];p(key,'Pressed').break_pin_links()
 trace=g.call('/Script/Engine.KismetSystemLibrary:LineTraceSingle')
 for name in ['Start','End','TraceChannel','bTraceComplex','ActorsToIgnore','DrawDebugType','bIgnoreSelf','TraceColor','TraceHitColor','DrawTime']:
  source=p(old,name);dest=p(trace,name);links=list(source.list_connected_pins())
  if links:
   for pin in links:assert pin.try_create_connection(dest)
  elif source.get_pin_value():dest.set_pin_value(str(source.get_pin_value()))
 link(key,'Pressed',trace,'execute');hit=g.call('/Script/Engine.GameplayStatics:BreakHitResult');link(trace,'OutHit',hit,'Hit');b=g.branch((trace,'then'),(trace,'ReturnValue'));link(b,'else',drop,'execute')
 c=g.cast((b,'then'),(hit,'HitActor'),base.generated_class());link(c,'CastFailed',drop,'execute');put=g.call(base.generated_class().get_path_name()+':PlaceStationItem');link(c,'then',put,'execute');link(c,outcast(c),put,'self')
 # E on chop or rolling station takes the item, or gives instructions if empty.
 for castid in ['K2Node_DynamicCast_4','K2Node_DynamicCast_5']:
  c=ns[castid];p(c,'then').break_pin_links();item=g.get('StationItem',base.generated_class().get_path_name());link(c,outcast(c),item,'self');b=g.branch((c,'then'),g.valid((item,'StationItem')))
  take=g.call(base.generated_class().get_path_name()+':TakeStationItem');link(b,'then',take,'execute');link(c,outcast(c),take,'self');g.msg((b,'else'),'手持食材对准工作台按 G 放入')
 save(char)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'partial':report,'error':traceback.format_exc()},ensure_ascii=False))

