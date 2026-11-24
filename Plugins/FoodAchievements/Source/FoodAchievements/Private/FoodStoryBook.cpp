#include "FoodStoryBook.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Styling/CoreStyle.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Text/STextBlock.h"

namespace FoodStoryBook
{
static TWeakObjectPtr<UWorld> CurrentWorld;
static TWeakObjectPtr<AStaticMeshActor> Book;
static TSharedPtr<SWidget> Hint;
static bool bCollected = false;
static bool bIntroRemoved = false;
static int32 HintType = -1;

bool IsCollected() { return bCollected; }
static void SetHint(UWorld* W, int32 Type)
{
    if (!W || !W->GetGameViewport() || HintType == Type) return;
    if (Hint.IsValid()) W->GetGameViewport()->RemoveViewportWidgetContent(Hint.ToSharedRef());
    Hint.Reset(); HintType = Type;
    if (!Type) return;
    const TCHAR* Text = Type == 1 ? TEXT("找找厨房台面上的老厨师手记") : Type == 2 ? TEXT("按 E 拾取老厨师的手记") : TEXT("按 Tab 查看手记与食谱");
    Hint = SNew(SOverlay).Visibility(EVisibility::HitTestInvisible)
      + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(0,0,0,85)
      [SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"))).BorderBackgroundColor(FLinearColor(.15f,.08f,.035f,.88f)).Padding(FMargin(18,9))
       [SNew(STextBlock).Text(FText::FromString(Text)).Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"),20)).ColorAndOpacity(FLinearColor(1,.91f,.72f))]];
    W->GetGameViewport()->AddViewportWidgetContent(Hint.ToSharedRef(),650);
}
void Tick(UWorld* W)
{
    if (!W || !W->GetGameViewport() || !W->GetFirstPlayerController()) return;
    if (CurrentWorld.Get() != W) { CurrentWorld = W; Book.Reset(); Hint.Reset(); HintType = -1; bCollected = false; bIntroRemoved = false; }
    if (W->IsPaused()) return;
    APlayerController* PC = W->GetFirstPlayerController();
    if (!bCollected)
    {
        if (!Book.IsValid())
        {
            for (TActorIterator<AStaticMeshActor> It(W); It; ++It)
                if (It->ActorHasTag(TEXT("FoodStoryBook"))) { Book = *It; break; }
        }
        if (!bCollected)
        {
            if (UClass* Intro = LoadClass<UUserWidget>(nullptr,TEXT("/Game/UI/Widgets/Panels/WBP_ChefIntro.WBP_ChefIntro_C")))
            {
                TArray<UUserWidget*> Widgets; UWidgetBlueprintLibrary::GetAllWidgetsOfClass(W,Widgets,Intro,false);
                for (UUserWidget* Widget : Widgets) if (Widget && Widget->IsInViewport()) { Widget->RemoveFromParent(); PC->SetInputMode(FInputModeGameOnly()); PC->bShowMouseCursor = false; bIntroRemoved = true; }
            }
        }
        if (UClass* Recipe = LoadClass<UUserWidget>(nullptr,TEXT("/Game/UI/Widgets/Panels/WBP_RecipeGuide.WBP_RecipeGuide_C")))
        {
            TArray<UUserWidget*> Widgets; UWidgetBlueprintLibrary::GetAllWidgetsOfClass(W,Widgets,Recipe,false);
            for (UUserWidget* Widget : Widgets) if (Widget && Widget->IsInViewport()) Widget->RemoveFromParent();
        }
        bool bNear = false;
        if (Book.IsValid())
        {
            FVector Eye; FRotator View; PC->GetPlayerViewPoint(Eye,View);
            FVector Origin, Extent;
            Book->GetActorBounds(false, Origin, Extent);
            const FVector ToBook = Origin - Eye;
            bNear = ToBook.Size() < 260.f && FVector::DotProduct(View.Vector(),ToBook.GetSafeNormal()) > .92f;
        }
        SetHint(W,bNear ? 2 : 1);
        if (bNear && PC->WasInputKeyJustPressed(EKeys::E))
        {
            bCollected = true;
            Book->Destroy(); Book.Reset(); SetHint(W,3);
            if (APawn* Pawn = PC->GetPawn())
                if (UFunction* Intro = Pawn->FindFunction(TEXT("OpenIntroDialogue"))) Pawn->ProcessEvent(Intro, nullptr);
        }
    }
    else if (HintType == 3 && PC->WasInputKeyJustPressed(EKeys::Tab)) SetHint(W,0);
}
void Shutdown(UWorld* W)
{
    if (CurrentWorld.Get() != W) return;
    if (Hint.IsValid() && W && W->GetGameViewport()) W->GetGameViewport()->RemoveViewportWidgetContent(Hint.ToSharedRef());
    Hint.Reset(); Book.Reset(); CurrentWorld.Reset();
}
}
