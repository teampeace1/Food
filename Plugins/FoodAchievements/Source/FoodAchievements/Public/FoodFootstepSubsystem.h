#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "FoodFootstepSubsystem.generated.h"
class UAudioComponent;
UCLASS()
class FOODACHIEVEMENTS_API UFoodFootstepSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;
    virtual void Tick(float DeltaTime) override;
    virtual void Deinitialize() override;
    virtual TStatId GetStatId() const override;
private:
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Footsteps;
    void StopFootsteps();
};
