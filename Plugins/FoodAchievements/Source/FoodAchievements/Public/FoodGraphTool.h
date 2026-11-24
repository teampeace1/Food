#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "FoodGraphTool.generated.h"
UCLASS()
class FOODACHIEVEMENTS_API UFoodGraphTool : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Food") static FString InspectPieGraph();
    UFUNCTION(BlueprintCallable, Category="Food") static FString InspectGraph(const FString& AssetPath);
    UFUNCTION(BlueprintCallable, Category="Food|Audio", meta=(DefaultToSelf="Context")) static void PlayChop(AActor* Context);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WireChopAudio();
    UFUNCTION(BlueprintCallable, Category="Food|Audio") static void StartWashAudio(AActor* Context);
    UFUNCTION(BlueprintCallable, Category="Food|Audio") static void StopWashAudio(AActor* Context);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WireWashAudio();
    UFUNCTION(BlueprintCallable, Category="Food|Audio") static void FinishWashAudio(AActor* Context);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WireWashFinishAudio();
    UFUNCTION(BlueprintCallable, Category="Food|Audio") static void PlayTraySwitch(AActor* Context);
    UFUNCTION(BlueprintCallable, Category="Food|Audio") static void PlayRecipeOpen(AActor* Context);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WireCharacterAudio();
    UFUNCTION(BlueprintCallable, Category="Food|Audio") static void PlayCookingCue(AActor* Context, FName Cue);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WirePlanCues(const FString& AssetPath);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WireAdditionalCues(const FString& AssetPath);
    UFUNCTION(BlueprintCallable, Category="Food|Audio") static void SetCookingLoop(AActor* Context, FName Loop, bool bStart);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WireCookingLoops(const FString& AssetPath);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WirePlacementWarnings(const FString& AssetPath);
    UFUNCTION(BlueprintCallable, Category="Food") static FString FinishCueCorrections(const FString& AssetPath);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WireRecipeClose();
    static void SetBackgroundMusic(UWorld* World, bool bEnding);
    static void SetEndingJournalMusic(UWorld* World, bool bJournalVisible);
    static void SetBakingMusic(UWorld* World);
    UFUNCTION(BlueprintCallable, Category="Food") static FString WirePlacementCues(const FString& AssetPath);
    UFUNCTION(BlueprintCallable, Category="Food") static int32 ChangePieToFour();
};
