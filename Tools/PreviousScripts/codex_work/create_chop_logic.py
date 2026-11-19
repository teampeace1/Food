import unreal,json,traceback
out={}
try:
 bel=unreal.BlueprintEditorLibrary
 ingredient=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_Ingredient')
 if 'CutCount' not in [str(x) for x in bel.list_member_variable_names(ingredient)]:
  assert bel.add_member_variable(ingredient,'CutCount',bel.get_basic_type_by_name('int'))
  assert bel.compile_blueprint(ingredient)
  assert unreal.EditorAssetLibrary.save_asset('/Game/FoodGameplay/BP_Ingredient',only_if_is_dirty=False)
 path='/Game/FoodGameplay/BP_ChoppingBoard_Test'
 if unreal.EditorAssetLibrary.does_asset_exist(path):raise RuntimeError('test asset exists')
 assert unreal.EditorAssetLibrary.duplicate_asset('/Game/FoodGameplay/BP_Sink',path)
 bp=unreal.EditorAssetLibrary.load_asset(path)
 graph=bel.find_graph(bp,'Interact'); ed=unreal.BlueprintGraphEditor.get_graph_editor(graph)
 ns={n.get_name():n for n in ed.list_all_nodes()}
 def pin(n,k):return next(p for p in n.list_all_pins() if str(p.get_pin_name())==k)
 def connect(a,ap,b,bp):
  if not pin(a,ap).try_create_connection(pin(b,bp)):raise RuntimeError('connection '+ap+' '+bp)
 def setval(n,p,v):
  if not pin(n,p).set_pin_value(str(v)):raise RuntimeError('value '+p)
 # Reuse the sink's existing player and ingredient casts, disconnect the sink-specific paths.
 entry=ns['K2Node_FunctionEntry_0']; pc=ns['K2Node_DynamicCast_1']; item=ns['K2Node_DynamicCast_2']
 pin(entry,'then').break_pin_links(); connect(entry,'then',pc,'execute')
 pin(item,'then').break_pin_links()
 for n in list(ed.list_all_nodes()):
  if n.get_name() not in ['K2Node_FunctionEntry_0','K2Node_CallFunction_4','K2Node_DynamicCast_1','K2Node_VariableGet_2','K2Node_CallFunction_5','K2Node_IfThenElse_1','K2Node_CallFunction_6','K2Node_DynamicCast_2']:
   ed.remove_nodes([n])
 cls=ingredient.generated_class().get_path_name()
 state=ed.add_get_member_variable_node('State',cls); typ=ed.add_get_member_variable_node('Type',cls)
 count=ed.add_get_member_variable_node('CutCount',cls)
 for n in (state,typ,count):connect(item,'AsBP Ingredient',n,'self')
 eq=ed.add_call_function_node('/Script/Engine.KismetStringLibrary:EqualEqual_StrStr')
 connect(state,'State',eq,'A');setval(eq,'B','Washed')
 branch=ed.add_branch_node();connect(item,'then',branch,'execute');connect(eq,'ReturnValue',branch,'Condition')
 msg=ed.create_node_from_name('开发|PrintString',unreal.Vector2D(1400,500),[]);setval(msg,'InString','请先清洗，或该食材已加工');connect(branch,'else',msg,'execute')
 # Check each accepted type and apply its required number of cuts.
 previous=(branch,'then')
 for i,(t,required) in enumerate([('Fish',3),('Onion',3),('Parsley',2)]):
  eqt=ed.add_call_function_node('/Script/Engine.KismetStringLibrary:EqualEqual_StrStr');connect(typ,'Type',eqt,'A');setval(eqt,'B',t)
  b=ed.add_branch_node();connect(previous[0],previous[1],b,'execute');connect(eqt,'ReturnValue',b,'Condition')
  add=ed.add_call_function_node('/Script/Engine.KismetMathLibrary:Add_IntInt');connect(count,'CutCount',add,'A');setval(add,'B','1')
  setter=ed.add_set_member_variable_node('CutCount',cls);connect(item,'AsBP Ingredient',setter,'self');connect(add,'ReturnValue',setter,'CutCount');connect(b,'then',setter,'execute')
  ge=ed.add_call_function_node('/Script/Engine.KismetMathLibrary:GreaterEqual_IntInt');connect(add,'ReturnValue',ge,'A');setval(ge,'B',str(required))
  done=ed.add_branch_node();connect(setter,'then',done,'execute');connect(ge,'ReturnValue',done,'Condition')
  state_set=ed.add_set_member_variable_node('State',cls);connect(item,'AsBP Ingredient',state_set,'self');setval(state_set,'State','Chopped');connect(done,'then',state_set,'execute')
  done_msg=ed.create_node_from_name('开发|PrintString',unreal.Vector2D(2000,i*300),[]);setval(done_msg,'InString','切配完成');connect(state_set,'then',done_msg,'execute')
  partial=ed.create_node_from_name('开发|PrintString',unreal.Vector2D(2300,i*300),[]);setval(partial,'InString',t+' 已切一刀');connect(done,'else',partial,'execute')
  previous=(b,'else')
 invalid=ed.create_node_from_name('开发|PrintString',unreal.Vector2D(2500,1000),[]);setval(invalid,'InString','该食材不能切配');connect(previous[0],previous[1],invalid,'execute')
 ok=bel.compile_blueprint(bp);errors=[str(x.get_node_title()) for x in ed.list_nodes_with_errors()]
 out={'compiled':ok,'errors':errors,'saved':unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=False) if ok and not errors else False}
except Exception as e:out={'error':repr(e),'trace':traceback.format_exc()}
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
