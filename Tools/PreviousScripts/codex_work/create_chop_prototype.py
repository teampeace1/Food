import unreal,json
path='/Game/FoodGameplay/BP_ChoppingBoard_Prototype'
if unreal.EditorAssetLibrary.does_asset_exist(path):
    raise RuntimeError('Prototype already exists; left untouched')
parent=unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_Workstation')
factory=unreal.BlueprintFactory()
factory.set_editor_property('parent_class',parent.generated_class())
bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_ChoppingBoard_Prototype','/Game/FoodGameplay',unreal.Blueprint,factory)
bel=unreal.BlueprintEditorLibrary
for name in ('FishRequiredCuts','OnionRequiredCuts','ParsleyRequiredCuts'):
    if not bel.add_member_variable(bp,name,bel.get_basic_type_by_name('int')): raise RuntimeError(name)
    bel.set_blueprint_variable_instance_editable(bp,name,True)
if not bel.compile_blueprint(bp):raise RuntimeError('compile failed')
cdo=unreal.get_default_object(bp.generated_class())
for name,value in [('FishRequiredCuts',3),('OnionRequiredCuts',3),('ParsleyRequiredCuts',2)]: cdo.set_editor_property(name,value)
saved=unreal.EditorAssetLibrary.save_asset(path,only_if_is_dirty=False)
unreal.MCPythonHelper.submit_result(json.dumps({'saved':saved,'path':path}))
