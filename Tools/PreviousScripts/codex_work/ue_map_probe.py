import unreal,json
unreal.EditorLevelLibrary.load_level('/Game/0Input/map/Kitchen_white')
out=[]
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    loc=a.get_actor_location()
    out.append({'name':a.get_name(),'label':a.get_actor_label(),'class':a.get_class().get_name(),'loc':[loc.x,loc.y,loc.z]})
with open(r'C:/Users/38606/Documents/Codex/2026-11-15/wo/work/ue_map_probe.json','w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2)
