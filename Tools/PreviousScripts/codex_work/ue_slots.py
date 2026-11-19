import json
import unreal

bp = unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
h = unreal.MCPythonHelper
created = []

def add(spec):
    r = json.loads(h.add_blueprint_node(bp, 'EventGraph', json.dumps(spec)))
    if not r.get('success'):
        raise RuntimeError(r)
    created.append((r['node_name'], r['node_title']))
    return r['node_name']

def link(a, ap, b, bpin):
    r = json.loads(h.connect_blueprint_pins(bp, 'EventGraph', a, ap, b, bpin))
    if not r.get('success'):
        raise RuntimeError((a, ap, b, bpin, r))

def route(start_node, start_pin, selected_get, source_actor, source_component, clear, y):
    previous = (start_node, start_pin)
    for i in (1, 2, 3):
        x = 7600 + (i - 1) * 780
        if i < 3:
            eq = add({'type': 'CallFunction', 'target': 'KismetMathLibrary',
                      'function_name': 'EqualEqual_IntInt', 'pos_x': x, 'pos_y': y + 240,
                      'pin_defaults': {'B': str(i)}})
            link(selected_get, 'SelectedSlot', eq, 'A')
        branch = add({'type': 'Branch', 'pos_x': x + 220, 'pos_y': y})
        link(previous[0], previous[1], branch, 'execute')
        if i < 3:
            link(eq, 'ReturnValue', branch, 'Condition')
        else:
            # The remaining valid selection is slot 3.
            link(selected_get, 'SelectedSlot', eq3, 'A')
            link(eq3, 'ReturnValue', branch, 'Condition')
        set_actor = add({'type': 'VariableSet', 'variable_name': f'TraySlot{i}',
                         'pos_x': x + 430, 'pos_y': y})
        set_component = add({'type': 'VariableSet', 'variable_name': f'TraySlot{i}Component',
                             'pos_x': x + 650, 'pos_y': y})
        link(branch, 'then', set_actor, 'execute')
        link(set_actor, 'then', set_component, 'execute')
        if not clear:
            link(source_actor, 'HitActor', set_actor, f'TraySlot{i}')
            link(source_component, 'HitComponent', set_component, f'TraySlot{i}Component')
        previous = (branch, 'else')

eq3 = add({'type': 'CallFunction', 'target': 'KismetMathLibrary',
           'function_name': 'EqualEqual_IntInt', 'pos_x': 9100, 'pos_y': 1600,
           'pin_defaults': {'B': '3'}})
pickup_selected = add({'type': 'VariableGet', 'variable_name': 'SelectedSlot',
                       'pos_x': 7410, 'pos_y': 1430})
route('K2Node_VariableSet_2', 'then', pickup_selected,
      'K2Node_CallFunction_15', 'K2Node_CallFunction_15', False, 1200)

eq3_drop = add({'type': 'CallFunction', 'target': 'KismetMathLibrary',
                'function_name': 'EqualEqual_IntInt', 'pos_x': 9100, 'pos_y': 2300,
                'pin_defaults': {'B': '3'}})
eq3 = eq3_drop
drop_selected = add({'type': 'VariableGet', 'variable_name': 'SelectedSlot',
                     'pos_x': 7410, 'pos_y': 2130})
route('K2Node_VariableSet_3', 'then', drop_selected, None, None, True, 1900)

unreal.MCPythonHelper.submit_result(json.dumps({'created': created}, ensure_ascii=False))
