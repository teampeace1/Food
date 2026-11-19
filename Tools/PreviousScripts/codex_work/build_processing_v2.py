import unreal,json,traceback
BEL=unreal.BlueprintEditorLibrary
EAL=unreal.EditorAssetLibrary
H=unreal.MCPythonHelper
ROOT='/Game/FoodGameplay/'
CHAR='/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter'
report={}
def save(bp):
 ok=BEL.compile_blueprint(bp)
 errs=[]
 for g in BEL.list_graphs(bp):
  ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
  if ed:errs += [str(n.get_node_title()) for n in ed.list_nodes_with_errors()]
 if not ok or errs:raise RuntimeError('Compile '+bp.get_name()+str(errs))
 assert EAL.save_loaded_asset(bp,only_if_is_dirty=False)
 report[bp.get_name()]='compiled and saved'
def variable(bp,name,kind,cls=None):
 if name in [str(v) for v in BEL.list_member_variable_names(bp)]:return
 t=BEL.get_object_reference_type(cls) if cls else BEL.get_basic_type_by_name(kind)
 assert BEL.add_member_variable(bp,name,t),name
def p(n,k):
 v=next((v for v in n.list_all_pins() if str(v.get_pin_name())==k),None)
 if v is None:raise RuntimeError(n.get_name()+' missing '+k+' '+str([str(x.get_pin_name()) for x in n.list_all_pins()]))
 return v
def link(a,ap,b,bp):
 assert p(a,ap).try_create_connection(p(b,bp)),(a.get_name(),ap,b.get_name(),bp)
def val(n,k,v):assert p(n,k).set_pin_value(str(v)),(n.get_name(),k,v)
def outcast(n):return next(str(x.get_pin_name()) for x in n.list_all_pins() if str(x.get_pin_name()).startswith('As'))
class G:
 def __init__(self,bp,name,clear=False):
  self.bp=bp; self.g=BEL.find_graph(bp,name) or BEL.add_function_graph(bp,name)
  self.ed=unreal.BlueprintGraphEditor.get_graph_editor(self.g);self.i=0
  if clear:self.ed.remove_nodes([n for n in self.ed.list_all_nodes() if n.get_class().get_name()!='K2Node_FunctionEntry'])
  self.entry=next((n for n in self.ed.list_all_nodes() if n.get_class().get_name()=='K2Node_FunctionEntry'),None)
 def place(self,n):
  if not n:raise RuntimeError('Node creation failed in '+self.g.get_name())
  n.set_node_pos(unreal.IntPoint((self.i%8)*310,(self.i//8)*400));self.i+=1;return n
 def call(self,path):return self.place(self.ed.add_call_function_node(path))
 def menu(self,name):return self.place(self.ed.create_node_from_name(name,unreal.Vector2D(0,0),[]))
 def get(self,n,cls=''):return self.place(self.ed.add_get_member_variable_node(n,cls))
 def set(self,n,cls=''):return self.place(self.ed.add_set_member_variable_node(n,cls))
 def branch(self,prev,cond):
  n=self.place(self.ed.add_branch_node());link(*prev,n,'execute');link(*cond,n,'Condition');return n
 def cast(self,prev,obj,cls):
  n=self.menu('工具|Casting|CastToStaticMeshActor');assert self.ed.retarget_node_class(n,unreal.StaticMeshActor.static_class(),cls)
  link(*prev,n,'execute');link(*obj,n,'Object');return n
 def msg(self,prev,text):
  n=self.menu('开发|PrintString');val(n,'InString',text);val(n,'Duration',3);link(*prev,n,'execute');return n
 def valid(self,obj):
  n=self.call('/Script/Engine.KismetSystemLibrary:IsValid');link(*obj,n,'Object');return n,'ReturnValue'
 def eqstr(self,a,b):
  n=self.call('/Script/Engine.KismetStringLibrary:EqualEqual_StrStr');link(*a,n,'A');val(n,'B',b);return n,'ReturnValue'
 def op(self,func,a,b):
  n=self.call('/Script/Engine.KismetMathLibrary:'+func);link(*a,n,'A')
  if isinstance(b,tuple):link(*b,n,'B')
  else:val(n,'B',b)
  return n,'ReturnValue'
 def setexec(self,prev,name,value=None,cls='',obj=None):
  n=self.set(name,cls);link(*prev,n,'execute')
  if obj:link(*obj,n,'self')
  if isinstance(value,tuple):link(*value,n,name)
  elif value is not None:val(n,name,value)
  return n,'then'
 def owncall(self,prev,fn):
  n=self.call(self.bp.generated_class().get_path_name()+':'+fn);link(*prev,n,'execute');return n,'then'
def held(g,prev):
 pc=g.call('/Script/Engine.GameplayStatics:GetPlayerCharacter')
 c=g.cast(prev,(pc,'ReturnValue'),char.generated_class())
 a=g.get('HeldActor',char.generated_class().get_path_name());link(c,outcast(c),a,'self')
 return (c,'then'),(a,'HeldActor')
def target_checks(g,prev):
 t=g.get('RollTarget');obj=(t,'RollTarget')
 b=g.branch(prev,g.valid(obj));g.owncall((b,'else'),'CancelRolling')
 ex,h=held(g,(b,'then'))
 same=g.op('EqualEqual_ObjectObject',h,obj)
 b=g.branch(ex,same);g.owncall((b,'else'),'CancelRolling')
 dist=g.call('/Script/Engine.Actor:GetDistanceTo');link(h[0],h[1],dist,'OtherActor')
 maxdist=g.get('MaxUseDistance');near=g.op('LessEqual_DoubleDouble',(dist,'ReturnValue'),(maxdist,'MaxUseDistance'))
 b=g.branch((b,'then'),near);g.owncall((b,'else'),'CancelRolling')
 st=g.get('State',icls);link(*obj,st,'self');b=g.branch((b,'then'),g.eqstr((st,'State'),'Raw'));g.owncall((b,'else'),'CancelRolling')
 return (b,'then'),obj
try:
 char=EAL.load_asset(CHAR);ingredient=EAL.load_asset(ROOT+'BP_Ingredient');roll=EAL.load_asset(ROOT+'BP_RollingStation');chop=EAL.load_asset(ROOT+'BP_ChoppingBoard')
 variable(ingredient,'RollQuality','string');save(ingredient);icls=ingredient.generated_class().get_path_name()
 # Build the dedicated rolling HUD without changing the tray widget.
 widget=EAL.load_asset(ROOT+'WBP_RollingProgress')
 if not widget:
  widget=unreal.AssetToolsHelpers.get_asset_tools().create_asset('WBP_RollingProgress',ROOT.rstrip('/'),unreal.WidgetBlueprint,unreal.WidgetBlueprintFactory())
  for typ,name,parent in [('CanvasPanel','Root',''),('Border','Backdrop','Root'),('TextBlock','HelpText','Root'),('ProgressBar','RollBar','Root')]:
   r=json.loads(H.umg_add_widget(widget,typ,name,parent));assert r.get('success'),r
  H.umg_set_slot_layout(widget,'Backdrop',.5,.72,.5,.72,-300,0,600,105)
  H.umg_set_slot_layout(widget,'HelpText',.5,.72,.5,.72,-280,12,560,40)
  H.umg_set_slot_layout(widget,'RollBar',.5,.72,.5,.72,-280,64,560,24)
  H.umg_set_text_style(widget,'HelpText',18,1,1,1,1,1)
  H.umg_set_widget_is_variable(widget,'RollBar',True)
  textw=H.umg_find_widget(widget,'HelpText');textw.set_editor_property('text',unreal.Text('按住左键擀面，松开结算\n50–90 可用 · 65–75 完美（默认）'))
  border=H.umg_find_widget(widget,'Backdrop');border.set_editor_property('brush_color',unreal.LinearColor(.025,.035,.05,.9))
  bar=H.umg_find_widget(widget,'RollBar');bar.set_editor_property('fill_color_and_opacity',unreal.LinearColor(.95,.65,.15,1))
 save(widget);wcls=widget.generated_class().get_path_name()
 for name,kind,cls in [('bRolling','bool',None),('ProgressRate','double',None),('AcceptMin','double',None),('AcceptMax','double',None),('PerfectMin','double',None),('PerfectMax','double',None),('MaxUseDistance','double',None),('ProgressWidget','object',widget.generated_class())]:variable(roll,name,kind,cls)
 # Create function signatures before building calls between them.
 for fn in ['BeginRolling','FinishRolling','CancelRolling','HideRollUI']: 
  if not BEL.find_graph(roll,fn):BEL.add_function_graph(roll,fn)
 assert BEL.compile_blueprint(roll)
 cdo=unreal.get_default_object(roll.generated_class())
 for n,v in [('ProgressRate',20.),('AcceptMin',50.),('AcceptMax',90.),('PerfectMin',65.),('PerfectMax',75.),('MaxUseDistance',300.)]:
  cdo.set_editor_property(n,v);BEL.set_blueprint_variable_instance_editable(roll,n,True)
 # Remove old rolling tick implementation, retaining ordinary lifecycle events.
 ev=G(roll,'EventGraph');ev.ed.remove_nodes([n for n in ev.ed.list_all_nodes() if n.get_name() not in ['K2Node_Event_0','K2Node_CallParentFunction_0','K2Node_Event_1','K2Node_CallParentFunction_1','K2Node_Event_2','K2Node_CallParentFunction_2']])
 g=G(roll,'HideRollUI',True);wg=g.get('ProgressWidget');b=g.branch((g.entry,'then'),g.valid((wg,'ProgressWidget')));rm=g.call('/Script/UMG.Widget:RemoveFromParent');link(b,'then',rm,'execute');link(wg,'ProgressWidget',rm,'self')
 g=G(roll,'CancelRolling',True);ex=g.setexec((g.entry,'then'),'bRolling','false');t=g.get('RollTarget');b=g.branch(ex,g.valid((t,'RollTarget')))
 ex=g.setexec((b,'then'),'RollProgress',0,icls,(t,'RollTarget'));clear=g.set('RollTarget');link(*ex,clear,'execute');link(b,'else',clear,'execute');g.owncall((clear,'then'),'HideRollUI')
 g=G(roll,'Interact',True);g.msg((g.entry,'then'),'手持原始面团，对准擀面台按住左键；松开结算')
 g=G(roll,'BeginRolling',True)
 running=g.get('bRolling');b=g.branch((g.entry,'then'),(running,'bRolling'))
 ex,obj=held(g,(b,'else'));b=g.branch(ex,g.valid(obj));g.msg((b,'else'),'请先拿起面团')
 cast=g.cast((b,'then'),obj,ingredient.generated_class());obj=(cast,outcast(cast));g.msg((cast,'CastFailed'),'这里只能擀面团')
 typ=g.get('Type',icls);link(*obj,typ,'self');a=g.eqstr((typ,'Type'),'面团');bb=g.eqstr((typ,'Type'),'Dough');accepted=g.op('BooleanOR',a,bb)
 b=g.branch((cast,'then'),accepted);g.msg((b,'else'),'这里只能擀面团')
 st=g.get('State',icls);link(*obj,st,'self');b=g.branch((b,'then'),g.eqstr((st,'State'),'Raw'));g.msg((b,'else'),'需要原始面团；失败后请领取备用面团重做')
 ex=g.setexec((b,'then'),'RollTarget',obj);ex=g.setexec(ex,'RollProgress',0,icls,obj);ex=g.setexec(ex,'RollQuality','',icls,obj);ex=g.setexec(ex,'bRolling','true')
 create=g.menu('用户界面|创建控件');val(create,'Class',wcls);link(*ex,create,'execute')
 pc=g.call('/Script/Engine.GameplayStatics:GetPlayerController');link(pc,'ReturnValue',create,'OwningPlayer')
 ex=g.setexec((create,'then'),'ProgressWidget',(create,'ReturnValue'));add=g.call('/Script/UMG.UserWidget:AddToViewport');link(*ex,add,'execute');link(create,'ReturnValue',add,'self');val(add,'ZOrder',20)
 g.msg((add,'then'),'开始擀制：松开左键判定，离开工作台或换格会取消')
 # Tick only advances an active, still-held, in-range raw dough.
 g=ev;tick=next(n for n in g.ed.list_all_nodes() if n.get_name()=='K2Node_Event_2');p(tick,'then').break_pin_links()
 run=g.get('bRolling');b=g.branch((tick,'then'),(run,'bRolling'));ex,obj=target_checks(g,(b,'then'))
 progress=g.get('RollProgress',icls);link(*obj,progress,'self');rate=g.get('ProgressRate');delta=g.op('Multiply_DoubleDouble',(tick,'DeltaSeconds'),(rate,'ProgressRate'));summ=g.op('Add_DoubleDouble',(progress,'RollProgress'),delta)
 clamp=g.call('/Script/Engine.KismetMathLibrary:FClamp');link(*summ,clamp,'Value');val(clamp,'Min',0);val(clamp,'Max',100)
 ex=g.setexec(ex,'RollProgress',(clamp,'ReturnValue'),icls,obj)
 wg=g.get('ProgressWidget');valid=g.branch(ex,g.valid((wg,'ProgressWidget')));bar=g.get('RollBar',wcls);link(wg,'ProgressWidget',bar,'self')
 percent=g.op('Divide_DoubleDouble',(clamp,'ReturnValue'),100);setpct=g.call('/Script/UMG.ProgressBar:SetPercent');link(valid,'then',setpct,'execute');link(bar,'RollBar',setpct,'self');link(*percent,setpct,'InPercent')
 # Release judges the active dough once, retaining its result on the ingredient.
 g=G(roll,'FinishRolling',True);running=g.get('bRolling');b=g.branch((g.entry,'then'),(running,'bRolling'));ex,obj=target_checks(g,(b,'then'));ex=g.setexec(ex,'bRolling','false')
 pr=g.get('RollProgress',icls);link(*obj,pr,'self')
 def rangecheck(lo,hi):
  l=g.get(lo);h=g.get(hi);a=g.op('GreaterEqual_DoubleDouble',(pr,'RollProgress'),(l,lo));b=g.op('LessEqual_DoubleDouble',(pr,'RollProgress'),(h,hi));return g.op('BooleanAND',a,b)
 acceptable=g.branch(ex,rangecheck('AcceptMin','AcceptMax'));perfect=g.branch((acceptable,'then'),rangecheck('PerfectMin','PerfectMax'))
 for prev,state,quality,message in [((acceptable,'else'),'RollFailed','Failed','擀制失败，请放下失败面团并领取备用面团重做'),((perfect,'then'),'PieBase','Perfect','擀制完成：完美派底'),((perfect,'else'),'PieBase','Normal','擀制完成：普通派底')]:
  ex=g.setexec(prev,'State',state,icls,obj);ex=g.setexec(ex,'RollQuality',quality,icls,obj)
  refresh=g.call(icls+':RefreshLook');link(*ex,refresh,'execute');link(*obj,refresh,'self');m=g.msg((refresh,'then'),message)
  ex=g.setexec((m,'then'),'RollTarget');g.owncall(ex,'HideRollUI')
 save(roll)
 # Preserve the existing chopping graph, fix the recipe and accept both naming conventions.
 g=G(chop,'Interact');ns={n.get_name():n for n in g.ed.list_all_nodes()};val(ns['K2Node_VariableSet_1'],'CutNeeded',3)
 for idx,english,branchname in [(4,'Fish','K2Node_IfThenElse_1'),(5,'Onion','K2Node_IfThenElse_2'),(6,'Parsley','K2Node_IfThenElse_3')]:
  original=ns['K2Node_CallFunction_'+str(idx)];alias=g.eqstr((ns['K2Node_VariableGet_1'],'Type'),english);either=g.op('BooleanOR',(original,'ReturnValue'),alias);link(*either,ns[branchname],'Condition')
 save(chop)
 with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/processing_build_result.json','w',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:
 unreal.MCPythonHelper.submit_result(json.dumps({'partial':report,'error':traceback.format_exc()},ensure_ascii=False))
