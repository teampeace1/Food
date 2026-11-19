import unreal, json
bp=unreal.EditorAssetLibrary.load_asset('/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter')
g=unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed=unreal.BlueprintGraphEditor.get_graph_editor(g)
out=[]
for n in ed.list_all_nodes():
    if n.get_node_pos().x < 1500: continue
    pins=[]
    for p in n.list_all_pins():
        pins.append({'name':str(p.get_pin_name()),'value':str(p.get_pin_value()),'links':[str(q.get_owning_node().get_name())+'.'+str(q.get_pin_name()) for q in p.list_connected_pins()]})
    out.append({'name':n.get_name(),'title':str(n.get_node_title()),'x':n.get_node_pos().x,'y':n.get_node_pos().y,'pins':pins})
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_graph_dump.json','w',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
