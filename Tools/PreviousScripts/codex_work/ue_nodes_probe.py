import unreal,json
bp=unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
g=unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
alln=list(ed.list_available_nodes([]))
terms=['SelectInt','选择Int','选择整数','Select|','选择|','PrintString','SpawnActor','生成Actor','ActorfromClass','Greater_IntInt','Subtract_IntInt','IsValid','SetActorHiddenInGame','SetVisibility','Stock','GetActorLocation']
out={t:[x for x in alln if t.lower() in x.lower()][:20] for t in terms}
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_nodes_probe.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
