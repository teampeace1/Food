import unreal, json
out = {}
path = '/Game/FoodGameplay/TempCharacterProbe'
if unreal.EditorAssetLibrary.does_asset_exist(path):
    unreal.EditorAssetLibrary.delete_asset(path)
unreal.EditorAssetLibrary.duplicate_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter', path)
bp = unreal.EditorAssetLibrary.load_asset(path)
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
supply = unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_IngredientSupply')
unreal.BlueprintEditorLibrary.compile_blueprint(supply)
n = next(n for n in ed.list_all_nodes() if n.get_name() == 'K2Node_CallFunction_15')
pin = next(p for p in n.list_all_pins() if str(p.get_pin_name()) == 'HitActor')
out['doc'] = str(ed.create_node_from_name.__doc__)
out['retargetdoc'] = str(ed.retarget_node_class.__doc__)
out['actorcasts'] = [x for x in ed.list_available_nodes([pin]) if 'CastToActor' in x][:10]
out['meshcasts'] = [x for x in ed.list_available_nodes([pin]) if 'CastToStaticMeshActor' in x][:10]
out['all_actorcasts'] = [x for x in ed.list_available_nodes([]) if 'CastToStaticMeshActor' in x][:10]
for i, name in enumerate(['工具|Casting|CastToBP_IngredientSupply', 'Utilities|Casting|CastToBP_IngredientSupply', 'CastToBP_IngredientSupply']):
    try:
        v = ed.create_node_from_name(name, unreal.Vector2D(12000+i*200, 0), [pin], supply.generated_class())
        out[name] = str(v)
        if v: out[name+' pins'] = [str(p.get_pin_name()) for p in v.list_all_pins()]
    except Exception as e: out[name] = repr(e)
v=ed.create_node_from_name('工具|Casting|CastToStaticMeshActor',unreal.Vector2D(13000,0),[pin])
out['basecast']=str(v)
if v:
    out['basecast pins']=[str(p.get_pin_name()) for p in v.list_all_pins()]
    try:
        out['retarget']=ed.retarget_node_class(v,unreal.StaticMeshActor.static_class(),supply.generated_class())
        out['newpins']=[str(p.get_pin_name()) for p in v.list_all_pins()]
    except Exception as e: out['retarget']=repr(e)
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_cast_probe.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
