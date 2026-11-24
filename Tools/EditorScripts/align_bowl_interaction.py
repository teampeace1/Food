import unreal
path='/Game/0Input/map/Kitchen_white_final_supply'
world=unreal.EditorLoadingAndSavingUtils.load_map(path)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
pie=next(a for a in actors if a.get_class().get_name()=='BP_Pie_C')
bowl=next(a for a in actors if a.get_class().get_name()=='BP_FillingBowl_C')
p=pie.get_actor_location()
comp=next(c for c in bowl.get_components_by_class(unreal.StaticMeshComponent) if c.get_name()=='Bowl')
comp.set_world_location(unreal.Vector(p.x,p.y,p.z-12.0),False,False)
unreal.EditorLoadingAndSavingUtils.save_map(world,path)
unreal.log_warning('BOWL_ALIGNMENT_SAVED '+str(comp.get_world_location()))
unreal.SystemLibrary.quit_editor()