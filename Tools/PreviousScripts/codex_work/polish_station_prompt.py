import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 base=EAL.load_asset(ROOT+'BP_Workstation');g=G(base,'PlaceStationItem');nodes=g.ed.list_all_nodes()
 station_bounds=next(n for n in nodes if any(str(x.get_pin_name())=='BoxExtent' for x in n.list_all_pins()));station_break=p(station_bounds,'BoxExtent').list_connected_pins()[0].get_owning_node();height=p(station_break,'Z').list_connected_pins()[0].get_owning_node()
 itemget=next(n for n in nodes if str(n.get_node_title())=='Get StationItem' and p(n,'StationItem').list_connected_pins()) if False else None
 # Use the item stored in the station to account for its actual mesh height.
 item=g.get('StationItem');bounds=g.call('/Script/Engine.Actor:GetActorBounds');link(item,'StationItem',bounds,'self');br=g.call('/Script/Engine.KismetMathLibrary:BreakVector');link(bounds,'BoxExtent',br,'InVec');pad=g.op('Add_DoubleDouble',(br,'Z'),2);link(*pad,height,'B');save(base)
 for name,label in [('BP_ChoppingBoard','切配台：G 放入，左键切配，E 取回'),('BP_RollingStation','擀面台：G 放入，按住左键擀面，E 取回'),('BP_Sink','水槽：G 放入，E 开关水或取回')]:
  bp=EAL.load_asset(ROOT+name);g=G(bp,'EventGraph');nodes={n.get_name():n for n in g.ed.list_all_nodes()};parent=nodes['K2Node_CallParentFunction_0'];ex=g.setexec((parent,'then'),'PromptLabel',label);save(bp)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'partial':report,'error':traceback.format_exc()},ensure_ascii=False))

