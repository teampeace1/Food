import unreal,json
dest='/Game/FoodGameplay/L_TraySupply_Playtest'
if unreal.EditorAssetLibrary.does_asset_exist(dest):raise RuntimeError('Playtest map already exists')
if not unreal.EditorLevelLibrary.new_level(dest):raise RuntimeError('Could not create level')
cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube')
floor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,-55))
floor.set_actor_label('TestFloor')
floor.static_mesh_component.set_editor_property('static_mesh',cube)
floor.set_actor_scale3d(unreal.Vector(12,10,0.1))
start=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(-350,0,100),unreal.Rotator(0,0,0))
start.set_actor_label('PlayerStart')
light=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PointLight,unreal.Vector(0,0,450))
light.set_actor_label('TestLight')
light.point_light_component.set_editor_property('intensity',120000)
supply=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_IngredientSupply')
unreal.BlueprintEditorLibrary.compile_blueprint(supply)
names=['Dough','Fish','Onion','Parsley','FishHeadGroup','Seasoning']
placed=[]
for i,name in enumerate(names):
    pos=unreal.Vector(160,(i-2.5)*145,0)
    a=unreal.EditorLevelLibrary.spawn_actor_from_class(supply.generated_class(),pos)
    a.set_actor_label('Supply_'+name)
    a.set_editor_property('IngredientName',name)
    a.set_editor_property('Stock',2)
    placed.append(a.get_actor_label())
saved=unreal.EditorLevelLibrary.save_current_level()
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_playtest_map_result.json','w',encoding='utf-8') as f:
    json.dump({'map':dest,'saved':saved,'placed':placed},f,ensure_ascii=False,indent=2)
