import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read()
exec(src.split('\ntry:\n')[0],globals())
try:
 roll=EAL.load_asset(ROOT+'BP_RollingStation');ingredient=EAL.load_asset(ROOT+'BP_Ingredient');widget=EAL.load_asset(ROOT+'WBP_RollingProgress')
 H.umg_find_widget(widget,'HelpText').set_editor_property('text',unreal.Text('按住左键擀面，松开结算\n金色可用 · 绿色完美 · 红色失败'))
 H.umg_find_widget(widget,'RollBar').set_editor_property('fill_color_and_opacity',unreal.LinearColor(.85,.12,.1,1))
 save(widget)
 g=G(roll,'EventGraph');g.i=72
 target=g.get('RollTarget');pr=g.get('RollProgress',ingredient.generated_class().get_path_name());link(target,'RollTarget',pr,'self')
 def inrange(lo,hi):
  l=g.get(lo);h=g.get(hi)
  return g.op('BooleanAND',g.op('GreaterEqual_DoubleDouble',(pr,'RollProgress'),(l,lo)),g.op('LessEqual_DoubleDouble',(pr,'RollProgress'),(h,hi)))
 perfect=inrange('PerfectMin','PerfectMax');valid=inrange('AcceptMin','AcceptMax')
 color=g.call('/Script/Engine.KismetMathLibrary:SelectColor');val(color,'A','(R=0.1,G=0.85,B=0.3,A=1.0)');val(color,'B','(R=0.95,G=0.65,B=0.15,A=1.0)');link(*perfect,color,'bPickA')
 final=g.call('/Script/Engine.KismetMathLibrary:SelectColor');link(color,'ReturnValue',final,'A');val(final,'B','(R=0.85,G=0.12,B=0.1,A=1.0)');link(*valid,final,'bPickA')
 textset=next(n for n in g.ed.list_all_nodes() if any(str(x.get_pin_name())=='InText' for x in n.list_all_pins()))
 wg=g.get('ProgressWidget');bar=g.get('RollBar',widget.generated_class().get_path_name());link(wg,'ProgressWidget',bar,'self')
 setcolor=g.call('/Script/UMG.ProgressBar:SetFillColorAndOpacity');link(textset,'then',setcolor,'execute');link(bar,'RollBar',setcolor,'self');link(final,'ReturnValue',setcolor,'InColor')
 save(roll)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'error':traceback.format_exc()},ensure_ascii=False))
