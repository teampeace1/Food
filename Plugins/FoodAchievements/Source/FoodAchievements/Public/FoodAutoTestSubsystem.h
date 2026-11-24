#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "FoodAutoTestSubsystem.generated.h"

/**
 * Scripted self-check for the kitchen scene.
 *
 * Enabled only when the game is launched with -FoodTest on the command line, so it costs
 * nothing during normal play. It drives the running world (spawns ingredients, waits for the
 * gameplay code to react, inspects results) and writes Saved/FoodAutoTest.json, then exits.
 *
 * This exists so regression checks no longer need a human in PIE.
 */
UCLASS()
class FOODACHIEVEMENTS_API UFoodAutoTestSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    struct FCheck
    {
        FString Name;
        bool bPass = false;
        FString Detail;
    };

private:
    bool OnCoreTick(float DeltaTime);
    void RunStep(int32 Step);
    void Baseline();
    void SpawnFishHeads();
    void CheckFishHeads();
    void SpawnFloatingDough();
    void CheckGrounding();
    void DumpCollisions();
    void CheckGeometry();
    void Finish();

    // --- interaction flow (the parts a human normally exercises by pressing E) ---
    void FlowApproachSupply();
    void FlowPressAtSupply();
    void FlowAfterPickup();
    void FlowApproachBowl();
    void FlowPressAtBowl();
    void FlowAfterBowl();
    void FlowProbeBowl();

    // --- achievements: trigger every unlock path, verify it persisted, then restore the save ---
    void AchievementsRun();
    void AchievementsVerify();
    void RestoreAchievementSave();

    // --- -FoodAch: drive the real gameplay chain (rolling, baking) and watch the poller unlock ---
    bool AchTick(float DeltaTime);
    void AchPrepare();
    void AchStartRolling();
    void AchStartBaking();
    void AchSample(const TCHAR* Tag);
    void AchMockMilestones();
    void AchVerify();
    void AchScreenshot(const TCHAR* FileName);
    void AchOpenRecipe();
    void AchPressTab();
    void AchEnsureRecipe();
    void AchOpenJournal();

    /** Teleports the player in front of Target and points the view at TargetPoint. */
    bool Approach(AActor* Target, const FVector& TargetPoint);
    /** Calls the character's own Interact function - exactly what the E key is bound to. */
    bool PressInteract();
    /** What the camera would hit right now, same trace the character uses. */
    AActor* CameraTrace(FVector& OutHitPoint, FString& OutComponent) const;

    AActor* FindSupply(const FString& IngredientName) const;
    AActor* HeldActor() const;
    int32 ReadIntProp(const AActor* Actor, const TCHAR* Name) const;
    bool ReadBoolProp(const AActor* Actor, const TCHAR* Name) const;
    FString DescribeActor(AActor* Actor) const;
    void DumpProps(AActor* Actor, const FString& Tag) const;

    void Check(const FString& Name, bool bPass, const FString& Detail);
    void Report(const FString& Line);

    bool bActive = false;
    bool bAchDiag = false;
    bool bFinished = false;
    float Elapsed = 0.0f;
    double StartRealTime = 0.0;
    int32 NextStep = 0;
    int32 AchStep = 0;
    FTSTicker::FDelegateHandle TickerHandle;

    TWeakObjectPtr<AActor> Pie;
    TWeakObjectPtr<AActor> Bowl;
    TArray<TWeakObjectPtr<AActor>> SpawnedFish;
    TWeakObjectPtr<AActor> SpawnedDough;
    TWeakObjectPtr<AActor> FlowTarget;
    TWeakObjectPtr<AActor> Rolling;
    TWeakObjectPtr<AActor> Oven;
    TWeakObjectPtr<AActor> Board;
    TWeakObjectPtr<AActor> Sink;
    FVector FlowTargetPoint = FVector::ZeroVector;
    FString FlowIngredient;
    FString FlowPickupResult;
    FString FlowBowlResult;

    bool bSaveExisted = false;
    TArray<uint8> SaveBackup;
    TArray<FName> PreexistingUnlocks;
    FVector ExpectedSurface = FVector::ZeroVector;
    float SpawnBottomZ = 0.0f;
    double WorldStartTime = 0.0;

    TArray<FCheck> Checks;
    TArray<FString> Log;
};
