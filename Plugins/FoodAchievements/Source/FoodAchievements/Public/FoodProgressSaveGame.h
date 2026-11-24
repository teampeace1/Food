#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "FoodProgressSaveGame.generated.h"

/** A reference into the recorded actor set, optionally to one of its components. */
USTRUCT()
struct FFoodSavedReference
{
    GENERATED_BODY()

    UPROPERTY(SaveGame) FString ActorId;
    UPROPERTY(SaveGame) FString ComponentName;
};

/** One gameplay actor. Values and links are restored separately, after all actors exist. */
USTRUCT()
struct FFoodSavedActor
{
    GENERATED_BODY()

    UPROPERTY(SaveGame) FString ActorId;
    UPROPERTY(SaveGame) FString ClassPath;
    UPROPERTY(SaveGame) bool bRuntimeSpawned = false;
    UPROPERTY(SaveGame) FTransform Transform = FTransform::Identity;
    UPROPERTY(SaveGame) FVector LinearVelocity = FVector::ZeroVector;
    UPROPERTY(SaveGame) bool bSimulatingPhysics = false;
    UPROPERTY(SaveGame) bool bActorHidden = false;
    UPROPERTY(SaveGame) bool bActorCollisionEnabled = true;
    UPROPERTY(SaveGame) FFoodSavedReference AttachParent;
    UPROPERTY(SaveGame) FName AttachSocket;
    UPROPERTY(SaveGame) FTransform RelativeTransform = FTransform::Identity;
    UPROPERTY(SaveGame) TMap<FString, FString> Values;
    UPROPERTY(SaveGame) TMap<FString, FFoodSavedReference> References;
    UPROPERTY(SaveGame) TMap<FString, FTransform> ComponentTransforms;
    UPROPERTY(SaveGame) TMap<FString, bool> ComponentVisibility;
    UPROPERTY(SaveGame) TMap<FString, int32> ComponentCollision;
};

/** Single cooking-session slot. Achievements and audio settings have separate storage. */
UCLASS()
class FOODACHIEVEMENTS_API UFoodProgressSaveGame : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY(SaveGame) int32 FormatVersion = 1;
    UPROPERTY(SaveGame) FString LevelPackage;
    UPROPERTY(SaveGame) FDateTime SavedAtUtc;
    UPROPERTY(SaveGame) FRotator PlayerViewRotation = FRotator::ZeroRotator;
    UPROPERTY(SaveGame) bool bEndingSeen = false;
    UPROPERTY(SaveGame) TArray<FFoodSavedActor> Actors;
};
