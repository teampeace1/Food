import unreal, json
unreal.EditorLoadingAndSavingUtils.load_map('/Game/0Input/map/Kitchen_white_final_supply')
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
out=[]
for a in actors:
 if a.get_class().get_name() not in ['BP_Sink_C','BP_FillingBowl_C','BP_Pie_C']: continue
 d={'label':a.get_actor_label(),'class':a.get_class().get_name(),'loc':str(a.get_actor_location()),'components':[]}
 for c in a.get_components_by_class(unreal.SceneComponent):
  row={'name':c.get_name(),'loc':str(c.get_world_location()),'class':c.get_class().get_name()}
  if isinstance(c,unreal.StaticMeshComponent):
   row['mesh']=str(c.get_editor_property('static_mesh')); row['collision']=str(c.get_collision_enabled())
  d['components'].append(row)
 out.append(d)
open(unreal.Paths.project_saved_dir()+'current_diag.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=2))
unreal.SystemLibrary.quit_editor()