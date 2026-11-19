import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 char=EAL.load_asset(CHAR);base=EAL.load_asset(ROOT+'BP_Workstation');ingredient=EAL.load_asset(ROOT+'BP_Ingredient');chop=EAL.load_asset(ROOT+'BP_ChoppingBoard');roll=EAL.load_asset(ROOT+'BP_RollingStation');sink=EAL.load_asset(ROOT+'BP_Sink')
 icls=ingredient.generated_class().get_path_name();ccls=char.generated_class().get_path_name()
 variable(base,'StationItem','object',ingredient.generated_class())
 for fn in ['PlaceStationItem','TakeStationItem']:
  if not BEL.find_graph(base,fn):BEL.add_function_graph(base,fn)
 assert BEL.compile_blueprint(base)
 # Place: require a free station and a held ingredient appropriate to the station.
 g=G(base,'PlaceStationItem',True);cur=g.get('StationItem');br=g.branch((g.entry,'then'),g.valid((cur,'StationItem')));g.msg((br,'then'),'工作台已有食材，请先取回')
 ex,obj=held(g,(br,'else'));b=g.branch(ex,g.valid(obj));g.msg((b,'else'),'请先拿起食材')
 c=g.cast((b,'then'),obj,ingredient.generated_class());g.msg((c,'CastFailed'),'这个物品不能放在这里');item=(c,outcast(c))
 # Validate station type without changing any item on failure.
 selfnode=g.menu('变量|获得一个对自身的引用')
 cs=g.cast((c,'then'),(selfnode,'self'),sink.generated_class());cr=g.cast((cs,'CastFailed'),(selfnode,'self'),roll.generated_class());cc=g.cast((cr,'CastFailed'),(selfnode,'self'),chop.generated_class());g.msg((cc,'CastFailed'),'这个工作台不能放入食材')
 washable=g.get('bWashable',icls);link(*item,washable,'self');b=g.branch((cs,'then'),(washable,'bWashable'));g.msg((b,'else'),'这个食材不需要清洗');sinkok=(b,'then')
 typ=g.get('Type',icls);link(*item,typ,'self');state=g.get('State',icls);link(*item,state,'self')
 dough=g.op('BooleanOR',g.eqstr((typ,'Type'),'面团'),g.eqstr((typ,'Type'),'Dough'));raw=g.eqstr((state,'State'),'Raw');br=g.branch((cr,'then'),g.op('BooleanAND',dough,raw));g.msg((br,'else'),'擀面台只接受原始面团');rollok=(br,'then')
 fish=g.op('BooleanOR',g.eqstr((typ,'Type'),'鱼'),g.eqstr((typ,'Type'),'Fish'));onion=g.op('BooleanOR',g.eqstr((typ,'Type'),'洋葱'),g.eqstr((typ,'Type'),'Onion'));parsley=g.op('BooleanOR',g.eqstr((typ,'Type'),'欧芹'),g.eqstr((typ,'Type'),'Parsley'))
 validtype=g.op('BooleanOR',g.op('BooleanOR',fish,onion),parsley);br=g.branch((cc,'then'),validtype);g.msg((br,'else'),'案板只接受鱼、洋葱或欧芹');chopok=(br,'then')
 setitem=g.set('StationItem');link(*sinkok,setitem,'execute');link(*rollok,setitem,'execute');link(*chopok,setitem,'execute');link(*item,setitem,'StationItem')
 pc=g.call('/Script/Engine.GameplayStatics:GetPlayerCharacter');pcast=g.cast((setitem,'then'),(pc,'ReturnValue'),char.generated_class());clear=g.call(ccls+':ClearHeldTraySlot');link(pcast,'then',clear,'execute');link(pcast,outcast(pcast),clear,'self')
 # Keep the object visible, disable collision/physics, and place it at the top of the station bounds.
 det=g.call('/Script/Engine.Actor:K2_DetachFromActor');link(clear,'then',det,'execute');link(*item,det,'self')
 mesh=g.get('StaticMeshComponent',icls);link(*item,mesh,'self');sim=g.call('/Script/Engine.PrimitiveComponent:SetSimulatePhysics');link(det,'then',sim,'execute');link(mesh,'StaticMeshComponent',sim,'self');val(sim,'bSimulate','false')
 col=g.call('/Script/Engine.Actor:SetActorEnableCollision');link(sim,'then',col,'execute');link(*item,col,'self');val(col,'bNewActorEnableCollision','false')
 bounds=g.call('/Script/Engine.Actor:GetActorBounds');breakv=g.call('/Script/Engine.KismetMathLibrary:BreakVector');link(bounds,'BoxExtent',breakv,'InVec');height=g.op('Add_DoubleDouble',(breakv,'Z'),30);vec=g.call('/Script/Engine.KismetMathLibrary:MakeVector');link(*height,vec,'Z');pos=g.call('/Script/Engine.KismetMathLibrary:Add_VectorVector');link(bounds,'Origin',pos,'A');link(vec,'ReturnValue',pos,'B')
 move=g.call('/Script/Engine.Actor:K2_SetActorLocation');link(col,'then',move,'execute');link(*item,move,'self');link(pos,'ReturnValue',move,'NewLocation');val(move,'bTeleport','true')
 show=g.call('/Script/Engine.Actor:SetActorHiddenInGame');link(move,'then',show,'execute');link(*item,show,'self');val(show,'bNewHidden','false')
 ex=(show,'then');player=(pcast,outcast(pcast))
 for var in ['HeldActor','HeldComponent','bIsHolding']:ex=g.setexec(ex,var,'false' if var=='bIsHolding' else None,ccls,player)
 g.msg(ex,'食材已放入工作台')
 save(base)
 unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'partial':report,'error':traceback.format_exc()},ensure_ascii=False))

