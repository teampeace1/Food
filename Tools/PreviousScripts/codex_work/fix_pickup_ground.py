import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 char=EAL.load_asset(CHAR);g=G(char,'EventGraph');g.i=80;ns={n.get_name():n for n in g.ed.list_all_nodes()};branch=ns['K2Node_IfThenElse_31'];pickup=ns['K2Node_CallFunction_99']
 p(branch,'else').break_pin_links();holding=g.get('bIsHolding');link(holding,'bIsHolding',branch,'Condition');g.msg((branch,'then'),'请先按 G 放下手里的食材')
 ex=(branch,'else')
 for i in (1,2,3):
  slot=g.get('TraySlot'+str(i));b=g.branch(ex,g.valid((slot,'TraySlot'+str(i))));setslot=g.set('SelectedSlot');link(b,'else',setslot,'execute');val(setslot,'SelectedSlot',i);link(setslot,'then',pickup,'execute');ex=(b,'then')
 g.msg(ex,'托盘已满，请先按 G 放下食材')
 link(ns['K2Node_VariableSet_52'],'then',ns['K2Node_IfThenElse_3'],'execute')
 save(char);unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'error':traceback.format_exc()},ensure_ascii=False))
