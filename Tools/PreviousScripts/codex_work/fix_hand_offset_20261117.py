import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 char=EAL.load_asset(CHAR);g=G(char,'EventGraph');ns={n.get_name():n for n in g.ed.list_all_nodes()}
 total=g.call('/Script/Engine.KismetMathLibrary:Add_VectorVector');link(ns['K2Node_CallFunction_25'],'ReturnValue',total,'A');link(ns['K2Node_VariableGet_39'],'HeldOffset',total,'B');link(total,'ReturnValue',ns['K2Node_CallFunction_103'],'NewRelativeLocation');save(char)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'error':traceback.format_exc()},ensure_ascii=False))
