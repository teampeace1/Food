import json
import unreal

bp = unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
report = {'blueprint': str(bp), 'variables': [str(x) for x in unreal.BlueprintEditorLibrary.list_member_variable_names(bp)]}
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_result.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
