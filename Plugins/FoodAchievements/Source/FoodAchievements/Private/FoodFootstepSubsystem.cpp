#include "FoodFootstepSubsystem.h"
#include "Components/AudioComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Engine/World.h"

bool UFoodFootstepSubsystem::DoesSupportWorldType(EWorldType::Type Type) const
{ return Type == EWorldType::Game || Type == EWorldType::PIE; }
TStatId UFoodFootstepSubsystem::GetStatId() const
{ RETURN_QUICK_DECLARE_CYCLE_STAT(UFoodFootstepSubsystem, STATGROUP_Tickables); }
void UFoodFootstepSubsystem::StopFootsteps()
{
    if (IsValid(Footsteps)) { Footsteps->Stop(); Footsteps->DestroyComponent(); }
    Footsteps = nullptr;
}
void UFoodFootstepSubsystem::Deinitialize()
{ StopFootsteps(); Super::Deinitialize(); }
void UFoodFootstepSubsystem::Tick(float DeltaTime)
{
    StopFootsteps();
}
