#pragma once
#include "CoreMinimal.h"
class UWorld;

/** Cooking-session persistence. Separate from achievements and settings. */
namespace FoodProgress
{
    bool HasSave(UWorld* World);
    bool Save(UWorld* World);
    bool Restore(UWorld* World);
    void SetActive(UWorld* World, bool bActive);
    void Tick(UWorld* World, float DeltaSeconds);
}
