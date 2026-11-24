#include "FoodIngredientVisualSubsystem.h"

#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/UObjectGlobals.h"
#include "UObject/UnrealType.h"

namespace
{
/** Last-resort table, only used when the level gives us nothing to copy from. */
const TCHAR* DefaultMeshForIngredient(const FString& Name)
{
    if (Name == TEXT("欧芹")) return TEXT("/Game/modularkitchen/modular-kitchen/kitchen/props/parsley.parsley");
    if (Name == TEXT("洋葱")) return TEXT("/Game/modularkitchen/modular-kitchen/kitchen/props/onion.onion");
    if (Name == TEXT("调料")) return TEXT("/Game/modularkitchen/modular-kitchen/kitchen/props/condiment-bottle.condiment-bottle");
    if (Name == TEXT("面团")) return TEXT("/Game/modularkitchen/modular-kitchen/kitchen/props/sourdough.sourdough");
    if (Name == TEXT("鱼头")) return TEXT("/Game/Food/Meshes/SM_Sardine_Half_1.SM_Sardine_Half_1");
    if (Name == TEXT("鱼")) return TEXT("/Game/Food/Meshes/SM_Sardine.SM_Sardine");
    return nullptr;
}

FString ReadIngredientName(const AActor* Actor)
{
    if (!Actor) return FString();
    const FProperty* Property = Actor->GetClass()->FindPropertyByName(TEXT("IngredientName"));
    if (const FStrProperty* StringProperty = CastField<FStrProperty>(Property))
    {
        return StringProperty->GetPropertyValue_InContainer(Actor);
    }
    if (const FNameProperty* NameProperty = CastField<FNameProperty>(Property))
    {
        return NameProperty->GetPropertyValue_InContainer(Actor).ToString();
    }
    if (const FTextProperty* TextProperty = CastField<FTextProperty>(Property))
    {
        return TextProperty->GetPropertyValue_InContainer(Actor).ToString();
    }
    return FString();
}

UStaticMesh* ReadActorMesh(const AActor* Actor)
{
    if (!Actor) return nullptr;
    if (const UStaticMeshComponent* Component = Actor->FindComponentByClass<UStaticMeshComponent>())
    {
        return Component->GetStaticMesh();
    }
    return nullptr;
}

/** Engine primitives (Cube/Sphere/...) mean "nobody picked a model here yet". */
bool IsPlaceholderMesh(const UStaticMesh* Mesh)
{
    if (!Mesh) return true;
    return Mesh->GetPathName().StartsWith(TEXT("/Engine/BasicShapes/"));
}

void SetMeshVariable(AActor* Actor, const FName PropertyName, UStaticMesh* Mesh)
{
    FProperty* Property = Actor->GetClass()->FindPropertyByName(PropertyName);
    if (FObjectPropertyBase* ObjectProperty = CastField<FObjectPropertyBase>(Property))
    {
        ObjectProperty->SetObjectPropertyValue_InContainer(Actor, Mesh);
    }
}

UStaticMesh* CutMeshFor(const FString& Name)
{
    const TCHAR* Path = nullptr;
    if (Name == TEXT("洋葱")) Path = TEXT("/Game/Food/Meshes/Prepared/SM_Onion_Chopped.SM_Onion_Chopped");
    else if (Name == TEXT("欧芹")) Path = TEXT("/Game/Food/Meshes/Prepared/SM_Parsley_Chopped.SM_Parsley_Chopped");
    else if (Name == TEXT("鱼")) Path = TEXT("/Game/Food/Meshes/SM_Sardine_Half_2.SM_Sardine_Half_2");
    return Path ? LoadObject<UStaticMesh>(nullptr, Path) : nullptr;
}

FString ReadState(const AActor* Actor)
{
    const FStrProperty* Property = FindFProperty<FStrProperty>(Actor->GetClass(), TEXT("State"));
    return Property ? Property->GetPropertyValue_InContainer(Actor) : FString();
}

float HandScaleFor(const UStaticMesh* Mesh)
{
    if (!Mesh) return 1.0f;
    const float LargestDimension = Mesh->GetBounds().BoxExtent.GetMax() * 2.0f;
    if (LargestDimension <= KINDA_SMALL_NUMBER) return 1.0f;
    // A held ingredient should be roughly hand sized, regardless of import units.
    const float DesiredSize = FMath::Clamp(LargestDimension, 8.0f, 35.0f);
    return DesiredSize / LargestDimension;
}
}

bool UFoodIngredientVisualSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
    const UWorld* World = Cast<UWorld>(Outer);
    return World && World->IsGameWorld();
}

void UFoodIngredientVisualSubsystem::Tick(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World) return;

    // Pass 1: remember the mesh the level currently shows for every supply point.
    // Whatever the level designer puts on "供应点_面团" is what the player should hold.
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        AStaticMeshActor* Supply = *It;
        if (!IsValid(Supply) || !Supply->GetClass()->GetName().Contains(TEXT("BP_IngredientSupply")))
        {
            continue;
        }

        const FString Name = ReadIngredientName(Supply);
        if (Name.IsEmpty()) continue;

        UStaticMesh* Mesh = ReadActorMesh(Supply);
        if (IsPlaceholderMesh(Mesh))
        {
            // The placed actor still uses the engine cube, so fall back to the Blueprint default.
            Mesh = ReadActorMesh(Cast<AActor>(Supply->GetClass()->GetDefaultObject()));
        }
        if (IsPlaceholderMesh(Mesh)) continue;

        SupplyMeshes.Add(Name, Mesh);
    }

    // Pass 2: push that mesh onto the ingredient actors the player picks up / spawns.
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        AStaticMeshActor* Actor = *It;
        if (!IsValid(Actor) || Actor->GetClass()->GetName() != TEXT("BP_Ingredient_C"))
        {
            continue;
        }

        const FString Name = ReadIngredientName(Actor);
        if (Name.IsEmpty())
        {
            // IngredientName is filled in after SpawnActor, but some spawn paths never set it - log once so it shows up.
            if (!ReportedEmpty.Contains(Actor))
            {
                ReportedEmpty.Add(Actor);
                const UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
                const UStaticMesh* CurrentMesh = Component ? Component->GetStaticMesh() : nullptr;
                UE_LOG(LogTemp, Warning, TEXT("[IngredientVisual] %s (%s) has empty IngredientName | mesh=%s | parent=%s"),
                    *Actor->GetName(),
                    *Actor->GetClass()->GetName(),
                    CurrentMesh ? *CurrentMesh->GetPathName() : TEXT("none"),
                    Actor->GetAttachParentActor() ? *Actor->GetAttachParentActor()->GetName() : TEXT("none"));
            }
            continue;
        }

        UStaticMesh* Target = nullptr;
        if (const TWeakObjectPtr<UStaticMesh>* Learned = SupplyMeshes.Find(Name))
        {
            Target = Learned->Get();
        }
        if (!Target)
        {
            UStaticMesh* Current = ReadActorMesh(Actor);
            if (!IsPlaceholderMesh(Current))
            {
                Target = Current; // The Blueprint already points at a real model, respect it.
            }
            else if (const TCHAR* Path = DefaultMeshForIngredient(Name))
            {
                Target = LoadObject<UStaticMesh>(nullptr, Path);
            }
        }
        if (!Target) continue;

        if (AppliedMeshes.FindRef(Actor).Get() != Target)
        {
            SetMeshVariable(Actor, TEXT("MeshRaw"), Target);
            SetMeshVariable(Actor, TEXT("MeshWashed"), Target);
            SetMeshVariable(Actor, TEXT("MeshCut"), CutMeshFor(Name) ? CutMeshFor(Name) : Target);
            SetMeshVariable(Actor, TEXT("MeshPieBase"), Target);

            if (UStaticMeshComponent* Component = Actor->GetStaticMeshComponent())
            {
                const UStaticMesh* Before = Component->GetStaticMesh();
                Component->SetStaticMesh(Target);
                Component->SetRelativeScale3D(FVector(HandScaleFor(Target)));
                UE_LOG(LogTemp, Warning, TEXT("[IngredientVisual] %s name='%s' %s -> %s (was %s)"),
                    *Actor->GetName(), *Name, *Actor->GetClass()->GetName(), *Target->GetName(),
                    Before ? *Before->GetName() : TEXT("none"));
            }
            AppliedMeshes.Add(Actor, Target);
        }

        // RefreshLook in the Blueprint applies placeholder tint materials. Restore the
        // mesh materials only when that placeholder is present; keep other overrides.
        if ((Name == TEXT("洋葱") || Name == TEXT("欧芹") || Name == TEXT("鱼") || Name == TEXT("鱼头")))
        if (UStaticMeshComponent* Component = Actor->GetStaticMeshComponent())
        {
            const bool bCut = ReadState(Actor) == TEXT("Cut");
            UStaticMesh* CutMesh = CutMeshFor(Name);
            UStaticMesh* Desired = bCut && CutMesh ? CutMesh : Target;
            if (Component->GetStaticMesh() != Desired)
            {
                Component->SetStaticMesh(Desired);
            }
            const float Size = Desired->GetBounds().BoxExtent.GetMax() * 2.0f;
            const float Scale = bCut && CutMesh && (Name == TEXT("洋葱") || Name == TEXT("欧芹")) && Size > KINDA_SMALL_NUMBER
                ? 12.0f / Size : HandScaleFor(Desired);
            Component->SetRelativeScale3D(FVector(Scale));
            const FBoolProperty* WashedProp = FindFProperty<FBoolProperty>(Actor->GetClass(), TEXT("bWashed"));
            const bool bWet = WashedProp && WashedProp->GetPropertyValue_InContainer(Actor);
            UpdateDroplets(Actor, Component, bWet);
            UMaterialInterface* WetMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Food/Meshes/Prepared/M_WetOverlay.M_WetOverlay"));
            if (bWet && WetMaterial && Component->GetOverlayMaterial() != WetMaterial)
                Component->SetOverlayMaterial(WetMaterial);
            else if (!bWet && Component->GetOverlayMaterial() == WetMaterial && WetMaterial)
                Component->SetOverlayMaterial(nullptr);
            for (int32 Index = 0; Index < Component->GetNumMaterials(); ++Index)
            {
                UMaterialInterface* Material = Component->GetMaterial(Index);
                if (Material && Material->GetPathName().StartsWith(TEXT("/Game/FoodGameplay/MI_Tint")))
                    Component->SetMaterial(Index, nullptr);
            }
        }
    }

    for (auto It = DropletSets.CreateIterator(); It; ++It)
        if (!It.Key().IsValid()) It.RemoveCurrent();

    if (AppliedMeshes.Num() > 64)
    {
        for (auto It = AppliedMeshes.CreateIterator(); It; ++It)
        {
            if (!It.Key().IsValid() || !It.Value().IsValid())
            {
                It.RemoveCurrent();
            }
        }
    }

    RefreshPieHeadSlots(DeltaTime);
    SnapPlacedIngredients(DeltaTime);
}

void UFoodIngredientVisualSubsystem::UpdateDroplets(AActor* Actor, UStaticMeshComponent* Component, bool bWet)
{
    UStaticMesh* Mesh = Component->GetStaticMesh();
    FFoodDropletSet* Existing = DropletSets.Find(Actor);
    if (Existing && (!bWet || Existing->SourceMesh.Get() != Mesh))
    {
        for (auto& Part : Existing->Parts) if (Part.IsValid()) Part->DestroyComponent();
        DropletSets.Remove(Actor);
        Existing = nullptr;
    }
    if (!bWet || !Mesh) return;
    if (!Existing)
    {
        FStaticMeshRenderData* Data = Mesh->GetRenderData();
        if (!Data || Data->LODResources.IsEmpty()) return;
        const FPositionVertexBuffer& Vertices = Data->LODResources[0].VertexBuffers.PositionVertexBuffer;
        if (!Vertices.GetVertexData() || Vertices.GetNumVertices() < 3) return;
        UStaticMesh* Sphere = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere"));
        UMaterialInterface* Water = LoadObject<UMaterialInterface>(nullptr, TEXT("/Game/Food/Meshes/Prepared/M_WaterDroplet.M_WaterDroplet"));
        if (!Sphere || !Water) return;
        FFoodDropletSet& Set = DropletSets.Add(Actor);
        Set.SourceMesh = Mesh;
        Set.StartTime = GetWorld()->GetTimeSeconds();
        FRandomStream Random(GetTypeHash(Actor->GetFName()));
        const float ComponentScale = FMath::Max(Component->GetComponentScale().GetAbsMax(), 0.00001f);
        const float LocalRadiusScale = 0.0035f / ComponentScale;
        for (int32 Index = 0; Index < 23; ++Index)
        {
            const uint32 VertexIndex = Random.RandRange(0, static_cast<int32>(Vertices.GetNumVertices()) - 1);
            const FVector Position(Vertices.VertexPosition(VertexIndex));
            UStaticMeshComponent* Drop = NewObject<UStaticMeshComponent>(Actor);
            if (!Drop) continue;
            Drop->SetStaticMesh(Sphere);
            Drop->SetMaterial(0, Water);
            Drop->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Drop->SetCastShadow(false);
            Drop->SetupAttachment(Component);
            Drop->RegisterComponent();
            Drop->SetRelativeLocation(Position);
            const float Variation = Random.FRandRange(0.7f, 1.25f);
            Drop->SetRelativeScale3D(FVector(LocalRadiusScale * Variation));
            Set.Parts.Add(Drop);
            Set.Origins.Add(Position);
        }
        Existing = &Set;
    }
    const double Age = GetWorld()->GetTimeSeconds() - Existing->StartTime;
    for (int32 Index = 0; Index < Existing->Parts.Num(); ++Index)
    {
        UStaticMeshComponent* Drop = Existing->Parts[Index].Get();
        if (!Drop || Index < 11) continue;
        const bool bFalling = true;
        Drop->SetVisibility(bFalling);
        if (bFalling)
        {
            const float Phase = FMath::Fmod(static_cast<float>(Age) + Index * 0.37f, 1.5f) / 1.5f;
            const FVector WorldFall(0, 0, -8.0f * Phase * Phase);
            Drop->SetRelativeLocation(Existing->Origins[Index] + Component->GetComponentTransform().InverseTransformVector(WorldFall));
        }
    }
}

void UFoodIngredientVisualSubsystem::RefreshPieHeadSlots(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World) return;

    // Slots only change when something is placed, no need to scan every frame.
    SlotRefreshTimer += DeltaTime;
    if (SlotRefreshTimer < 0.2f) return;
    SlotRefreshTimer = 0.0f;

    const APawn* Pawn = UGameplayStatics::GetPlayerPawn(World, 0);

    // Collect every ingredient lying around (not carried) that already shows a real mesh.
    // Matching by slot component name was unreliable - the placement path does not always attach
    // to HeadPoint* - so the pie slots below are matched by proximity instead.
    struct FPlacedIngredient
    {
        FVector Location = FVector::ZeroVector;
        UStaticMesh* Mesh = nullptr;
        FString Name;
    };
    TArray<FPlacedIngredient> Placed;

    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        AStaticMeshActor* Ingredient = *It;
        if (!IsValid(Ingredient) || Ingredient->GetClass()->GetName() != TEXT("BP_Ingredient_C")) continue;

        bool bHeld = false;
        for (AActor* Parent = Ingredient->GetAttachParentActor(); Parent; Parent = Parent->GetAttachParentActor())
        {
            if (Parent == Pawn)
            {
                bHeld = true;
                break;
            }
        }
        if (bHeld) continue;

        FPlacedIngredient Sample;
        Sample.Location = Ingredient->GetActorLocation();
        Sample.Mesh = ReadActorMesh(Ingredient);
        Sample.Name = ReadIngredientName(Ingredient);

        if (IsPlaceholderMesh(Sample.Mesh))
        {
            // Still the engine cube: fall back to whatever the supply point for this name shows.
            if (const TWeakObjectPtr<UStaticMesh>* Learned = SupplyMeshes.Find(Sample.Name))
            {
                Sample.Mesh = Learned->Get();
            }
        }
        if (IsPlaceholderMesh(Sample.Mesh)) continue;

        Placed.Add(Sample);
    }



    // BP_Pie only toggles visibility of its HeadMesh placeholders - the mesh itself stays the engine
    // cube, which is the grey box the player sees in the pie. Copy the nearest ingredient mesh in.
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Pie = *It;
        if (!IsValid(Pie) || !Pie->GetClass()->GetName().Contains(TEXT("BP_Pie_C"))) continue;

        // Reproduce the finished reference pie assembled in the kitchen display.
        const FIntProperty* CountProp = FindFProperty<FIntProperty>(Pie->GetClass(), TEXT("HeadsPlaced"));
        if (CountProp && CountProp->GetPropertyValue_InContainer(Pie) > 0)
        {
            UStaticMeshComponent* Disc = nullptr;
            TArray<UStaticMeshComponent*> Slots;
            for (UActorComponent* Part : Pie->GetComponents())
            {
                UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Part);
                if (!Mesh) continue;
                if (Mesh->GetName() == TEXT("PieDisc")) Disc = Mesh;
                if (Mesh->GetName().StartsWith(TEXT("HeadMesh"))) Slots.Add(Mesh);
            }
            AStaticMeshActor* ReferencePie = nullptr;
            const FVector ReferencePosition(1480.16, 2609.49, 170.77);
            for (TActorIterator<AStaticMeshActor> RefIt(World); RefIt; ++RefIt)
            {
                AStaticMeshActor* Ref = *RefIt;
                UStaticMesh* Mesh = ReadActorMesh(Ref);
                if (Ref->GetClass() == AStaticMeshActor::StaticClass() && Mesh &&
                    Mesh->GetName() == TEXT("SM_Pie") && FVector::Dist(Ref->GetActorLocation(), ReferencePosition) < 30.0f)
                { ReferencePie = Ref; break; }
            }
            TArray<AStaticMeshActor*> Heads;
            if (ReferencePie)
            {
                for (TActorIterator<AStaticMeshActor> RefIt(World); RefIt; ++RefIt)
                {
                    AStaticMeshActor* Ref = *RefIt;
                    UStaticMesh* Mesh = ReadActorMesh(Ref);
                    if (Ref->GetClass() != AStaticMeshActor::StaticClass() || !Mesh ||
                        Mesh->GetName() != TEXT("SM_Sardine_Half_1") ||
                        FVector::Dist2D(Ref->GetActorLocation(), ReferencePie->GetActorLocation()) > 16.0f ||
                        FMath::Abs(Ref->GetActorLocation().Z - ReferencePie->GetActorLocation().Z) > 20.0f) continue;
                    bool bDuplicate = false;
                    for (AStaticMeshActor* Existing : Heads)
                        if (FVector::Dist(Existing->GetActorLocation(), Ref->GetActorLocation()) < 1.0f) bDuplicate = true;
                    if (!bDuplicate) Heads.Add(Ref);
                }
            }
            if (Disc && ReferencePie && Heads.Num() == 4 && Slots.Num() >= 4)
            {
                Disc->SetStaticMesh(ReadActorMesh(ReferencePie));
                for (int32 Index = 0; Index < Slots.Num(); ++Index)
                {
                    UStaticMeshComponent* Slot = Slots[Index];
                    const bool bShow = Index < FMath::Min(CountProp->GetPropertyValue_InContainer(Pie), Heads.Num());
                    Slot->SetVisibility(bShow);
                    if (!bShow) continue;
                    UStaticMeshComponent* RefHead = Heads[Index]->GetStaticMeshComponent();
                    Slot->SetStaticMesh(RefHead->GetStaticMesh());
                    const FTransform Relative = RefHead->GetComponentTransform().GetRelativeTransform(ReferencePie->GetStaticMeshComponent()->GetComponentTransform());
                    Slot->SetWorldTransform(Relative * Disc->GetComponentTransform());
                }
                continue;
            }
        }
        for (UActorComponent* RawComponent : Pie->GetComponents())
        {
            UStaticMeshComponent* Head = Cast<UStaticMeshComponent>(RawComponent);
            if (!Head || !Head->GetName().StartsWith(TEXT("HeadMesh"))) continue;
            if (!IsPlaceholderMesh(Head->GetStaticMesh())) continue;

            const FVector HeadLocation = Head->GetComponentLocation();
            const FPlacedIngredient* Nearest = nullptr;
            float NearestDistance = 45.0f;

            for (const FPlacedIngredient& Sample : Placed)
            {
                const float Distance = FVector::Dist(Sample.Location, HeadLocation);
                if (Distance < NearestDistance)
                {
                    NearestDistance = Distance;
                    Nearest = &Sample;
                }
            }
            UStaticMesh* HeadMesh = Nearest && Nearest->Name == TEXT("鱼头") ? Nearest->Mesh : nullptr;
            if (!HeadMesh)
            {
                HeadMesh = LoadObject<UStaticMesh>(nullptr, DefaultMeshForIngredient(TEXT("鱼头")));
            }
            if (!HeadMesh) continue;
            Head->SetStaticMesh(HeadMesh);
            Head->SetRelativeScale3D(FVector(HandScaleFor(HeadMesh)));
        }
    }
}

void UFoodIngredientVisualSubsystem::SnapPlacedIngredients(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World) return;

    SnapTimer += DeltaTime;
    if (SnapTimer < 0.2f) return;
    SnapTimer = 0.0f;

    const APawn* Pawn = UGameplayStatics::GetPlayerPawn(World, 0);

    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        AStaticMeshActor* Actor = *It;
        if (!IsValid(Actor) || Actor->GetClass()->GetName() != TEXT("BP_Ingredient_C")) continue;

        // Carried by the player? Then the hand owns its position.
        bool bHeldByPlayer = false;
        for (AActor* Parent = Actor->GetAttachParentActor(); Parent; Parent = Parent->GetAttachParentActor())
        {
            if (Parent == Pawn)
            {
                bHeldByPlayer = true;
                break;
            }
        }
        if (bHeldByPlayer) continue;

        // Already slotted into the pie: the pie decides where it sits.
        USceneComponent* Root = Actor->GetRootComponent();
        if (Root && Root->GetAttachParent() && Root->GetAttachParent()->GetName().StartsWith(TEXT("HeadPoint")))
        {
            continue;
        }

        const FBox Bounds = Actor->GetComponentsBoundingBox(true);
        if (!Bounds.IsValid) continue;

        // At the stream, the sink's hidden basin collision is above the visible bottom.
        // Use the existing splash position as the water landing height, without moving water.
        bool bSettledAtSink = false;
        for (TActorIterator<AActor> SinkIt(World); SinkIt; ++SinkIt)
        {
            AActor* SinkActor = *SinkIt;
            if (!SinkActor->GetClass()->GetName().StartsWith(TEXT("BP_Sink_C"))) continue;
            for (UActorComponent* Part : SinkActor->GetComponents())
            {
                USceneComponent* Splash = Cast<USceneComponent>(Part);
                if (!Splash || Splash->GetName() != TEXT("SplashFoam")) continue;
                const FVector Water = Splash->GetComponentLocation();
                const FVector Center = Bounds.GetCenter();
                const float Gap = Bounds.Min.Z - Water.Z;
                if (FVector::Dist2D(Center, Water) > 22.0f || Gap < 1.0f || Gap > 80.0f) continue;
                const FVector Delta(0.0f, 0.0f, -Gap + 0.5f);
                if (Root && Root->GetAttachParent())
                    Root->AddLocalOffset(Root->GetAttachParent()->GetComponentTransform().InverseTransformVector(Delta));
                else
                    Actor->AddActorWorldOffset(Delta, false, nullptr, ETeleportType::TeleportPhysics);
                bSettledAtSink = true;
                break;
            }
            if (bSettledAtSink) break;
        }
        if (bSettledAtSink) continue;
        const FVector Center = Bounds.GetCenter();
        FCollisionQueryParams Params(SCENE_QUERY_STAT(SnapPlacedIngredient), false, Actor);
        FHitResult Hit;
        const FVector Start(Center.X, Center.Y, Bounds.Max.Z + 2.0f);
        const FVector End(Center.X, Center.Y, Bounds.Min.Z - 150.0f);
        if (!World->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params)) continue;

        const float Gap = Bounds.Min.Z - Hit.ImpactPoint.Z;
        if (Gap < 0.5f) continue; // resting on the surface (or slightly sunk) - leave it

        if (!ReportedFloat.Contains(Actor))
        {
            ReportedFloat.Add(Actor);
            UE_LOG(LogTemp, Warning, TEXT("[Placement] %s '%s' floats %.1fcm above Z=%.1f (bottom %.1f)"),
                *Actor->GetName(), *ReadIngredientName(Actor), Gap, Hit.ImpactPoint.Z, Bounds.Min.Z);
        }

        if (Gap > 150.0f) continue; // not a "dropped on a worktop" case, do not yank it down

        const FVector Delta(0.0f, 0.0f, -(Gap - 0.2f));
        if (Root && Root->GetAttachParent())
        {
            // Keep it attached (bowl/board), just move it down inside the parent's space.
            Root->AddLocalOffset(Root->GetAttachParent()->GetComponentTransform().InverseTransformVector(Delta));
        }
        else
        {
            Actor->AddActorWorldOffset(Delta, false, nullptr, ETeleportType::TeleportPhysics);
        }
    }

    if (ReportedFloat.Num() > 128)
    {
        ReportedFloat.Empty();
    }
}

TStatId UFoodIngredientVisualSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(UFoodIngredientVisualSubsystem, STATGROUP_Tickables);
}

