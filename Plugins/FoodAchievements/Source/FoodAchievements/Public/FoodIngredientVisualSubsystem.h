#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "FoodIngredientVisualSubsystem.generated.h"

class UStaticMesh;
class UStaticMeshComponent;

struct FFoodDropletSet
{
    TWeakObjectPtr<UStaticMesh> SourceMesh;
    TArray<TWeakObjectPtr<UStaticMeshComponent>> Parts;
    TArray<FVector> Origins;
    double StartTime = 0.0;
};

/** Applies the matching food mesh to ingredient actors after their Blueprint name is assigned. */
UCLASS()
class FOODACHIEVEMENTS_API UFoodIngredientVisualSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;

private:
    void RefreshPieHeadSlots(float DeltaTime);
    void UpdateDroplets(AActor* Actor, UStaticMeshComponent* Component, bool bWet);
    TMap<TWeakObjectPtr<AActor>, FFoodDropletSet> DropletSets;

    /**
     * Some blueprints drop ingredients at a height taken from the worktop actor's bounds top
     * (sink 186, rolling station 294) instead of the real surface, so food floats in the air.
     * Trace down under each loose ingredient and settle it onto whatever is beneath.
     */
    void SnapPlacedIngredients(float DeltaTime);

    float SnapTimer = 0.0f;

    /** Actors already logged by the placement fix, keeps the log one line per ingredient. */
    TSet<TWeakObjectPtr<AActor>> ReportedFloat;

    /** Ingredient name -> mesh currently assigned to its supply point in the level (the designer's choice wins). */
    TMap<FString, TWeakObjectPtr<UStaticMesh>> SupplyMeshes;

    /** Ingredient actor -> mesh we already pushed onto it, so the swap happens once per change. */
    TMap<TWeakObjectPtr<AActor>, TWeakObjectPtr<UStaticMesh>> AppliedMeshes;

    /** Actors already reported for having no IngredientName, keeps the log readable. */
    TSet<TWeakObjectPtr<AActor>> ReportedEmpty;

    float SlotRefreshTimer = 0.0f;
};
