import unreal,json,traceback
# Load the shared graph utilities without executing the builder.
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read()
exec(src.split('\ntry:\n')[0],globals())
try:
 char=EAL.load_asset(CHAR);roll=EAL.load_asset(ROOT+'BP_RollingStation');chop=EAL.load_asset(ROOT+'BP_ChoppingBoard')
 variable(char,'ActiveRollingStation','object',roll.generated_class());assert BEL.compile_blueprint(char)
 g=G(char,'EventGraph');ns={n.get_name():n for n in g.ed.list_all_nodes()}
 existing=[n for n in g.ed.list_all_nodes() if n.get_class().get_name()=='K2Node_InputKey' and '鼠标左键' in str(n.get_node_title())]
 if existing:raise RuntimeError('Left mouse event already exists; not duplicating')
 key=g.menu('输入|MouseEvents|鼠标左键')
 trace=g.call('/Script/Engine.KismetSystemLibrary:LineTraceSingle')
 old=ns['K2Node_CallFunction_14']
 for name in ['Start','End','TraceChannel','bTraceComplex','ActorsToIgnore','DrawDebugType','bIgnoreSelf','TraceColor','TraceHitColor','DrawTime']:
  try:
   source=p(old,name);dest=p(trace,name)
   links=list(source.list_connected_pins())
   if links:
    for pin in links:assert pin.try_create_connection(dest)
   elif source.get_pin_value():dest.set_pin_value(str(source.get_pin_value()))
  except Exception:
   if name in ['Start','End']:raise
 link(key,'Pressed',trace,'execute')
 hit=g.call('/Script/Engine.GameplayStatics:BreakHitResult');link(trace,'OutHit',hit,'Hit')
 b=g.branch((trace,'then'),(trace,'ReturnValue'))
 c=g.cast((b,'then'),(hit,'HitActor'),chop.generated_class())
 call=g.call(chop.generated_class().get_path_name()+':Interact');link(c,'then',call,'execute');link(c,outcast(c),call,'self')
 r=g.cast((c,'CastFailed'),(hit,'HitActor'),roll.generated_class())
 ex=g.setexec((r,'then'),'ActiveRollingStation',(r,outcast(r)))
 begin=g.call(roll.generated_class().get_path_name()+':BeginRolling');link(*ex,begin,'execute');link(r,outcast(r),begin,'self')
 active=g.get('ActiveRollingStation');b=g.branch((key,'Released'),g.valid((active,'ActiveRollingStation')))
 finish=g.call(roll.generated_class().get_path_name()+':FinishRolling');link(b,'then',finish,'execute');link(active,'ActiveRollingStation',finish,'self');g.setexec((finish,'then'),'ActiveRollingStation')
 # E remains interaction and gives instructions at processing stations; left click performs the work.
 work=ns['K2Node_DynamicCast_1'];p(work,'then').break_pin_links()
 c=g.cast((work,'then'),(work,outcast(work)),chop.generated_class());g.msg((c,'then'),'手持已清洗的鱼、洋葱或欧芹，对准案板点击左键切配')
 r=g.cast((c,'CastFailed'),(work,outcast(work)),roll.generated_class());g.msg((r,'then'),'手持原始面团，对准擀面台按住左键；松开结算')
 link(r,'CastFailed',ns['K2Node_CallFunction_76'],'execute')
 save(char)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'error':traceback.format_exc()},ensure_ascii=False))
