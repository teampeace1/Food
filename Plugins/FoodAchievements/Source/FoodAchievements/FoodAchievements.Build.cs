using UnrealBuildTool;

public class FoodAchievements : ModuleRules
{
    public FoodAchievements(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "UMG", "SlateCore" });
        PrivateDependencyModuleNames.AddRange(new[] { "Slate", "InputCore" });
        if (Target.bBuildEditor) PrivateDependencyModuleNames.AddRange(new[] { "UnrealEd", "BlueprintGraph" });
    }
}
