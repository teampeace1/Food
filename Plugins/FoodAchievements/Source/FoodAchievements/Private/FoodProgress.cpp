#include "FoodProgress.h"
#include "FoodProgressSaveGame.h"
#include "FoodAchievementSubsystem.h"
#include "FoodGraphTool.h"
#include "Blueprint/UserWidget.h"
#include "Components/ActorComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UObject/UnrealType.h"

namespace FoodProgress
{
static TWeakObjectPtr<UWorld> ActiveWorld;
static float SaveElapsed = 0.f;
static const TCHAR* Slot(UWorld* W) { if(FParse::Param(FCommandLine::Get(),TEXT("FoodTest"))) return TEXT("FoodCooking_AutoTest"); return W && W->WorldType == EWorldType::PIE ? TEXT("FoodCooking_Preview") : TEXT("FoodCooking"); }
static bool IsRelevant(AActor* A)
{
    if (!A) return false;
    const FString N=A->GetClass()->GetName();
    return N==TEXT("BP_FirstPersonCharacter_C") || N==TEXT("BP_Ingredient_C") || N==TEXT("BP_IngredientSupply_C") || N==TEXT("BP_Workstation_C") || N==TEXT("BP_ChoppingBoard_C") || N==TEXT("BP_RollingStation_C") || N==TEXT("BP_Sink_C") || N==TEXT("BP_FillingBowl_C") || N==TEXT("BP_Oven_C") || N==TEXT("BP_Pie_C");
}
static bool Allowed(FName Name)
{
    static const TSet<FName> Names={
      TEXT("IngredientName"),TEXT("Type"),TEXT("State"),TEXT("WashProgress"),TEXT("bWashable"),TEXT("CutCount"),TEXT("bWashed"),TEXT("CutNeeded"),TEXT("RollProgress"),TEXT("RollQuality"),TEXT("HeadCount"),TEXT("DisplayText"),
      TEXT("Stock"),TEXT("PromptLabel"),TEXT("StationItem"),TEXT("RollTarget"),TEXT("bRolling"),TEXT("WashTarget"),TEXT("bRunning"),
      TEXT("HasFish"),TEXT("HasOnion"),TEXT("HasParsley"),TEXT("HasSeasoning"),TEXT("FilledCount"),TEXT("bFillingReady"),TEXT("bPieMade"),TEXT("PieRef"),TEXT("PendingActor"),
      TEXT("Heat"),TEXT("BakeElapsed"),TEXT("bIsBaking"),TEXT("bFinished"),TEXT("BakeQuality"),TEXT("TargetSeconds"),TEXT("bStartSent"),TEXT("BakeSeconds"),TEXT("BakeSecondsReal"),TEXT("bPieLoaded"),
      TEXT("HeadsPlaced"),TEXT("bReadyToBake"),TEXT("bRequireWashedHead"),TEXT("CurrentPoint"),
      TEXT("bIsHolding"),TEXT("HeldActor"),TEXT("HeldComponent"),TEXT("TraySlot1"),TEXT("TraySlot2"),TEXT("TraySlot3"),TEXT("SelectedSlot"),TEXT("TraySlot1Component"),TEXT("TraySlot2Component"),TEXT("TraySlot3Component"),TEXT("ActiveRollingStation"),TEXT("CurrentObjective")};
    return Names.Contains(Name);
}
static FFoodSavedReference Ref(UObject* Object)
{
    FFoodSavedReference R;
    if(AActor* A=Cast<AActor>(Object)){R.ActorId=A->GetName();}
    else if(UActorComponent* C=Cast<UActorComponent>(Object)){if(AActor* Owner=C->GetOwner()){R.ActorId=Owner->GetName();R.ComponentName=C->GetName();}}
    return R;
}
static UObject* Resolve(const FFoodSavedReference& R,const TMap<FString,AActor*>& Actors)
{
    AActor* const* A=Actors.Find(R.ActorId);if(!A||!*A)return nullptr;
    if(R.ComponentName.IsEmpty())return *A;
    TArray<UActorComponent*> Components;(*A)->GetComponents(Components);
    for(UActorComponent* C:Components)if(C && C->GetName()==R.ComponentName)return C;
    return nullptr;
}
bool HasSave(UWorld* World){return World && UGameplayStatics::DoesSaveGameExist(Slot(World),0);}
void SetActive(UWorld* World,bool bActive){ActiveWorld=bActive?World:nullptr;SaveElapsed=0.f;}
bool Save(UWorld* World)
{
    if(!World)return false;
    UFoodProgressSaveGame* Data=Cast<UFoodProgressSaveGame>(UGameplayStatics::CreateSaveGameObject(UFoodProgressSaveGame::StaticClass()));if(!Data)return false;
    Data->LevelPackage=World->GetOutermost()->GetName();Data->SavedAtUtc=FDateTime::UtcNow();
    if(APlayerController* PC=World->GetFirstPlayerController())Data->PlayerViewRotation=PC->GetControlRotation();
    if(UFoodAchievementSubsystem* Achievement=World->GetSubsystem<UFoodAchievementSubsystem>())Data->bEndingSeen=Achievement->HasSessionEnding();
    for(TActorIterator<AActor> It(World);It;++It){AActor* A=*It;if(!IsRelevant(A)||A->IsActorBeingDestroyed())continue;
      FFoodSavedActor R;R.ActorId=A->GetName();R.ClassPath=A->GetClass()->GetPathName();R.bRuntimeSpawned=!A->HasAnyFlags(RF_WasLoaded);R.Transform=A->GetActorTransform();R.bActorHidden=A->IsHidden();R.bActorCollisionEnabled=A->GetActorEnableCollision();
      if(USceneComponent* Root=A->GetRootComponent()){
        if(USceneComponent* Parent=Root->GetAttachParent()){R.AttachParent=Ref(Parent);R.AttachSocket=Root->GetAttachSocketName();R.RelativeTransform=Root->GetRelativeTransform();}
      }
      if(UPrimitiveComponent* P=A->FindComponentByClass<UPrimitiveComponent>()){R.bSimulatingPhysics=P->IsSimulatingPhysics();R.LinearVelocity=P->GetPhysicsLinearVelocity();}
      TArray<USceneComponent*> SceneComponents;A->GetComponents<USceneComponent>(SceneComponents);
      for(USceneComponent* C:SceneComponents) if(C) {
        R.ComponentTransforms.Add(C->GetName(),C->GetRelativeTransform());
        R.ComponentVisibility.Add(C->GetName(),C->IsVisible());
        if(UPrimitiveComponent* P=Cast<UPrimitiveComponent>(C)) R.ComponentCollision.Add(C->GetName(),static_cast<int32>(P->GetCollisionEnabled()));
      }
      for(TFieldIterator<FProperty> PropIt(A->GetClass());PropIt;++PropIt){FProperty* P=*PropIt;if(!Allowed(P->GetFName()))continue;
        void* Value=P->ContainerPtrToValuePtr<void>(A);
        if(FObjectPropertyBase* OP=CastField<FObjectPropertyBase>(P)){UObject* Object=OP->GetObjectPropertyValue(Value);R.References.Add(P->GetName(),Ref(Object));}
        else if(CastField<FNumericProperty>(P)||CastField<FBoolProperty>(P)||CastField<FStrProperty>(P)||CastField<FNameProperty>(P)||CastField<FTextProperty>(P)){FString V;P->ExportTextItem_Direct(V,Value,nullptr,A,PPF_None);R.Values.Add(P->GetName(),V);}
      }
      Data->Actors.Add(MoveTemp(R));
    }
    ACharacter* Player=UGameplayStatics::GetPlayerCharacter(World,0);
    bool bPlayerCaptured=false;for(const FFoodSavedActor& R:Data->Actors)if(Player && R.ActorId==Player->GetName()){bPlayerCaptured=true;break;}
    if(Data->Actors.IsEmpty() || !World->GetFirstPlayerController() || !bPlayerCaptured)return false;
    return UGameplayStatics::SaveGameToSlot(Data,Slot(World),0);
}
bool Restore(UWorld* World)
{
    if(!World)return false;UFoodProgressSaveGame* Data=Cast<UFoodProgressSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot(World),0));if(!Data||Data->FormatVersion!=1||Data->Actors.IsEmpty())return false;
    if(UWorld::RemovePIEPrefix(Data->LevelPackage)!=UWorld::RemovePIEPrefix(World->GetOutermost()->GetName()))return false;
    TMap<FString,AActor*> Actors;for(TActorIterator<AActor> It(World);It;++It)if(IsRelevant(*It))Actors.Add(It->GetName(),*It);
    // Validate all classes and references before changing the running level.
    for(const FFoodSavedActor& R:Data->Actors){if(!LoadClass<AActor>(nullptr,*R.ClassPath))return false;}
    for(const FFoodSavedActor& R:Data->Actors){if(!Actors.Contains(R.ActorId)){
      if(!R.bRuntimeSpawned)return false;UClass* Class=LoadClass<AActor>(nullptr,*R.ClassPath);if(!Class)return false;
      FActorSpawnParameters Params;Params.Name=FName(*R.ActorId);Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
      AActor* A=World->SpawnActor<AActor>(Class,R.Transform,Params);if(!A)return false;Actors.Add(R.ActorId,A);
    }}
    for(const FFoodSavedActor& R:Data->Actors){AActor* A=Actors.FindRef(R.ActorId);if(!A||A->GetClass()->GetPathName()!=R.ClassPath)return false;
      A->SetActorTransform(R.Transform,false,nullptr,ETeleportType::TeleportPhysics);A->SetActorHiddenInGame(R.bActorHidden);A->SetActorEnableCollision(R.bActorCollisionEnabled);
      for(const auto& Entry:R.Values){FProperty* P=A->GetClass()->FindPropertyByName(FName(*Entry.Key));if(P && Allowed(P->GetFName()))P->ImportText_Direct(*Entry.Value,P->ContainerPtrToValuePtr<void>(A),A,PPF_None);}
      for(const auto& Entry:R.References){FObjectPropertyBase* P=CastField<FObjectPropertyBase>(A->GetClass()->FindPropertyByName(FName(*Entry.Key)));if(P && Allowed(P->GetFName()))P->SetObjectPropertyValue_InContainer(A,Resolve(Entry.Value,Actors));}
    }
    for(const FFoodSavedActor& R:Data->Actors){AActor* A=Actors.FindRef(R.ActorId);if(!A)continue;
      USceneComponent* Root=A->GetRootComponent();USceneComponent* Parent=Cast<USceneComponent>(Resolve(R.AttachParent,Actors));
      if(Root&&Parent){Root->AttachToComponent(Parent,FAttachmentTransformRules::KeepRelativeTransform,R.AttachSocket);Root->SetRelativeTransform(R.RelativeTransform);}
      if(UPrimitiveComponent* P=A->FindComponentByClass<UPrimitiveComponent>()){P->SetSimulatePhysics(R.bSimulatingPhysics);if(R.bSimulatingPhysics)P->SetPhysicsLinearVelocity(R.LinearVelocity);}
      TArray<USceneComponent*> SceneComponents;A->GetComponents<USceneComponent>(SceneComponents);
      for(USceneComponent* C:SceneComponents) if(C) {
        if(const FTransform* T=R.ComponentTransforms.Find(C->GetName());T && C!=Root) C->SetRelativeTransform(*T);
        if(const bool* Visible=R.ComponentVisibility.Find(C->GetName())) C->SetVisibility(*Visible,false);
        if(UPrimitiveComponent* P=Cast<UPrimitiveComponent>(C)) if(const int32* Collision=R.ComponentCollision.Find(C->GetName())) {
          if(*Collision>=0 && *Collision<=static_cast<int32>(ECollisionEnabled::QueryAndPhysics)) P->SetCollisionEnabled(static_cast<ECollisionEnabled::Type>(*Collision));
        }
      }
    }
    APlayerController* PC=World->GetFirstPlayerController();
    if(PC)PC->SetControlRotation(Data->PlayerViewRotation);
    // Restore the transient progress panels and looping operation sounds, which cannot be serialized as widgets or audio components.
    for(const FFoodSavedActor& R:Data->Actors){
      AActor* A=Actors.FindRef(R.ActorId);if(!A)continue;const FString N=A->GetClass()->GetName();
      auto Flag=[A](const TCHAR* Key){const FBoolProperty* P=FindFProperty<FBoolProperty>(A->GetClass(),Key);return P && P->GetPropertyValue_InContainer(A);};
      auto RestorePanel=[A,PC](const TCHAR* PropName,const TCHAR* ClassPath){
        if(!PC)return;FObjectPropertyBase* Prop=FindFProperty<FObjectPropertyBase>(A->GetClass(),PropName);if(!Prop || Prop->GetObjectPropertyValue_InContainer(A))return;
        UClass* WidgetClass=LoadClass<UUserWidget>(nullptr,ClassPath);if(!WidgetClass)return;
        if(UUserWidget* Widget=CreateWidget<UUserWidget>(PC,WidgetClass)){Prop->SetObjectPropertyValue_InContainer(A,Widget);Widget->AddToViewport(20);}
      };
      if(N==TEXT("BP_Oven_C") && (Flag(TEXT("bIsBaking")) || Flag(TEXT("bFinished")))) UFoodGraphTool::SetBakingMusic(World);
      if(N==TEXT("BP_Oven_C") && Flag(TEXT("bIsBaking"))){RestorePanel(TEXT("BakeWidget"),TEXT("/Game/UI/Widgets/Progress/WBP_BakingProgress.WBP_BakingProgress_C"));UFoodGraphTool::SetCookingLoop(A,TEXT("Oven"),true);}
      if(N==TEXT("BP_RollingStation_C") && Flag(TEXT("bRolling"))){RestorePanel(TEXT("ProgressWidget"),TEXT("/Game/UI/Widgets/Progress/WBP_RollingProgress.WBP_RollingProgress_C"));UFoodGraphTool::SetCookingLoop(A,TEXT("Roll"),true);}
      if(N==TEXT("BP_Sink_C") && Flag(TEXT("bRunning")))UFoodGraphTool::StartWashAudio(A);
    }
    if(UFoodAchievementSubsystem* Achievement=World->GetSubsystem<UFoodAchievementSubsystem>())Achievement->RestoreSessionEnding(Data->bEndingSeen);
    if(Data->bEndingSeen)UFoodGraphTool::SetBackgroundMusic(World,true);
    return true;
}
void Tick(UWorld* World,float DeltaSeconds)
{
    if(!World||World!=ActiveWorld.Get()||World->IsPaused())return;
    SaveElapsed+=DeltaSeconds;if(SaveElapsed>=5.f){SaveElapsed=0.f;Save(World);}
}
}
