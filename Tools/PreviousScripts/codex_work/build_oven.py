import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 parent=EAL.load_asset(ROOT+'BP_Workstation');pie=EAL.load_asset(ROOT+'BP_Pie');char=EAL.load_asset(CHAR)
 oven=EAL.load_asset(ROOT+'BP_Oven')
 if not oven:
  f=unreal.BlueprintFactory();f.set_editor_property('parent_class',parent.generated_class())
  oven=unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_Oven',ROOT.rstrip('/'),unreal.Blueprint,f)
  print(H.add_component_to_blueprint(oven,'/Script/Engine.StaticMeshComponent','OvenMesh',0,0,90,0,0,0,''))
  print(H.set_component_property(oven,'OvenMesh','static_mesh','/Engine/BasicShapes/Cube.Cube'))
  print(H.set_component_property(oven,'OvenMesh','relative_scale3d','(X=1.5,Y=1.5,Z=1.8)'))
 for n,k,c in [('PieRef','object',pie.generated_class()),('Heat','int',None),('BakeElapsed','double',None),('bIsBaking','bool',None),('bFinished','bool',None),('BakeQuality','string',None)]:variable(oven,n,k,c)
 BEL.set_blueprint_variable_instance_editable(oven,'PieRef',True)
 for fn in ['CycleHeat','OnPieFinished']:
  if not BEL.find_graph(oven,fn):BEL.add_function_graph(oven,fn)
 assert BEL.compile_blueprint(oven)
 cdo=unreal.get_default_object(oven.generated_class());cdo.set_editor_property('Heat',1)
 # Left click cycles temperature before baking.
 g=G(oven,'CycleHeat',True);b=g.branch((g.entry,'then'),(g.get('bIsBaking'),'bIsBaking'));g.msg((b,'then'),'正在烘烤，请按 E 取出')
 heat=g.get('Heat');n=g.op('Add_IntInt',(heat,'Heat'),1);mod=g.op('Percent_IntInt',n,3);ex=g.setexec((b,'else'),'Heat',mod)
 for i,label in [(0,'低温：目标 30 秒'),(1,'中温：目标 20 秒'),(2,'高温：目标 10 秒')]:
  h=g.get('Heat');eq=g.op('EqualEqual_IntInt',(h,'Heat'),i);br=g.branch(ex,eq);g.msg((br,'then'),label+'；按 E 开始')
 # Override workstation interaction.
 graph=BEL.find_graph(oven,'Interact') or BEL.add_function_override(oven,'Interact');g=G(oven,'Interact',True)
 finished=g.get('bFinished');b=g.branch((g.entry,'then'),(finished,'bFinished'));g.msg((b,'then'),'料理已完成')
 run=g.get('bIsBaking');b=g.branch((b,'else'),(run,'bIsBaking'))
 # Taking out judges elapsed as a fraction of heat-specific target.
 ex=g.setexec((b,'then'),'bIsBaking','false');h=g.get('Heat');sel=g.call('/Script/Engine.KismetMathLibrary:SelectFloat');eq=g.op('EqualEqual_IntInt',(h,'Heat'),0);val(sel,'A',30);val(sel,'B',20);link(*eq,sel,'bPickA')
 sel2=g.call('/Script/Engine.KismetMathLibrary:SelectFloat');eq2=g.op('EqualEqual_IntInt',(h,'Heat'),2);val(sel2,'A',10);link(sel,'ReturnValue',sel2,'B');link(*eq2,sel2,'bPickA')
 elapsed=g.get('BakeElapsed');ratio=g.op('Divide_DoubleDouble',(elapsed,'BakeElapsed'),(sel2,'ReturnValue'))
 lower=g.op('GreaterEqual_DoubleDouble',ratio,.8);upper=g.op('LessEqual_DoubleDouble',ratio,1.2);ok=g.op('BooleanAND',lower,upper);judge=g.branch(ex,ok)
 ex=g.setexec((judge,'then'),'BakeQuality','Success');ex=g.setexec(ex,'bFinished','true');ex=g.owncall(ex,'OnPieFinished');g.msg(ex,'派烤好了！料理完成')
 ex=g.setexec((judge,'else'),'BakeQuality','Failed');g.msg(ex,'火候不合适，请重新开始烘烤')
 # Start only when a fully assembled pie is present.
 ref=g.get('PieRef');b2=g.branch((b,'else'),g.valid((ref,'PieRef')));g.msg((b2,'else'),'烤箱未连接派，请检查场景')
 ready=g.get('bReadyToBake',pie.generated_class().get_path_name());link(ref,'PieRef',ready,'self');b3=g.branch((b2,'then'),(ready,'bReadyToBake'));g.msg((b3,'else'),'请先完成馅料、派底和七个鱼头')
 ex=g.setexec((b3,'then'),'BakeElapsed',0);ex=g.setexec(ex,'bIsBaking','true');g.msg(ex,'烘烤开始，按 E 取出；暂停时计时停止')
 g=G(oven,'OnPieFinished',True);g.msg((g.entry,'then'),'完成：仰望星空派')
 # Actor Tick naturally stops while the world is paused.
 ev=G(oven,'EventGraph');tick=next((n for n in ev.ed.list_all_nodes() if 'Event Tick' in str(n.get_node_title()) or '事件 Tick' in str(n.get_node_title())),None)
 if not tick:tick=ev.menu('添加事件|事件 Tick')
 run=ev.get('bIsBaking');br=ev.branch((tick,'then'),(run,'bIsBaking'));elapsed=ev.get('BakeElapsed');s=ev.op('Add_DoubleDouble',(elapsed,'BakeElapsed'),(tick,'DeltaSeconds'));ev.setexec((br,'then'),'BakeElapsed',s)
 save(oven);unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'partial':report,'error':traceback.format_exc()},ensure_ascii=False))
