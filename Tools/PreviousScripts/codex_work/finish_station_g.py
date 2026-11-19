import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 char=EAL.load_asset(CHAR);g=G(char,'EventGraph');ns={n.get_name():n for n in g.ed.list_all_nodes()};drop=ns['K2Node_CallFunction_106'];p(drop,'execute').break_pin_links()
 # Empty space and non-workstations should never dump food on the floor.
 trace=next(n for n in g.ed.list_all_nodes() if str(n.get_node_title())=='Line Trace By Channel' and any(q.get_owning_node().get_name()=='K2Node_InputKey_4' for q in p(n,'execute').list_connected_pins()))
 br=p(trace,'then').list_connected_pins()[0].get_owning_node();g.msg((br,'else'),'请对准水槽、切配台或擀面台按 G 放入')
 cast=next(q.get_owning_node() for q in p(br,'then').list_connected_pins());g.msg((cast,'CastFailed'),'请对准水槽、切配台或擀面台按 G 放入')
 save(char);unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'error':traceback.format_exc()},ensure_ascii=False))
