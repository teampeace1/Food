#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "FoodAchievementSaveGame.generated.h"

UCLASS()
class FOODACHIEVEMENTS_API UFoodAchievementSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY(SaveGame)
    TArray<FName> UnlockedIds;
};
