import unreal, json, os

target = os.environ.get('FOOD_BLUEPRINT_TARGET','/Game/FoodGameplay/TempCharacterProbe')
if target.endswith('TempCharacterProbe'):
    if unreal.EditorAssetLibrary.does_asset_exist(target): unreal.EditorAssetLibrary.delete_asset(target)
    unreal.EditorAssetLibrary.duplicate_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter',target)
bp = unreal.EditorAssetLibrary.load_asset(target)
ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
supply = unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_IngredientSupply')
ingredient = unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_Ingredient')
unreal.BlueprintEditorLibrary.compile_blueprint(supply)
unreal.BlueprintEditorLibrary.compile_blueprint(ingredient)
nodes={str(n.get_name()):n for n in ed.list_all_nodes()}
created=[]
def pin(n,name):
    if isinstance(n,str): n=nodes[n]
    p=next((p for p in n.list_all_pins() if str(p.get_pin_name())==name),None)
    if p is None: raise RuntimeError('missing pin '+str(n.get_name())+'.'+name)
    return p
def link(a,ap,b,bp):
    if not pin(a,ap).try_create_connection(pin(b,bp)):
        raise RuntimeError('link failed '+str(a)+'.'+ap+' -> '+str(b)+'.'+bp)
def value(n,p,v):
    if not pin(n,p).set_pin_value(str(v)): raise RuntimeError('value failed '+str(n)+'.'+p+'='+str(v))
def add(n,x,y):
    if n is None:raise RuntimeError('node not created')
    n.set_node_pos(unreal.IntPoint(x,y))
    created.append(str(n.get_name()))
    return n
def call(path,x,y):return add(ed.add_call_function_node(path),x,y)
def menu(name,x,y):return add(ed.create_node_from_name(name,unreal.Vector2D(x,y),[]),x,y)
def get(name,x,y,cls=''):return add(ed.add_get_member_variable_node(name,cls),x,y)
def setv(name,x,y,cls=''):return add(ed.add_set_member_variable_node(name,cls),x,y)
def branch(x,y):return add(ed.add_branch_node(),x,y)

# Trace on E even while holding, so a full tray can report its state at a supply counter.
pin('K2Node_EnhancedInputAction_1','Started').break_pin_links()
pin('K2Node_CallFunction_14','execute').break_pin_links()
link('K2Node_EnhancedInputAction_1','Started','K2Node_CallFunction_14','execute')
# A supply counter is recognized before the existing physics-grab path.
cast=menu('工具|Casting|CastToStaticMeshActor',5500,900)
if not ed.retarget_node_class(cast,unreal.StaticMeshActor.static_class(),supply.generated_class()):raise RuntimeError('cast retarget failed')
pin('K2Node_IfThenElse_1','then').break_pin_links()
link('K2Node_IfThenElse_1','then',cast,'execute')
link('K2Node_CallFunction_15','HitActor',cast,'Object')
holding_now=get('bIsHolding',5700,400)
ordinary=branch(6000,450)
link(holding_now,'bIsHolding',ordinary,'Condition')
link(cast,'CastFailed',ordinary,'execute')
link('K2Node_IfThenElse_1','else',ordinary,'execute')
link(ordinary,'then','K2Node_CallFunction_20','execute')
stock=get('Stock',5800,850,supply.generated_class().get_path_name())
link(cast,'AsBP Ingredient Supply',stock,'self')
positive=call('/Script/Engine.KismetMathLibrary:Greater_IntInt',6050,890)
link(stock,'Stock',positive,'A');value(positive,'B','0')
has_stock=branch(6250,900)
link(cast,'then',has_stock,'execute');link(positive,'ReturnValue',has_stock,'Condition')
empty_msg=menu('开发|PrintString',6500,1200)
value(empty_msg,'InString','这一批已经用完了')
link(has_stock,'else',empty_msg,'execute')

# Find the first empty slot, and never replace an occupied slot.
prev=(has_stock,'then')
slot_sets=[]
for i in (1,2,3):
    x=6650+(i-1)*470
    slot=get('TraySlot'+str(i),x,750)
    valid=call('/Script/Engine.KismetSystemLibrary:IsValid',x+170,750)
    link(slot,'TraySlot'+str(i),valid,'Object')
    b=branch(x+190,950)
    link(prev[0],prev[1],b,'execute');link(valid,'ReturnValue',b,'Condition')
    s=setv('SelectedSlot',x+360,1050);value(s,'SelectedSlot',i)
    link(b,'else',s,'execute')
    slot_sets.append(s)
    prev=(b,'then')
full_msg=menu('开发|PrintString',8100,900)
value(full_msg,'InString','先放下手里的食材')
link(prev[0],prev[1],full_msg,'execute')

# The same first-empty rule applies to physical ingredients.
physics_prev=(ordinary,'else')
for i in (1,2,3):
    x=6250+(i-1)*470
    slot=get('TraySlot'+str(i),x,100)
    valid=call('/Script/Engine.KismetSystemLibrary:IsValid',x+170,100)
    link(slot,'TraySlot'+str(i),valid,'Object')
    b=branch(x+190,280)
    link(physics_prev[0],physics_prev[1],b,'execute');link(valid,'ReturnValue',b,'Condition')
    s=setv('SelectedSlot',x+360,380);value(s,'SelectedSlot',i)
    link(b,'else',s,'execute')
    link(s,'then','K2Node_IfThenElse_2','execute')
    physics_prev=(b,'then')
physics_full=menu('开发|PrintString',7900,300)
value(physics_full,'InString','先放下手里的食材')
link(physics_prev[0],physics_prev[1],physics_full,'execute')

spawn=menu('游戏|从类生成Actor',8300,1350)
value(spawn,'Class',ingredient.generated_class().get_path_name())
value(spawn,'CollisionHandlingOverride','AlwaysSpawn')
make_transform=call('/Script/Engine.KismetMathLibrary:MakeTransform',8050,1600)
link(make_transform,'ReturnValue',spawn,'SpawnTransform')
old_held=get('HeldActor',8000,1150)
old_valid=call('/Script/Engine.KismetSystemLibrary:IsValid',8200,1120)
link(old_held,'HeldActor',old_valid,'Object')
old_branch=branch(8350,1100)
link(old_valid,'ReturnValue',old_branch,'Condition')
for s in slot_sets:link(s,'then',old_branch,'execute')
old_hide=call('/Script/Engine.Actor:SetActorHiddenInGame',8500,1040)
link(old_held,'HeldActor',old_hide,'self');value(old_hide,'bNewHidden','true')
link(old_branch,'then',old_hide,'execute')
link(old_hide,'then',spawn,'execute')
link(old_branch,'else',spawn,'execute')
spawned=call('/Script/Engine.KismetSystemLibrary:IsValid',8600,1600)
link(spawn,'ReturnValue',spawned,'Object')
spawn_ok=branch(8800,1350)
link(spawn,'then',spawn_ok,'execute');link(spawned,'ReturnValue',spawn_ok,'Condition')

# Stock changes only after a valid actor was spawned.
source_name=get('IngredientName',9000,1850,supply.generated_class().get_path_name())
link(cast,'AsBP Ingredient Supply',source_name,'self')
set_ingredient_name=setv('IngredientName',9050,1450,ingredient.generated_class().get_path_name())
link(spawn,'ReturnValue',set_ingredient_name,'self')
link(source_name,'IngredientName',set_ingredient_name,'IngredientName')
link(spawn_ok,'then',set_ingredient_name,'execute')
minus=call('/Script/Engine.KismetMathLibrary:Subtract_IntInt',9000,1630)
link(stock,'Stock',minus,'A');value(minus,'B','1')
set_stock=setv('Stock',9100,1350,supply.generated_class().get_path_name())
link(cast,'AsBP Ingredient Supply',set_stock,'self')
link(minus,'ReturnValue',set_stock,'Stock')
collision=call('/Script/Engine.Actor:SetActorEnableCollision',9350,1350)
link(set_ingredient_name,'then',collision,'execute');link(spawn,'ReturnValue',collision,'self')
value(collision,'bNewActorEnableCollision','false')
attach=call('/Script/Engine.Actor:K2_AttachToComponent',9600,1350)
link(collision,'then',attach,'execute');link(spawn,'ReturnValue',attach,'self')
link('K2Node_VariableGet_4','FirstPersonCamera',attach,'Parent')
for rule in ('LocationRule','RotationRule'):value(attach,rule,'SnapToTarget')
attached=branch(9800,1200)
link(attach,'then',attached,'execute');link(attach,'ReturnValue',attached,'Condition')
link(attached,'then',set_stock,'execute')
destroy=call('/Script/Engine.Actor:K2_DestroyActor',10000,1120)
link(attached,'else',destroy,'execute');link(spawn,'ReturnValue',destroy,'self')
relative=call('/Script/Engine.Actor:K2_SetActorRelativeLocation',9900,1350)
link(set_stock,'then',relative,'execute');link(spawn,'ReturnValue',relative,'self')
link('K2Node_CallFunction_25','ReturnValue',relative,'NewRelativeLocation')
mesh=get('StaticMeshComponent',10000,1730,'/Script/Engine.StaticMeshActor')
link(spawn,'ReturnValue',mesh,'self')
held_actor=setv('HeldActor',10200,1350)
link(relative,'then',held_actor,'execute');link(spawn,'ReturnValue',held_actor,'HeldActor')
held_comp=setv('HeldComponent',10450,1350)
link(held_actor,'then',held_comp,'execute');link(mesh,'StaticMeshComponent',held_comp,'HeldComponent')
holding=setv('bIsHolding',10700,1350)
value(holding,'bIsHolding','true');link(held_comp,'then',holding,'execute')
link(holding,'then','K2Node_IfThenElse_3','execute')

# The existing slot dispatcher now uses the shared held item values.
current_actor=get('HeldActor',7350,1680)
current_comp=get('HeldComponent',7350,1780)
for i in (1,2,3):
    link(current_actor,'HeldActor',nodes['K2Node_VariableSet_'+str(14+i*2)],'TraySlot'+str(i))
    link(current_comp,'HeldComponent',nodes['K2Node_VariableSet_'+str(15+i*2)],'TraySlot'+str(i)+'Component')

# Items attached to the camera do not collide with the player; dropping restores collision.
pin('K2Node_CallFunction_19','then').break_pin_links()
pickup_collision=call('/Script/Engine.Actor:SetActorEnableCollision',4700,850)
link('K2Node_CallFunction_19','then',pickup_collision,'execute')
link('K2Node_CallFunction_15','HitActor',pickup_collision,'self')
value(pickup_collision,'bNewActorEnableCollision','false')
link(pickup_collision,'then','K2Node_VariableSet_0','execute')
pin('K2Node_CallFunction_21','then').break_pin_links()
drop_collision=call('/Script/Engine.Actor:SetActorEnableCollision',3000,350)
link('K2Node_CallFunction_21','then',drop_collision,'execute')
link('K2Node_VariableGet_1','HeldActor',drop_collision,'self')
value(drop_collision,'bNewActorEnableCollision','true')
link(drop_collision,'then','K2Node_VariableSet_3','execute')

# Selecting 1-3 hides the old hand item and reveals the newly selected one.
for i in (1,2,3):
    x=11000+(i-1)*700
    key=nodes['K2Node_InputKey_'+str(i-1)]
    selected=nodes['K2Node_VariableSet_'+str(4+(i-1)*4)]
    selected_holding=nodes['K2Node_VariableSet_'+str(7+(i-1)*4)]
    pin(key,'Pressed').break_pin_links()
    old=get('HeldActor',x,2000)
    valid=call('/Script/Engine.KismetSystemLibrary:IsValid',x+150,2000)
    link(old,'HeldActor',valid,'Object')
    b=branch(x+250,2200)
    link(key,'Pressed',b,'execute');link(valid,'ReturnValue',b,'Condition')
    hide=call('/Script/Engine.Actor:SetActorHiddenInGame',x+420,2150)
    link(old,'HeldActor',hide,'self');value(hide,'bNewHidden','true')
    link(b,'then',hide,'execute');link(hide,'then',selected,'execute')
    link(b,'else',selected,'execute')
    new=get('HeldActor',x+400,2500)
    new_valid=call('/Script/Engine.KismetSystemLibrary:IsValid',x+590,2500)
    link(new,'HeldActor',new_valid,'Object')
    show_branch=branch(x+700,2200)
    link(selected_holding,'then',show_branch,'execute')
    link(new_valid,'ReturnValue',show_branch,'Condition')
    show=call('/Script/Engine.Actor:SetActorHiddenInGame',x+850,2150)
    link(new,'HeldActor',show,'self');value(show,'bNewHidden','false')
    link(show_branch,'then',show,'execute')

ok=unreal.BlueprintEditorLibrary.compile_blueprint(bp)
errors=[str(n.get_node_title()) for n in ed.list_nodes_with_errors()]
out={'target':target,'compiled':ok,'errors':errors,'created':created}
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_build_supply_result.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
if ok and not errors:unreal.EditorAssetLibrary.save_asset(target,only_if_is_dirty=False)
