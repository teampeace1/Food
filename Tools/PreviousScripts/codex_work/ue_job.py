import json
import unreal

def finish(data):
    unreal.MCPythonHelper.submit_result(json.dumps(data, ensure_ascii=False, default=str))

bel = unreal.BlueprintEditorLibrary
specs = {
    '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter': [
        ('TraySlot1Component', 'object', unreal.PrimitiveComponent),
        ('TraySlot2Component', 'object', unreal.PrimitiveComponent),
        ('TraySlot3Component', 'object', unreal.PrimitiveComponent),
    ],
}
out = []
for path, fields in specs.items():
    bp = unreal.EditorAssetLibrary.load_asset(path)
    existing = set(str(x) for x in bel.list_member_variable_names(bp))
    for name, category, sub in fields:
        if name in existing:
            out.append((path, name, 'exists'))
            continue
        pin_type = (bel.get_object_reference_type(sub.static_class()) if sub
                    else bel.get_basic_type_by_name(category))
        ok = bel.add_member_variable(bp, name, pin_type)
        if path.endswith('BP_IngredientSupply') and ok:
            bel.set_blueprint_variable_instance_editable(bp, name, True)
        out.append((path, name, ok))
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
cube = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube')
for name in ('BP_Ingredient', 'BP_IngredientSupply'):
    path = '/Game/FoodGameplay/' + name
    bp = unreal.EditorAssetLibrary.load_asset(path)
    bel.compile_blueprint(bp)
    cdo = unreal.get_default_object(bp.generated_class())
    mesh = cdo.get_editor_property('static_mesh_component')
    mesh.set_editor_property('static_mesh', cube)
    if name == 'BP_IngredientSupply':
        cdo.set_editor_property('Stock', 2)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
finish({'vars': out})
