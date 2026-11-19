import unreal,json,traceback
src=open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/build_processing_v2.py',encoding='utf-8').read();exec(src.split('\ntry:\n')[0],globals())
try:
 char=EAL.load_asset(CHAR);base=EAL.load_asset(ROOT+'BP_Workstation');ingredient=EAL.load_asset(ROOT+'BP_Ingredient');roll=EAL.load_asset(ROOT+'BP_RollingStation');sink=EAL.load_asset(ROOT+'BP_Sink');ccls=char.generated_class().get_path_name();icls=ingredient.generated_class().get_path_name()
 g=G(base,'TakeStationItem',True);cur=g.get('StationItem');item=(cur,'StationItem');b=g.branch((g.entry,'then'),g.valid(item));g.msg((b,'else'),'工作台没有食材')
 selfnode=g.menu('变量|获得一个对自身的引用');rs=g.cast((b,'then'),(selfnode,'self'),roll.generated_class());r=g.get('bRolling',roll.generated_class().get_path_name());link(rs,outcast(rs),r,'self');b=g.branch((rs,'then'),(r,'bRolling'));g.msg((b,'then'),'请先松开左键结束擀制')
 ss=g.cast((rs,'CastFailed'),(selfnode,'self'),sink.generated_class());running=g.get('bRunning',sink.generated_class().get_path_name());link(ss,outcast(ss),running,'self');sb=g.branch((ss,'then'),(running,'bRunning'));g.msg((sb,'then'),'请先按 E 关水')
 pc=g.call('/Script/Engine.GameplayStatics:GetPlayerCharacter');c=g.cast((b,'else'),(pc,'ReturnValue'),char.generated_class());link(sb,'else',c,'execute');link(ss,'CastFailed',c,'execute');player=(c,outcast(c))
 holding=g.get('bIsHolding',ccls);link(*player,holding,'self');b=g.branch((c,'then'),(holding,'bIsHolding'));g.msg((b,'then'),'请先放下手中食材')
 mesh=g.get('StaticMeshComponent',icls);link(*item,mesh,'self')
 # Reserve first empty slot before moving the item.
 ex=(b,'else');selected=[]
 for i in (1,2,3):
  n='TraySlot'+str(i);slot=g.get(n,ccls);link(*player,slot,'self');branch=g.branch(ex,g.valid((slot,n)));ex=(branch,'then')
  yes=g.setexec((branch,'else'),n,item,ccls,player);yes=g.setexec(yes,n+'Component',(mesh,'StaticMeshComponent'),ccls,player);yes=g.setexec(yes,'SelectedSlot',i,ccls,player);selected.append(yes)
 g.msg(ex,'托盘已满，请先放下食材')
 first=g.set('HeldActor',ccls);link(*player,first,'self');link(*item,first,'HeldActor')
 for x in selected:link(*x,first,'execute')
 ex=g.setexec((first,'then'),'HeldComponent',(mesh,'StaticMeshComponent'),ccls,player);ex=g.setexec(ex,'bIsHolding','true',ccls,player)
 camera=g.get('FirstPersonCamera',ccls);link(*player,camera,'self');attach=g.call('/Script/Engine.Actor:K2_AttachToComponent');link(*ex,attach,'execute');link(*item,attach,'self');link(camera,'FirstPersonCamera',attach,'Parent')
 offset=g.get('HeldOffset',icls);link(*item,offset,'self');vec=g.call('/Script/Engine.KismetMathLibrary:MakeVector');val(vec,'X',70);val(vec,'Y',12);val(vec,'Z',-10);add=g.call('/Script/Engine.KismetMathLibrary:Add_VectorVector');link(vec,'ReturnValue',add,'A');link(offset,'HeldOffset',add,'B')
 move=g.call('/Script/Engine.Actor:K2_SetActorRelativeLocation');link(attach,'then',move,'execute');link(*item,move,'self');link(add,'ReturnValue',move,'NewRelativeLocation')
 visible=g.call('/Script/Engine.Actor:SetActorHiddenInGame');link(move,'then',visible,'execute');link(*item,visible,'self');val(visible,'bNewHidden','false')
 ex=g.setexec((visible,'then'),'StationItem');g.msg(ex,'已取回食材')
 save(base);unreal.MCPythonHelper.submit_result(json.dumps(report,ensure_ascii=False))
except Exception:unreal.MCPythonHelper.submit_result(json.dumps({'partial':report,'error':traceback.format_exc()},ensure_ascii=False))

