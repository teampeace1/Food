import unreal,json
path='/Game/FoodGameplay/TempCharacterProbe'
if unreal.EditorAssetLibrary.does_asset_exist(path): unreal.EditorAssetLibrary.delete_asset(path)
unreal.EditorAssetLibrary.duplicate_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter',path)
bp=unreal.EditorAssetLibrary.load_asset(path)
g=unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
supply=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_IngredientSupply')
ingredient=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_Ingredient')
unreal.BlueprintEditorLibrary.compile_blueprint(supply)
unreal.BlueprintEditorLibrary.compile_blueprint(ingredient)
out={}
def info(n):
    return {'name':str(n.get_name()) if n else None,'class':str(n.get_class().get_name()) if n else None,'pins':[{'name':str(p.get_pin_name()),'value':str(p.get_pin_value()),'type':str(p.get_pin_type_display_string())} for p in n.list_all_pins()] if n else []}
for label,make in {
 'stock_get':lambda:ed.add_get_member_variable_node('Stock',str(supply.generated_class().get_path_name())),
 'stock_set':lambda:ed.add_set_member_variable_node('Stock',str(supply.generated_class().get_path_name())),
 'spawn':lambda:ed.create_node_from_name('游戏|从类生成Actor',unreal.Vector2D(14000,0),[]),
 'print':lambda:ed.create_node_from_name('开发|PrintString',unreal.Vector2D(14100,0),[]),
 'greater':lambda:ed.create_node_from_name('数学|整数|大于',unreal.Vector2D(14200,0),[]),
 'greater_func':lambda:ed.add_call_function_node('/Script/Engine.KismetMathLibrary:Greater_IntInt'),
 'subtract_func':lambda:ed.add_call_function_node('/Script/Engine.KismetMathLibrary:Subtract_IntInt'),
 'isvalid_func':lambda:ed.add_call_function_node('/Script/Engine.KismetSystemLibrary:IsValid'),
 'attach':lambda:ed.add_call_function_node('/Script/Engine.Actor:K2_AttachToComponent'),
 'getmesh':lambda:ed.add_call_function_node('/Script/Engine.StaticMeshActor:GetStaticMeshComponent'),
 'meshvar':lambda:ed.add_get_member_variable_node('StaticMeshComponent','/Script/Engine.StaticMeshActor'),
 'hidden':lambda:ed.add_call_function_node('/Script/Engine.Actor:SetActorHiddenInGame'),
 'collision':lambda:ed.add_call_function_node('/Script/Engine.Actor:SetActorEnableCollision'),
 'actorloc':lambda:ed.add_call_function_node('/Script/Engine.Actor:K2_GetActorLocation'),
 }.items():
    try:out[label]=info(make())
    except Exception as e:out[label]=repr(e)
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_build_probe.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
