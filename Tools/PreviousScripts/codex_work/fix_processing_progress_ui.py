import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read()
exec(src.split('\ntry:\n')[0],globals())
try:
 roll=EAL.load_asset(ROOT+'BP_RollingStation');ingredient=EAL.load_asset(ROOT+'BP_Ingredient');widget=EAL.load_asset(ROOT+'WBP_RollingProgress')
 # Enlarge the background to include a readable numeric value.
 H.umg_set_slot_layout(widget,'Backdrop',.5,.68,.5,.68,-300,0,600,140)
 H.umg_set_slot_layout(widget,'HelpText',.5,.68,.5,.68,-280,12,560,50)
 H.umg_set_slot_layout(widget,'RollBar',.5,.68,.5,.68,-280,68,560,22)
 if not H.umg_find_widget(widget,'ValueText'):
  assert json.loads(H.umg_add_widget(widget,'TextBlock','ValueText','Root')).get('success')
 H.umg_set_slot_layout(widget,'ValueText',.5,.68,.5,.68,-280,98,560,30)
 H.umg_set_text_style(widget,'ValueText',18,1,1,1,1,1)
 H.umg_set_widget_is_variable(widget,'ValueText',True)
 H.umg_find_widget(widget,'ValueText').set_editor_property('text',unreal.Text('0 / 100'))
 save(widget)
 g=G(roll,'EventGraph');g.i=60
 nodes=g.ed.list_all_nodes()
 percent=next(n for n in nodes if any(str(pn.get_pin_name())=='B' and str(pn.get_pin_value())=='100.0' for pn in n.list_all_pins()) and 'Divide' in str(n.get_node_title())) if False else None
 # Locate the Percent input from SetPercent, then reconnect its numerator to stored RollProgress.
 setpct=next(n for n in nodes if any(str(pn.get_pin_name())=='InPercent' for pn in n.list_all_pins()))
 divide=p(setpct,'InPercent').list_connected_pins()[0].get_owning_node()
 stored=g.get('RollProgress',ingredient.generated_class().get_path_name());target=g.get('RollTarget');link(target,'RollTarget',stored,'self')
 link(stored,'RollProgress',divide,'A')
 wg=g.get('ProgressWidget');textget=g.get('ValueText',widget.generated_class().get_path_name());link(wg,'ProgressWidget',textget,'self')
 roundn=g.call('/Script/Engine.KismetMathLibrary:Round');link(stored,'RollProgress',roundn,'A')
 fmt=g.call('/Script/Engine.KismetStringLibrary:BuildString_Int');val(fmt,'Suffix',' / 100');link(roundn,'ReturnValue',fmt,'InInt')
 textn=g.call('/Script/Engine.KismetTextLibrary:Conv_StringToText');link(fmt,'ReturnValue',textn,'InString')
 settext=g.call('/Script/UMG.TextBlock:SetText');link(setpct,'then',settext,'execute');link(textget,'ValueText',settext,'self');link(textn,'ReturnValue',settext,'InText')
 save(roll)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'error':traceback.format_exc()},ensure_ascii=False))
