import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 bp=EAL.load_asset(ROOT+'BP_Workstation');g=G(bp,'EventGraph');out={}
 for path in ['/Script/Engine.Actor:GetActorBounds','/Script/Engine.Actor:K2_AttachToComponent','/Script/Engine.Actor:K2_SetActorLocation','/Script/Engine.Actor:K2_SetActorRelativeLocation','/Script/Engine.Actor:K2_DetachFromActor','/Script/Engine.KismetMathLibrary:BreakVector','/Script/Engine.KismetMathLibrary:MakeVector','/Script/Engine.Actor:GetComponentByClass']:
  n=g.call(path);out[path]=[str(p.get_pin_name()) for p in n.list_all_pins()];g.ed.remove_nodes([n])
 unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'error':traceback.format_exc()},ensure_ascii=False))
