import unreal,json,math
source='/Game/0Input/map/Kitchen_white'
dest='/Game/FoodGameplay/L_TraySupply_Test'
if unreal.EditorAssetLibrary.does_asset_exist(dest):
    raise RuntimeError('Test map already exists; leaving it untouched')
if not unreal.EditorAssetLibrary.duplicate_asset(source,dest):
    raise RuntimeError('Could not duplicate the kitchen map')
if not unreal.EditorLevelLibrary.load_level(dest):
    raise RuntimeError('Could not load the test map')
actors=list(unreal.EditorLevelLibrary.get_all_level_actors())
start=next(a for a in actors if a.get_class().get_name()=='PlayerStart')
loc=start.get_actor_location()
forward=start.get_actor_forward_vector()
right=start.get_actor_right_vector()
supply=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_IngredientSupply')
unreal.BlueprintEditorLibrary.compile_blueprint(supply)
names=['Dough','Fish','Onion','Parsley','FishHeadGroup','Seasoning']
placed=[]
for i,name in enumerate(names):
    offset=(i-2.5)*120.0
    pos=unreal.Vector(loc.x+forward.x*240+right.x*offset,
                      loc.y+forward.y*240+right.y*offset,
                      65.0)
    a=unreal.EditorLevelLibrary.spawn_actor_from_class(supply.generated_class(),pos)
    if not a:raise RuntimeError('spawn failed '+name)
    a.set_actor_label('Supply_'+name)
    a.set_editor_property('IngredientName',name)
    a.set_editor_property('Stock',2)
    placed.append({'label':a.get_actor_label(),'loc':[pos.x,pos.y,pos.z],'stock':a.get_editor_property('Stock')})
saved=unreal.EditorLevelLibrary.save_current_level()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_test_map_result.json','w',encoding='utf-8') as f:
    json.dump({'map':dest,'saved':saved,'placed':placed},f,ensure_ascii=False,indent=2)
