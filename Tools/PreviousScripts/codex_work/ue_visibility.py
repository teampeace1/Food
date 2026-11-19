import json
import unreal

bp = unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
h = unreal.MCPythonHelper
made = []

def add(spec):
    r = json.loads(h.add_blueprint_node(bp, 'EventGraph', json.dumps(spec)))
    if not r.get('success'):
        raise RuntimeError(r)
    made.append((r['node_name'], r['node_title']))
    return r['node_name']

def link(a, ap, b, bpin):
    r = json.loads(h.connect_blueprint_pins(bp, 'EventGraph', a, ap, b, bpin))
    if not r.get('success'):
        raise RuntimeError((a, ap, b, bpin, r))

current_valid = 'K2Node_CallFunction_39'
link('K2Node_VariableGet_1', 'HeldActor', current_valid, 'Object')
entries = [
    ('K2Node_InputKey_0', 'K2Node_VariableSet_4', 'K2Node_VariableSet_7',
     'K2Node_VariableGet_5', 'K2Node_CallFunction_18'),
    ('K2Node_InputKey_1', 'K2Node_VariableSet_8', 'K2Node_VariableSet_11',
     'K2Node_VariableGet_7', 'K2Node_CallFunction_23'),
    ('K2Node_InputKey_2', 'K2Node_VariableSet_12', 'K2Node_VariableSet_15',
     'K2Node_VariableGet_9', 'K2Node_CallFunction_26'),
]
for i, (event, selected, holding, slot, slot_valid) in enumerate(entries, 1):
    x = 5200 + (i - 1) * 1800
    pre = add({'type': 'Branch', 'pos_x': x + 100, 'pos_y': 820})
    hide = add({'type': 'CallFunction', 'target': 'Actor', 'function_name': 'SetActorHiddenInGame',
                'pos_x': x + 320, 'pos_y': 680, 'pin_defaults': {'bNewHidden': 'true'}})
    link(event, 'Pressed', pre, 'execute')
    link(current_valid, 'ReturnValue', pre, 'Condition')
    link(pre, 'then', hide, 'execute')
    link('K2Node_VariableGet_1', 'HeldActor', hide, 'self')
    link(hide, 'then', selected, 'execute')
    link(pre, 'else', selected, 'execute')

    post = add({'type': 'Branch', 'pos_x': x + 1380, 'pos_y': 820})
    show = add({'type': 'CallFunction', 'target': 'Actor', 'function_name': 'SetActorHiddenInGame',
                'pos_x': x + 1590, 'pos_y': 800, 'pin_defaults': {'bNewHidden': 'false'}})
    link(holding, 'then', post, 'execute')
    link(slot_valid, 'ReturnValue', post, 'Condition')
    link(post, 'then', show, 'execute')
    link(slot, f'TraySlot{i}', show, 'self')

unreal.MCPythonHelper.submit_result(json.dumps({'made': made}, ensure_ascii=False))
