import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 char=EAL.load_asset(CHAR);pie=EAL.load_asset(ROOT+'BP_Pie');bowl=EAL.load_asset(ROOT+'BP_FillingBowl')
 if not BEL.find_graph(char,'ClearHeldTraySlot'):BEL.add_function_graph(char,'ClearHeldTraySlot')
 assert BEL.compile_blueprint(char)
 g=G(char,'ClearHeldTraySlot',True);held=g.get('HeldActor');valid=g.branch((g.entry,'then'),g.valid((held,'HeldActor')));ex=(valid,'then')
 for i in (1,2,3):
  slot=g.get('TraySlot'+str(i));same=g.op('EqualEqual_ObjectObject',(held,'HeldActor'),(slot,'TraySlot'+str(i)));b=g.branch(ex,same)
  yes=g.setexec((b,'then'),'TraySlot'+str(i));yes=g.setexec(yes,'TraySlot'+str(i)+'Component')
  # A held actor can belong to only one slot. Branches continue only when no match was found.
  ex=(b,'else')
 save(char)
 # Drop: remove the slot reference while HeldActor is still valid.
 g=G(char,'DropHeldItem');ns={n.get_name():n for n in g.ed.list_all_nodes()};br=ns['K2Node_IfThenElse_0'];detach=ns['K2Node_CallFunction_4'];p(br,'then').break_pin_links();clear=g.call(char.generated_class().get_path_name()+':ClearHeldTraySlot');link(br,'then',clear,'execute');link(clear,'then',detach,'execute');save(char)
 # Consume paths: invoke the same operation before destroying the held item.
 for bp,graph,fromid,frompin,toid in [(bowl,'ConsumeHeld','K2Node_FunctionEntry_0','then','K2Node_CallFunction_0'),(pie,'PlaceHead','K2Node_IfThenElse_0','then','K2Node_CallFunction_21')]:
  g=G(bp,graph);ns={n.get_name():n for n in g.ed.list_all_nodes()};start=ns[fromid];dest=ns[toid];p(start,frompin).break_pin_links()
  pc=g.call('/Script/Engine.GameplayStatics:GetPlayerCharacter');cast=g.cast((start,frompin),(pc,'ReturnValue'),char.generated_class())
  call=g.call(char.generated_class().get_path_name()+':ClearHeldTraySlot');link(cast,'then',call,'execute');link(cast,outcast(cast),call,'self');link(call,'then',dest,'execute');link(cast,'CastFailed',dest,'execute')
  save(bp)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'partial':report,'error':traceback.format_exc()},ensure_ascii=False))
