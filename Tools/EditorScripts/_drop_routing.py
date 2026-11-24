# -*- coding: utf-8 -*-
"""Drop the interaction-routing function: the bowl and the pie are far enough apart in height
that both can answer the trace, so the mutual-exclusion hack is no longer wanted."""
import io

PATH = "Plugins/FoodAchievements/Source/FoodAchievements/Private/FoodIngredientVisualSubsystem.cpp"

source = io.open(PATH, encoding="utf-8").read()
start = source.index("void UFoodIngredientVisualSubsystem::RefreshInteractionRouting")
end = source.index("void UFoodIngredientVisualSubsystem::SnapPlacedIngredients")
removed = source[start:end]
source = source[:start] + source[end:]
io.open(PATH, "w", encoding="utf-8").write(source)
print("REMOVED %d chars, %d lines" % (len(removed), removed.count("\n")))
