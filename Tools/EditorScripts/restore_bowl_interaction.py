# -*- coding: utf-8 -*-
"""Make the filling bowl interactable again without letting it cover the pie.

Layout recap:
  BP_FillingBowl / Table   - 112x84x141 cube, invisible, spans Z 44..186 and would swallow the pie.
  BP_FillingBowl / Bowl    - the actual bowl cylinder (Z 146..163). This is what should answer the
                             trace while the player carries fillings or a pie base.
  BP_Pie / PieDisc         - the pie itself, sitting on the bowl rim (Z 160..175).
  BP_Pie / HeadMesh1..7    - invisible 100cm cube placeholders, must never block the trace.

Collision is switched at runtime by FoodIngredientVisualSubsystem (held fish head -> pie, anything
else -> bowl). This script only sets the resting state so a freshly loaded level is sane before the
first tick.
"""
import json
import os

import unreal

MAP = "/Game/0Input/map/Kitchen_white_final_supply"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "restore_bowl_interaction.json")

log = []


def note(text):
    log.append(str(text))


def collision_state(component):
    try:
        body = component.get_editor_property("body_instance")
        return str(body.get_editor_property("collision_enabled"))
    except Exception as exc:
        return "unknown(%s)" % exc


def set_collision(component, enabled):
    """Keep a real profile (BlockAllDynamic) so the Visibility channel still blocks the trace.

    Setting `collision_enabled` alone turns the profile into "Custom", which leaves the responses
    hard to reason about; the runtime subsystem flips the enabled flag from here on.
    """
    try:
        component.set_collision_profile_name("BlockAllDynamic")
    except Exception as exc:
        note("  ! set_collision_profile_name failed for %s: %s" % (component.get_name(), exc))
    try:
        component.set_collision_enabled(enabled)
        return True
    except Exception as exc:
        note("  ! set_collision_enabled failed for %s: %s" % (component.get_name(), exc))
    return False


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

    report = {}

    for actor in actors:
        if not isinstance(actor, unreal.Actor):
            continue
        label = actor.get_actor_label()
        cls = actor.get_class().get_name()

        if "FillingBowl" not in cls and "FillingBowl" not in label:
            continue

        rows = []
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            name = component.get_name()
            before = collision_state(component)
            if name == "Table":
                set_collision(component, unreal.CollisionEnabled.NO_COLLISION)
                note("bowl/Table  %s -> NO_COLLISION (it covers the pie)" % before)
            elif name.startswith("Bowl"):
                set_collision(component, unreal.CollisionEnabled.QUERY_ONLY)
                note("bowl/%s  %s -> QUERY_ONLY (accepts fillings / pie base)" % (name, before))
            else:
                continue
            rows.append({"name": name, "before": before, "after": collision_state(component)})
        report.setdefault("bowl", []).extend(rows)

    for actor in actors:
        if not isinstance(actor, unreal.Actor):
            continue
        cls = actor.get_class().get_name()
        if "BP_Pie" not in cls:
            continue

        rows = []
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            name = component.get_name()
            before = collision_state(component)
            if name == "PieDisc":
                set_collision(component, unreal.CollisionEnabled.QUERY_ONLY)
                note("pie/PieDisc  %s -> QUERY_ONLY (accepts fish heads)" % before)
            elif name.startswith("HeadMesh"):
                set_collision(component, unreal.CollisionEnabled.NO_COLLISION)
                note("pie/%s  %s -> NO_COLLISION" % (name, before))
            else:
                continue
            rows.append({"name": name, "before": before, "after": collision_state(component)})
        report.setdefault("pie", []).extend(rows)

    for key in ("bowl", "pie"):
        for row in report.get(key, []):
            if row["before"] == row["after"]:
                note("  (unchanged) %s %s = %s" % (key, row["name"], row["after"]))

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
    note("saved %s" % MAP)

    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump({"log": log, "report": report}, handle, ensure_ascii=False, indent=1)
    unreal.log_warning("RESTORE_BOWL_OK")


main()
