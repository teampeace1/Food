import unreal,json,traceback
out={}
try:
 worlds=unreal.EditorLevelLibrary.get_pie_worlds(False);out['worlds']=[str(x) for x in worlds]
 world=worlds[0];player=unreal.GameplayStatics.get_player_character(world,0)
 out['player']=str(player)
 sys=unreal.get_default_object(unreal.SystemLibrary)
 before=player.get_editor_property('HeldActor')
 sys.call_method('SetObjectPropertyByName',args=(player,'HeldActor',before))
 out['setter']='works'
 out['actors']=[(a.get_name(),a.get_class().get_name()) for a in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor) if 'Ingredient' in a.get_class().get_name() or 'Station' in a.get_class().get_name() or 'Chopping' in a.get_class().get_name()]
except Exception:out['error']=traceback.format_exc()
unreal.MCPythonHelper.submit_result(json.dumps(out,ensure_ascii=False))
