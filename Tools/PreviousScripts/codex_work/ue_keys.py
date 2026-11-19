import json
import unreal

path = '/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter'
bp = unreal.EditorAssetLibrary.load_asset(path)
h = unreal.MCPythonHelper
results = []

def add(spec):
    r = json.loads(h.add_blueprint_node(bp, 'EventGraph', json.dumps(spec)))
    if not r.get('success'):
        raise RuntimeError(r)
    results.append(('add', r['node_name'], r['node_title']))
    return r['node_name']

def link(a, ap, b, bpin):
    r = json.loads(h.connect_blueprint_pins(bp, 'EventGraph', a, ap, b, bpin))
    if not r.get('success'):
        raise RuntimeError((a, ap, b, bpin, r))

for i, key in enumerate(('One', 'Two', 'Three'), 1):
    x = 5200 + (i - 1) * 1800
    y = 1000
    event = add({'type': 'InputKey', 'key_name': key, 'pos_x': x, 'pos_y': y})
    selected = add({'type': 'VariableSet', 'variable_name': 'SelectedSlot', 'pos_x': x + 220, 'pos_y': y,
                    'pin_defaults': {'SelectedSlot': str(i)}})
    slot = add({'type': 'VariableGet', 'variable_name': f'TraySlot{i}', 'pos_x': x + 450, 'pos_y': y + 350})
    component = add({'type': 'VariableGet', 'variable_name': f'TraySlot{i}Component', 'pos_x': x + 450, 'pos_y': y + 550})
    held = add({'type': 'VariableSet', 'variable_name': 'HeldActor', 'pos_x': x + 690, 'pos_y': y})
    held_comp = add({'type': 'VariableSet', 'variable_name': 'HeldComponent', 'pos_x': x + 930, 'pos_y': y})
    valid = add({'type': 'CallFunction', 'target': 'KismetSystemLibrary', 'function_name': 'IsValid',
                 'pos_x': x + 690, 'pos_y': y + 550})
    holding = add({'type': 'VariableSet', 'variable_name': 'bIsHolding', 'pos_x': x + 1180, 'pos_y': y})
    link(event, 'Pressed', selected, 'execute')
    link(selected, 'then', held, 'execute')
    link(slot, f'TraySlot{i}', held, 'HeldActor')
    link(held, 'then', held_comp, 'execute')
    link(component, f'TraySlot{i}Component', held_comp, 'HeldComponent')
    link(held_comp, 'then', holding, 'execute')
    link(slot, f'TraySlot{i}', valid, 'Object')
    link(valid, 'ReturnValue', holding, 'bIsHolding')

unreal.MCPythonHelper.submit_result(json.dumps({'results': results}, ensure_ascii=False))
