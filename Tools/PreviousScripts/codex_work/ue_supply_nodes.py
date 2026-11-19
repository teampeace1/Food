import json
import unreal

bp = unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
h = unreal.MCPythonHelper
out = []
specs = [
    {'type':'CastTo','cast_class':'/Game/FoodGameplay/BP_IngredientSupply.BP_IngredientSupply_C','pos_x':3350,'pos_y':2100},
    {'type':'VariableGet','variable_name':'Stock','variable_class':'/Game/FoodGameplay/BP_IngredientSupply.BP_IngredientSupply_C','pos_x':3650,'pos_y':2360},
    {'type':'VariableGet','variable_name':'IngredientName','variable_class':'/Game/FoodGameplay/BP_IngredientSupply.BP_IngredientSupply_C','pos_x':3650,'pos_y':2550},
    {'type':'CallFunction','target':'KismetMathLibrary','function_name':'Greater_IntInt','pos_x':3880,'pos_y':2360,'pin_defaults':{'B':'0'}},
    {'type':'Branch','pos_x':4080,'pos_y':2100},
    {'type':'CallFunction','target':'KismetSystemLibrary','function_name':'PrintString','pos_x':4300,'pos_y':2650,
     'pin_defaults':{'InString':'这一批已经用完了','Duration':'3.0'}},
    {'type':'SpawnActor','pos_x':4320,'pos_y':2100},
    {'type':'CallFunction','target':'Actor','function_name':'GetActorTransform','pos_x':3870,'pos_y':2600},
]
for spec in specs:
    r = json.loads(h.add_blueprint_node(bp,'EventGraph',json.dumps(spec,ensure_ascii=False)))
    if not r.get('success'):
        raise RuntimeError((spec,r))
    out.append(r)
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
