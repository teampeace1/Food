#include "FoodFinale.h"
#include "FoodAchievementSubsystem.h"
#include "Engine/TriggerBox.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "UObject/UnrealType.h"
#include "Styling/CoreStyle.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"

namespace FoodFinale {
static TWeakObjectPtr<UWorld> WorldRef;
static TWeakObjectPtr<AActor> Pie;
static TSharedPtr<SWidget> Hint;
static bool bReady=false,bDone=false;
static FString StringProp(AActor* A,const TCHAR* N) { if (!A) return {}; if (auto* P=FindFProperty<FStrProperty>(A->GetClass(),N)) return P->GetPropertyValue_InContainer(A); return {}; }
static AActor* ActorProp(AActor* A,const TCHAR* N) { if (!A) return nullptr; if (auto* P=FindFProperty<FObjectPropertyBase>(A->GetClass(),N)) return Cast<AActor>(P->GetObjectPropertyValue_InContainer(A)); return nullptr; }
void Shutdown(UWorld* W) { if (WorldRef.Get()!=W) return; if (Hint.IsValid() && W && W->GetGameViewport()) W->GetGameViewport()->RemoveViewportWidgetContent(Hint.ToSharedRef()); Hint.Reset(); Pie.Reset(); WorldRef.Reset(); }
void Tick(UWorld* W) {
 if (!W || !W->GetGameViewport() || W->IsPaused()) return;
 if (WorldRef.Get()!=W) { WorldRef=W; Pie.Reset(); Hint.Reset(); bReady=false; bDone=false; }
 if (UFoodAchievementSubsystem* Ach=W->GetSubsystem<UFoodAchievementSubsystem>()) if (Ach->HasSessionEnding()) { bDone=true; return; }
 if (bDone) return;
 for (TActorIterator<AActor> I(W); I; ++I) if (I->GetClass()->GetName()==TEXT("BP_Oven_C")) {
   AActor* P=ActorProp(*I,TEXT("PieRef"));
   if (P && StringProp(*I,TEXT("BakeQuality")).Equals(TEXT("Success"),ESearchCase::IgnoreCase)) { Pie=P; bReady=true; break; }
 }
 if (!bReady || !Pie.IsValid()) return;
 if (!Hint.IsValid()) { Hint=SNew(SOverlay).Visibility(EVisibility::HitTestInvisible)
   +SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,110)
   [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"))).BorderBackgroundColor(FLinearColor(.15f,.08f,.035f,.9f)).Padding(FMargin(18,9))
    [SNew(STextBlock).Text(FText::FromString(TEXT("派烤好了，请把派放到餐桌上"))).Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"),20)).ColorAndOpacity(FLinearColor(1,.91f,.72f))]];
   W->GetGameViewport()->AddViewportWidgetContent(Hint.ToSharedRef(),650);
 }
 APlayerController* PC=W->GetFirstPlayerController(); APawn* Pawn=PC?PC->GetPawn():nullptr;
 if (!Pawn || ActorProp(Pawn,TEXT("HeldActor"))==Pie.Get() || Pie->GetAttachParentActor()!=nullptr) return;
 FVector Origin,Extent; Pie->GetActorBounds(false,Origin,Extent);
 for (TActorIterator<ATriggerBox> I(W); I; ++I) if (I->ActorHasTag(TEXT("FoodFinaleTableZone"))) {
   FVector Zone,Radius; I->GetActorBounds(false,Zone,Radius);
   if (FMath::Abs(Origin.X-Zone.X)<=Radius.X && FMath::Abs(Origin.Y-Zone.Y)<=Radius.Y && FMath::Abs(Origin.Z-Zone.Z)<=Radius.Z+Extent.Z) {
    if (UFunction* F=Pawn->FindFunction(TEXT("OpenEndingDialogue"))) { bDone=true; W->GetGameViewport()->RemoveViewportWidgetContent(Hint.ToSharedRef()); Hint.Reset(); if (UFoodAchievementSubsystem* Ach=W->GetSubsystem<UFoodAchievementSubsystem>()) Ach->ReportEndingStarted(); Pawn->ProcessEvent(F,nullptr); }
    break;
   }
 }
}
}
