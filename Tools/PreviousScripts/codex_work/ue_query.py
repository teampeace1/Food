import json
import unreal
bp = unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
supply = unreal.EditorAssetLibrary.load_asset('/Game/FoodGameplay/BP_IngredientSupply')
unreal.BlueprintEditorLibrary.compile_blueprint(supply)
node = next(n for n in editor.list_all_nodes() if n.get_name() == 'K2Node_CallFunction_15')
pin = next(p for p in node.list_all_pins() if str(p.get_pin_name()) == 'HitActor')
all_nodes = editor.list_available_nodes([pin])
matches = {'count': len(all_nodes), 'first': list(all_nodes[:12]),
           'supply': [x for x in all_nodes if 'Ingredient' in x or '食材' in x][:30],
           'cast': [x for x in all_nodes if 'cast' in x.lower() or '转换' in x][:20]}
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_query_result.json', 'w', encoding='utf-8') as f:
    json.dump({'matches': matches}, f, ensure_ascii=False, indent=2)
