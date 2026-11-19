import unreal,json
w=unreal.EditorLevelLibrary.get_pie_worlds(False)[0];p=unreal.GameplayStatics.get_player_character(w,0);ac=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.Actor);st=next(a for a in ac if a.get_class().get_name()=='BP_ChoppingBoard_C');a=p.get_editor_property('HeldActor');st.call_method('PlaceStationItem');sys=unreal.get_default_object(unreal.SystemLibrary)
for i in (1,2,3):sys.call_method('SetObjectPropertyByName',args=(p,'TraySlot'+str(i),a))
st.call_method('TakeStationItem');unreal.MCPythonHelper.submit_result(json.dumps({'item_kept':st.get_editor_property('StationItem')==a,'hand_empty':p.get_editor_property('HeldActor') is None},ensure_ascii=False))
