#include "FoodAchievementSubsystem.h"
#include "FoodProgress.h"
#include "FoodGraphTool.h"
#include "FoodAchievementSaveGame.h"
#include "FoodMenu.h"
#include "FoodStoryBook.h"
#include "FoodFinale.h"

#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"
#include "Components/Image.h"
#include "Components/ScrollBox.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/GameViewportClient.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

#if PLATFORM_WINDOWS
#include "Windows/AllowWindowsPlatformTypes.h"
#include <windows.h>
#include "Windows/HideWindowsPlatformTypes.h"
#endif
#include "UObject/UnrealType.h"

namespace
{
constexpr TCHAR SaveSlot[] = TEXT("FoodAchievements");
struct FMedalDefinition
{
    const TCHAR* Id;
    const TCHAR* Name;
    const TCHAR* Description;
    const TCHAR* Texture;
};
const FMedalDefinition Medals[] = {
    {TEXT("dough_beginner"), TEXT("面点新手"), TEXT("一切从一块面团开始。"), TEXT("/Game/UI/Art/Medals/achievement_dough_beginner.achievement_dough_beginner")},
    {TEXT("knife_skills"), TEXT("刀工初显"), TEXT("每一刀都有它的意义。"), TEXT("/Game/UI/Art/Medals/achievement_knife_skills.achievement_knife_skills")},
    {TEXT("seven_fish_heads"), TEXT("星空排列师"), TEXT("让四颗星星找到自己的位置。"), TEXT("/Game/UI/Art/Medals/achievement_seven_fish_heads.achievement_seven_fish_heads")},
    {TEXT("heat_master"), TEXT("火候大师"), TEXT("时间与温度，都掌握在手中。"), TEXT("/Game/UI/Art/Medals/achievement_heat_master.achievement_heat_master")},
    {TEXT("chef_approval"), TEXT("大厨的认可"), TEXT("老厨师终于露出了满意的笑容。"), TEXT("/Game/UI/Art/Medals/achievement_chef_approval.achievement_chef_approval")},
    {TEXT("shared_pie"), TEXT("一起完成"), TEXT("一道料理，一段同行的回忆。"), TEXT("/Game/UI/Art/Medals/achievement_shared_pie.achievement_shared_pie")},
};
constexpr int32 MedalCount = UE_ARRAY_COUNT(Medals);

FString ReadString(UObject* Object, const TCHAR* Name)
{
    if (!Object) return {};
    FProperty* Property = Object->GetClass()->FindPropertyByName(FName(Name));
    if (!Property) return {};
    if (const FStrProperty* P = CastField<FStrProperty>(Property)) return P->GetPropertyValue_InContainer(Object);
    if (const FNameProperty* P = CastField<FNameProperty>(Property)) return P->GetPropertyValue_InContainer(Object).ToString();
    if (const FTextProperty* P = CastField<FTextProperty>(Property)) return P->GetPropertyValue_InContainer(Object).ToString();
    return {};
}

int32 ReadInt(UObject* Object, const TCHAR* Name)
{
    if (!Object) return 0;
    FProperty* Property = Object->GetClass()->FindPropertyByName(FName(Name));
    if (const FIntProperty* P = CastField<FIntProperty>(Property)) return P->GetPropertyValue_InContainer(Object);
    if (const FByteProperty* P = CastField<FByteProperty>(Property)) return P->GetPropertyValue_InContainer(Object);
    return 0;
}

bool ReadBool(UObject* Object, const TCHAR* Name)
{
    if (!Object) return false;
    if (const FBoolProperty* P = CastField<FBoolProperty>(Object->GetClass()->FindPropertyByName(FName(Name))))
        return P->GetPropertyValue_InContainer(Object);
    return false;
}

bool IsPerfect(const FString& Quality)
{
    // BP_Oven only ever writes "Success" / "Failed" (see its OnPieFinished graph), so a successful
    // bake is the best "perfect" this game can express. The S/Perfect/完美 forms are still honoured
    // in case the oven grows a graded scale later.
    return Quality.Equals(TEXT("S"), ESearchCase::IgnoreCase)
        || Quality.Equals(TEXT("Success"), ESearchCase::IgnoreCase)
        || Quality.Contains(TEXT("Success"), ESearchCase::IgnoreCase)
        || Quality.Contains(TEXT("Perfect"), ESearchCase::IgnoreCase)
        || Quality.Contains(TEXT("完美"))
        || Quality.Contains(TEXT("成功"));
}

bool IsSuccessfulRoll(const FString& Quality)
{
    return !Quality.IsEmpty() && !Quality.Equals(TEXT("Raw"), ESearchCase::IgnoreCase)
        && !Quality.Equals(TEXT("F"), ESearchCase::IgnoreCase)
        && !Quality.Contains(TEXT("Failed"), ESearchCase::IgnoreCase)
        && !Quality.Contains(TEXT("失败"));
}

void PlayRecipePageFlip(UWorld* World)
{
    if (!World) return;
    static double LastPlay = -100.0;
    const double Now=FPlatformTime::Seconds(); if (Now-LastPlay<0.2) return; LastPlay=Now;
    if (USoundBase* Sound=LoadObject<USoundBase>(nullptr,TEXT("/Game/FoodAudio/SFX_PageFlip.SFX_PageFlip"))) UGameplayStatics::PlaySound2D(World,Sound,0.26f);
}
FSlateFontInfo Font(int32 Size, bool bBold = false)
{
    return FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), Size);
}
}

bool UFoodAchievementSubsystem::DoesSupportWorldType(EWorldType::Type WorldType) const
{
    return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UFoodAchievementSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    // Every Play-in-Editor run is a fresh acceptance pass. Do not load a previous test's medals,
    // and do not let the test write over the player's stand-alone save slot.
    const bool bEditorPreview = GetWorld() && GetWorld()->WorldType == EWorldType::PIE;
    if (!bEditorPreview && UGameplayStatics::DoesSaveGameExist(SaveSlot, 0))
        SaveData = Cast<UFoodAchievementSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlot, 0));
    if (!SaveData) SaveData = Cast<UFoodAchievementSaveGame>(UGameplayStatics::CreateSaveGameObject(UFoodAchievementSaveGame::StaticClass()));
    if (bEditorPreview)
        UE_LOG(LogTemp, Display, TEXT("Food achievements: fresh PIE preview, progress will not be saved"));

    // Opt-in wipe for testing the popups: launch with -FoodResetAchievements. Normal runs never
    // touch the player's medal list.
    if (FParse::Param(FCommandLine::Get(), TEXT("FoodResetAchievements")))
    {
        SaveData->UnlockedIds.Reset();
        Save();
        UE_LOG(LogTemp, Warning, TEXT("Food achievements wiped by -FoodResetAchievements"));
    }

    BuildMedalBrushes();
    TextPanelTexture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/UI/Art/Frames/T_WoodParchmentFrame.T_WoodParchmentFrame"));
    TextPanelBrush.SetResourceObject(TextPanelTexture);
    TextPanelBrush.ImageSize = FVector2D(2048, 1152);
    TextPanelBrush.DrawAs = ESlateBrushDrawType::Image;
    // A player who already owns five medals on disk earns the approval as soon as the game starts,
    // even though this session has not re-done any of the steps yet.
    CheckChefApproval();
}

void UFoodAchievementSubsystem::Deinitialize()
{
    FoodProgress::SetActive(GetWorld(), false);
    FoodMenu::Shutdown(GetWorld());
    FoodStoryBook::Shutdown(GetWorld());
    FoodFinale::Shutdown(GetWorld());
    if (bRecipeMovementLocked && GetWorld() && GetWorld()->GetFirstPlayerController()) GetWorld()->GetFirstPlayerController()->SetIgnoreMoveInput(false);
    if (MemoryToast.IsValid()) MemoryToast->RemoveFromParent();
    MemoryToast.Reset();
    RemovePopup();
    RemoveJournal();
    Super::Deinitialize();
}

TStatId UFoodAchievementSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(UFoodAchievementSubsystem, STATGROUP_Tickables);
}

void UFoodAchievementSubsystem::Tick(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World) return;
    FoodMenu::Tick(World);
    FoodProgress::Tick(World, DeltaTime);
    if (World->IsPaused()) { StyleTextPanels(); return; }
    FoodStoryBook::Tick(World);
    FoodFinale::Tick(World);

    // Polling must not depend on a viewport: a -nullrhi stand-alone session (and a dedicated
    // server) has none, and bailing out here silently disabled every milestone except the
    // ending one. Only the popup/journal below actually need the viewport.
    RecipeScanAccumulator += DeltaTime;
    if (RecipeScanAccumulator >= 0.1f)
    {
        RecipeScanAccumulator = 0.0f;
        for (TActorIterator<AActor> It(World); It; ++It) InspectActor(*It);
        UpdateMemoryNotifications();
        UpdateRecipeUI();
        StyleTextPanels();
    }

    if (!World->GetGameViewport()) return;

    // There is no mouse cursor in game, so the two pages are flipped with the arrow keys. The
    // subsystem owns no input component, hence polling the controller and edge-detecting here.
    if (bRecipeVisible)
    {
        if (APlayerController* PC = World->GetFirstPlayerController())
        {
            // The overlay owns focus, so neither the controller nor Slate reliably reports the arrow
            // keys here. Read the raw key state instead: it is the only source that works without
            // a mouse cursor.
            auto ArrowDown = [](int32 VirtualKey)
            {
#if PLATFORM_WINDOWS
                return (::GetAsyncKeyState(VirtualKey) & 0x8000) != 0;
#else
                return false;
#endif
            };
            const bool bLeft = PC->IsInputKeyDown(EKeys::Left) || ArrowDown(0x25);   // VK_LEFT
            const bool bRight = PC->IsInputKeyDown(EKeys::Right) || ArrowDown(0x27); // VK_RIGHT
            if ((bLeft && !bLeftHeld) || (bRight && !bRightHeld))
            {
                bJournalOpen = !bJournalOpen;
                PlayRecipePageFlip(GetWorld());
                RebuildJournal();
            }
            bLeftHeld = bLeft;
            bRightHeld = bRight;
            const bool bUp = PC->IsInputKeyDown(EKeys::Up) || ArrowDown(0x26);
            const bool bDown = PC->IsInputKeyDown(EKeys::Down) || ArrowDown(0x28);
            if (bJournalOpen && MemoryScroll.IsValid())
            {
                if (bUp && !bUpHeld) MemoryScroll->SetScrollOffset(FMath::Max(0.f, MemoryScroll->GetScrollOffset() - 110.f));
                if (bDown && !bDownHeld) MemoryScroll->SetScrollOffset(MemoryScroll->GetScrollOffset() + 110.f);
            }
            bUpHeld = bUp; bDownHeld = bDown;
        }
    }

    if (PopupWidget.IsValid())
    {
        const double Elapsed = FPlatformTime::Seconds() - PopupStartTime;
        if (Elapsed >= 5.0)
        {
            RemovePopup();
            ShowNextPopup();
        }
        else
        {
            const float Alpha = FMath::Clamp(static_cast<float>(FMath::Min(Elapsed, 5.0 - Elapsed) / 0.35), 0.0f, 1.0f);
            if (PopupBorder.IsValid()) PopupBorder->SetRenderOpacity(Alpha);
            // A quick full turn settles into a gentle shine while the toast is visible.
            if (PopupMedal.IsValid())
            {
                const float Intro = FMath::Clamp(static_cast<float>(Elapsed / 0.75), 0.0f, 1.0f);
                const float Ease = 1.0f - FMath::Pow(1.0f - Intro, 3.0f);
                const float Angle = 2.0f * PI * Ease;
                const float Scale = 0.55f + 0.45f * Ease + 0.08f * FMath::Sin(Intro * PI);
                FWidgetTransform MedalTransform;
                MedalTransform.Scale = FVector2D(Scale, Scale);
                MedalTransform.Angle = FMath::RadiansToDegrees(Angle);
                PopupMedal->SetRenderTransform(MedalTransform);
                PopupMedal->SetColorAndOpacity(FLinearColor(1.0f, 0.93f + 0.07f * FMath::Sin(static_cast<float>(Elapsed) * 12.0f), 0.75f + 0.25f * FMath::Sin(static_cast<float>(Elapsed) * 12.0f), 1.0f));
            }
            if (PopupSparkle.IsValid())
                PopupSparkle->SetRenderOpacity(0.35f + 0.65f * FMath::Abs(FMath::Sin(static_cast<float>(Elapsed) * 9.0f)));
        }
    }
    else if (!PopupQueue.IsEmpty()) ShowNextPopup();
}

void UFoodAchievementSubsystem::UpdateMemoryNotifications()
{
    UWorld* World = GetWorld();
    if (!World || !World->GetGameViewport()) return;
    const bool Ready[] = {bDoughComplete, bFishCut && bOnionCut && bParsleyCut, bFillingReady, bHeadsComplete, bBakePerfect, bEndingSeen};
    const TCHAR* Lines[] = {
        TEXT("第一次擀面时，我们把厨房弄得像下了一场雪。"),
        TEXT("准备食材的时间，也像一场小小的聚会。"),
        TEXT("把不同的味道拌在一起，是大家最期待的一步。"),
        TEXT("鱼头朝向天空，就好像在看海上的星星。"),
        TEXT("等香味传出来，总有人已经坐在桌边。"),
        TEXT("谢谢你陪我走过餐馆的最后一天。")
    };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Ready); ++Index)
        if (Ready[Index] && !bMemoryNotified[Index]) { bMemoryNotified[Index] = true; MemoryToastQueue.Add(Index); }
    if (MemoryToast.IsValid() && FPlatformTime::Seconds() - MemoryToastStart >= 5.0)
    {
        MemoryToast->RemoveFromParent();
        MemoryToast.Reset();
    }
    if (!MemoryToast.IsValid() && !MemoryToastQueue.IsEmpty())
    {
        const int32 Index = MemoryToastQueue[0];
        MemoryToastQueue.RemoveAt(0);
        UClass* ToastClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/HUD/WBP_MemoryToast.WBP_MemoryToast_C"));
        UUserWidget* Toast = ToastClass ? CreateWidget<UUserWidget>(World, ToastClass) : nullptr;
        if (!Toast)
        {
            UE_LOG(LogTemp, Warning, TEXT("Missing widget blueprint: /Game/UI/Widgets/HUD/WBP_MemoryToast"));
            return;
        }
        // 位置、背景、字号都在 WBP_MemoryToast 里调，代码只负责填这一句回忆
        if (Toast->WidgetTree)
        {
            if (UTextBlock* Body = Cast<UTextBlock>(Toast->WidgetTree->FindWidget(TEXT("Body"))))
                Body->SetText(FText::FromString(Lines[Index]));
        }
        Toast->AddToViewport(750);
        MemoryToast = Toast;
        MemoryToastStart = FPlatformTime::Seconds();
    }
}

void UFoodAchievementSubsystem::ReportDoughCompleted(bool bPerfect)
{
    bDoughComplete = true;
    bDoughPerfect |= bPerfect;
    Unlock(TEXT("dough_beginner"));
    CheckChefApproval();
}

void UFoodAchievementSubsystem::ReportIngredientChopped(const FString& IngredientName)
{
    if ((IngredientName.Contains(TEXT("鱼")) && !IngredientName.Contains(TEXT("鱼头"))) || IngredientName.Contains(TEXT("fish"), ESearchCase::IgnoreCase)) bFishCut = true;
    if (IngredientName.Contains(TEXT("洋葱")) || IngredientName.Contains(TEXT("onion"), ESearchCase::IgnoreCase)) bOnionCut = true;
    if (IngredientName.Contains(TEXT("欧芹")) || IngredientName.Contains(TEXT("parsley"), ESearchCase::IgnoreCase)) bParsleyCut = true;
    if (bFishCut && bOnionCut && bParsleyCut) Unlock(TEXT("knife_skills"));
    CheckChefApproval();
}

void UFoodAchievementSubsystem::ReportFishHeadPlaced(int32 TotalPlaced)
{
    if (TotalPlaced < 4) return;
    bHeadsComplete = true;
    Unlock(TEXT("seven_fish_heads"));
    CheckChefApproval();
}

void UFoodAchievementSubsystem::ReportPieFinished(const FString& Quality)
{
    if (Quality.IsEmpty()) return;
    const bool bPerfect = IsPerfect(Quality);
    // Unlock() is already idempotent, so a good bake grants the medal no matter how many earlier
    // ones failed. The old "only before the first bake" guard made a single botched attempt
    // permanently disqualify the player.
    if (bPerfect) Unlock(TEXT("heat_master"));
    bPieFinished = true;
    bBakePerfect |= bPerfect;
    CheckChefApproval();
}

void UFoodAchievementSubsystem::ReportEndingStarted()
{
    if (bEndingSeen) return;
    // The pie may well have been baked in an earlier session; the medal set remembers that.
    if (!bPieFinished && !IsUnlocked(TEXT("heat_master"))) return;
    bEndingSeen = true;
    Unlock(TEXT("shared_pie"));
    CheckChefApproval();
}

bool UFoodAchievementSubsystem::IsUnlocked(FName AchievementId) const
{
    return SaveData && SaveData->UnlockedIds.Contains(AchievementId);
}

void UFoodAchievementSubsystem::ResetProgress()
{
    bDoughComplete = bDoughPerfect = false;
    bFishCut = bOnionCut = bParsleyCut = false;
    bHeadsComplete = bFillingReady = bBakePerfect = bPieFinished = bEndingSeen = false;
    PopupQueue.Reset();
    RemovePopup();
    if (JournalWidget.IsValid()) RebuildJournal();
    if (!SaveData) return;
    SaveData->UnlockedIds.Reset();
    Save();
    UE_LOG(LogTemp, Warning, TEXT("Food achievements reset (memory + save slot)"));
}

bool UFoodAchievementSubsystem::IsPopupShowing() const
{
    return PopupWidget.IsValid();
}

void UFoodAchievementSubsystem::SetJournalOpen(bool bOpen)
{
    bJournalOpen = bOpen;
    if (bRecipeVisible || JournalWidget.IsValid()) RebuildJournal();
}

bool UFoodAchievementSubsystem::IsJournalShowing() const
{
    return bJournalOpen && JournalWidget.IsValid();
}

bool UFoodAchievementSubsystem::IsRecipeVisible() const
{
    return bRecipeVisible;
}

FString UFoodAchievementSubsystem::DescribeMilestones() const
{
    TArray<FString> Parts;
    Parts.Add(FString::Printf(TEXT("dough=%d/%d"), bDoughComplete ? 1 : 0, bDoughPerfect ? 1 : 0));
    Parts.Add(FString::Printf(TEXT("cut(fish/onion/parsley)=%d/%d/%d"), bFishCut ? 1 : 0, bOnionCut ? 1 : 0, bParsleyCut ? 1 : 0));
    Parts.Add(FString::Printf(TEXT("heads=%d filling=%d bakePerfect=%d pie=%d ending=%d"),
        bHeadsComplete ? 1 : 0, bFillingReady ? 1 : 0, bBakePerfect ? 1 : 0, bPieFinished ? 1 : 0, bEndingSeen ? 1 : 0));
    int32 Unlocked = 0;
    for (const FMedalDefinition& Medal : Medals) if (IsUnlocked(FName(Medal.Id))) ++Unlocked;
    Parts.Add(FString::Printf(TEXT("unlocked=%d/%d"), Unlocked, MedalCount));
    return FString::Join(Parts, TEXT(" "));
}

void UFoodAchievementSubsystem::InspectActor(AActor* Actor)
{
    if (!Actor || Actor->IsActorBeingDestroyed()) return;
    const FString ClassName = Actor->GetClass()->GetName();
    if (ClassName == TEXT("BP_Ingredient_C"))
    {
        const FString Name = ReadString(Actor, TEXT("IngredientName"));
        const FString RollQuality = ReadString(Actor, TEXT("RollQuality"));
        if ((Name.Contains(TEXT("面团")) || Name.Contains(TEXT("Dough"), ESearchCase::IgnoreCase)) && IsSuccessfulRoll(RollQuality))
            ReportDoughCompleted(IsPerfect(RollQuality));
        const int32 CutNeeded = ReadInt(Actor, TEXT("CutNeeded"));
        if (CutNeeded > 0 && ReadInt(Actor, TEXT("CutCount")) >= CutNeeded) ReportIngredientChopped(Name);
    }
    else if (ClassName == TEXT("BP_Pie_C")) ReportFishHeadPlaced(ReadInt(Actor, TEXT("HeadsPlaced")));
    else if (ClassName == TEXT("BP_FillingBowl_C"))
    {
        bFillingReady |= ReadBool(Actor, TEXT("bFillingReady"));
        CheckChefApproval();
    }
    else if (ClassName == TEXT("BP_Oven_C") && ReadBool(Actor, TEXT("bFinished")))
        ReportPieFinished(ReadString(Actor, TEXT("BakeQuality")));
}

void UFoodAchievementSubsystem::CheckChefApproval()
{
    // Judged from the medals themselves, not from this session's flags: a cook who rolls, chops,
    // places, bakes and shares over several sittings still earns the approval. The old in-memory
    // version demanded all eight milestones inside one run, which normal play almost never does.
    static const TCHAR* Required[] = {
        TEXT("dough_beginner"), TEXT("knife_skills"), TEXT("seven_fish_heads"),
        TEXT("heat_master"), TEXT("shared_pie")
    };
    for (const TCHAR* Id : Required)
    {
        if (!IsUnlocked(FName(Id))) return;
    }
    Unlock(TEXT("chef_approval"));
}

int32 UFoodAchievementSubsystem::FindDefinition(FName Id) const
{
    for (int32 Index = 0; Index < MedalCount; ++Index)
        if (Id == FName(Medals[Index].Id)) return Index;
    return INDEX_NONE;
}

void UFoodAchievementSubsystem::Unlock(FName Id)
{
    const int32 Index = FindDefinition(Id);
    if (Index == INDEX_NONE || IsUnlocked(Id) || !SaveData) return;
    SaveData->UnlockedIds.Add(Id);
    Save();
    PopupQueue.Add(Index);
    // Mount the toast in the gameplay viewport at the moment of completion. The recipe/journal
    // overlay is unrelated and never has to be opened for a medal to appear.
    if (!PopupWidget.IsValid()) ShowNextPopup();
    if (bRecipeVisible && bJournalOpen) RebuildJournal();
    UE_LOG(LogTemp, Display, TEXT("Food achievement unlocked: %s"), Medals[Index].Name);
}

void UFoodAchievementSubsystem::Save()
{
    if (GetWorld() && GetWorld()->WorldType == EWorldType::PIE) return;
    if (!UGameplayStatics::SaveGameToSlot(SaveData, SaveSlot, 0))
        UE_LOG(LogTemp, Error, TEXT("Food achievement save failed"));
}

void UFoodAchievementSubsystem::BuildMedalBrushes()
{
    MedalTextures.Reset();
    MedalBrushes.Reset();
    MedalTextures.Reserve(MedalCount);
    MedalBrushes.Reserve(MedalCount);
    for (const FMedalDefinition& Medal : Medals)
    {
        UTexture2D* Texture = LoadObject<UTexture2D>(nullptr, Medal.Texture);
        MedalTextures.Add(Texture);
        FSlateBrush Brush;
        Brush.SetResourceObject(Texture);
        Brush.ImageSize = FVector2D(72, 72);
        MedalBrushes.Add(Brush);
        if (!Texture) UE_LOG(LogTemp, Warning, TEXT("Missing achievement medal: %s"), Medal.Texture);
    }
}

void UFoodAchievementSubsystem::UpdateRecipeUI()
{
    UWorld* World = GetWorld();
    static const TCHAR* RecipePath = TEXT("/Game/UI/Widgets/Panels/WBP_RecipeGuide.WBP_RecipeGuide_C");
    static const TCHAR* EndingPath = TEXT("/Game/UI/Widgets/Panels/WBP_ChefEnding.WBP_ChefEnding_C");
    bool bNowVisible = false;
    if (UClass* RecipeClass = LoadClass<UUserWidget>(nullptr, RecipePath))
    {
        TArray<UUserWidget*> Widgets;
        UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Widgets, RecipeClass, false);
        // InViewport, not IsVisible: the journal collapses the recipe sheet while its tab is open,
        // and that must not read as "the player closed the recipe".
        for (UUserWidget* Widget : Widgets) if (Widget && Widget->IsInViewport()) { bNowVisible = true; break; }
    }
    if (bNowVisible != bRecipeVisible)
    {
        bRecipeVisible = bNowVisible;
        if (APlayerController* PC = World->GetFirstPlayerController())
        {
            if (bNowVisible && !bRecipeMovementLocked) { PC->SetIgnoreMoveInput(true); bRecipeMovementLocked = true; }
            else if (!bNowVisible && bRecipeMovementLocked) { PC->SetIgnoreMoveInput(false); bRecipeMovementLocked = false; }
        }
        if (bRecipeVisible) RebuildJournal();
        else { bJournalOpen = false; bRecipeTitleAligned = false; RemoveJournal(); }
    }
    if (bRecipeVisible) FixRecipeTitleLayout();
    if (!bEndingSeen)
    {
        if (UClass* EndingClass = LoadClass<UUserWidget>(nullptr, EndingPath))
        {
            TArray<UUserWidget*> Widgets;
            UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Widgets, EndingClass, false);
            for (UUserWidget* Widget : Widgets) if (Widget && Widget->IsInViewport() && Widget->IsVisible()) { UFoodGraphTool::SetBackgroundMusic(World, true); ReportEndingStarted(); break; }
        }
    }
}

void UFoodAchievementSubsystem::FixRecipeTitleLayout()
{
    // The plaque is painted into the Backdrop image, not a widget of its own, so the title is
    // aligned against a measured fraction of the backdrop instead of a pixel offset: that keeps it
    // on the plaque at any resolution. The slot data itself is protected in the widget blueprint.
    UWorld* World = GetWorld();
    if (!World) return;
    UClass* RecipeClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_RecipeGuide.WBP_RecipeGuide_C"));
    if (!RecipeClass) return;

    TArray<UUserWidget*> Widgets;
    UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Widgets, RecipeClass, false);
    for (UUserWidget* Widget : Widgets)
    {
        if (!Widget || !Widget->IsInViewport() || !Widget->WidgetTree) continue;

        FGeometry BackdropGeo;
        UWidget* Title = nullptr;
        Widget->WidgetTree->ForEachWidget([&BackdropGeo, &Title](UWidget* Child)
        {
            if (!Child) return;
            if (Child->GetName() == TEXT("Backdrop")) BackdropGeo = Child->GetTickSpaceGeometry();
            else if (Child->GetName() == TEXT("Title")) Title = Child;
        });

        if (!Title) continue;
        const FGeometry TitleGeo = Title->GetTickSpaceGeometry();
        const FVector2D BackdropSize = BackdropGeo.GetAbsoluteSize();
        if (BackdropSize.IsNearlyZero() || TitleGeo.GetAbsoluteSize().IsNearlyZero()) continue;

        const FVector2D TargetCenter = BackdropGeo.GetAbsolutePosition()
            + FVector2D(BackdropSize.X * 0.235f, BackdropSize.Y * 0.075f);
        const FVector2D CurrentCenter = TitleGeo.GetAbsolutePosition() + TitleGeo.GetAbsoluteSize() * 0.5f;
        // Render translation is in DPI-scaled local units, so the measured pixel delta is divided
        // by the widget's accumulated layout scale before it is applied.
        // One shot per opened panel: the cached tick geometry does not follow the translation, so
        // repeating this would keep pushing the title off screen.
        if (!bRecipeTitleAligned)
        {
            // Tuned against renders at 1280x720: the plaque centre sits about 54px left and 8px up
            // from where the title block is authored, which leaves its bottom half off the plaque.
            Title->SetRenderTranslation(FVector2D(-15.0f, 2.0f));
            bRecipeTitleAligned = true;
        }

        if (UTextBlock* TitleText = Cast<UTextBlock>(Title))
            TitleText->SetColorAndOpacity(FSlateColor(FLinearColor(1.0f, 0.95f, 0.84f, 1.0f)));
    }
}

void UFoodAchievementSubsystem::StyleTextPanels()
{
    if (!TextPanelTexture || !GetWorld()) return;
    static const TCHAR* PanelPaths[] = {
        TEXT("/Game/UI/Widgets/Panels/WBP_ChefEnding.WBP_ChefEnding_C"),
        TEXT("/Game/UI/Widgets/Progress/WBP_BakingProgress.WBP_BakingProgress_C"),
        TEXT("/Game/UI/Widgets/Progress/WBP_RollingProgress.WBP_RollingProgress_C")
    };
    StyledTextPanels.RemoveAll([](const TWeakObjectPtr<UObject>& Item) { return !Item.IsValid(); });
    for (const TCHAR* Path : PanelPaths)
    {
        UClass* Class = LoadClass<UUserWidget>(nullptr, Path);
        if (!Class) continue;
        TArray<UUserWidget*> Widgets;
        UWidgetBlueprintLibrary::GetAllWidgetsOfClass(GetWorld(), Widgets, Class, false);
        for (UUserWidget* Widget : Widgets)
        {
            if (!Widget || !Widget->IsInViewport() || !Widget->WidgetTree || StyledTextPanels.Contains(Widget)) continue;
            Widget->WidgetTree->ForEachWidget([this](UWidget* Child)
            {
                if (UBorder* Border = Cast<UBorder>(Child))
                {
                    Border->SetBrushFromTexture(TextPanelTexture);
                    Border->SetBrushColor(FLinearColor::White);
                }
                else if (UTextBlock* Text = Cast<UTextBlock>(Child))
                {
                    Text->SetColorAndOpacity(FSlateColor(FLinearColor(0.16f, 0.075f, 0.035f, 1.0f)));
                }
            });
            StyledTextPanels.Add(Widget);
        }
    }
}

void UFoodAchievementSubsystem::RebuildJournal()
{
    RemoveJournal();
    UWorld* World = GetWorld();
    if (!World || !World->GetGameViewport() || !bRecipeVisible) return;

    // Tab only opens the overlay once; these arrows flip between the recipe sheet and the journal
    // without closing it, so a player does not have to leave the menu to look at the medals.
    auto MakeArrow = [this](const TCHAR* Glyph) -> TSharedRef<SWidget>
    {
        return SNew(SButton)
            .ButtonColorAndOpacity(FLinearColor(0.42f, 0.25f, 0.13f))
            .ContentPadding(FMargin(10, 0))
            .OnClicked_Lambda([this]() { bJournalOpen = !bJournalOpen; PlayRecipePageFlip(GetWorld()); RebuildJournal(); return FReply::Handled(); })
            [SNew(STextBlock).Text(FText::FromString(Glyph)).Font(Font(20, true)).ColorAndOpacity(FLinearColor(1.0f, 0.90f, 0.70f))];
    };
    auto MakeTab = [this](const TCHAR* Label, bool bActive, bool bTarget) -> TSharedRef<SWidget>
    {
        return SNew(SButton)
            .ButtonColorAndOpacity(bActive ? FLinearColor(0.55f, 0.35f, 0.16f) : FLinearColor(0.30f, 0.18f, 0.09f))
            .OnClicked_Lambda([this, bTarget]() { if (bJournalOpen != bTarget) PlayRecipePageFlip(GetWorld()); bJournalOpen = bTarget; RebuildJournal(); return FReply::Handled(); })
            [SNew(STextBlock).Text(FText::FromString(Label)).Font(Font(15, bActive)).ColorAndOpacity(FLinearColor(1.0f, 0.91f, 0.74f))];
    };

    // The switch lives on its own strip instead of inside the panel: the recipe sheet owns the
    // top-left corner and the medal popup owns the top-right, so it floats on the empty top edge
    // where it covers neither.
    TSharedRef<SWidget> TabRow = SNew(SBorder)
        .BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush")))
        .BorderBackgroundColor(FLinearColor(0.13f, 0.075f, 0.04f, 0.93f))
        .Padding(FMargin(6, 3))
        [SNew(SHorizontalBox)
         + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 6, 0)[MakeArrow(TEXT("<"))]
         + SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 6, 0)[MakeTab(TEXT("食谱"), !bJournalOpen, false)]
         + SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 6, 0)[MakeTab(TEXT("厨房手记"), bJournalOpen, true)]
         + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)[MakeArrow(TEXT(">"))]
         + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8, 0, 2, 0)
         [SNew(STextBlock).Text(FText::FromString(TEXT("左右键切换"))).Font(Font(11)).ColorAndOpacity(FLinearColor(0.82f, 0.74f, 0.60f))]];

    // The strip stays in Slate because it carries the click handlers; the panel itself is a widget
    // blueprint so the memory text and the card styling live in the designer.
    JournalTabStrip = SNew(SOverlay)
        + SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Top).Padding(FMargin(0, 9, 0, 0))
        [TabRow];
    World->GetGameViewport()->AddViewportWidgetContent(JournalTabStrip.ToSharedRef(), 701);

    if (bJournalOpen)
    {
        UClass* JournalClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_Journal.WBP_Journal_C"));
        UUserWidget* Journal = JournalClass ? CreateWidget<UUserWidget>(World, JournalClass) : nullptr;
        if (!Journal || !Journal->WidgetTree)
        {
            UE_LOG(LogTemp, Warning, TEXT("Missing widget blueprint: /Game/UI/Widgets/Panels/WBP_Journal"));
            SyncRecipeSheetVisibility();
            return;
        }

        // Story entries are tied to this play session's cooking progress rather than saved
        // achievement unlocks, so the memories follow what the player has actually done.
        // The wording lives in WBP_Journal; only the entries the player has not reached yet get
        // covered with the placeholder text.
        const bool Available[] = {
            true,
            bDoughComplete,
            bFishCut && bOnionCut && bParsleyCut,
            bFillingReady,
            bHeadsComplete,
            bBakePerfect,
            bEndingSeen,
        };
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(Available); ++Index)
        {
            if (Available[Index]) continue;
            if (UTextBlock* Heading = Cast<UTextBlock>(Journal->WidgetTree->FindWidget(FName(*FString::Printf(TEXT("Head%d"), Index)))))
                Heading->SetText(FText::FromString(TEXT("尚未解锁")));
            if (UTextBlock* Body = Cast<UTextBlock>(Journal->WidgetTree->FindWidget(FName(*FString::Printf(TEXT("Body%d"), Index)))))
                Body->SetText(FText::FromString(TEXT("……")));
        }

        // Medal rows are filled in here, but the card itself is WBP_MedalRow.
        UVerticalBox* MedalList = Cast<UVerticalBox>(Journal->WidgetTree->FindWidget(TEXT("MedalList")));
        UClass* RowClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_MedalRow.WBP_MedalRow_C"));
        if (MedalList && RowClass)
        {
            for (int32 Index = 0; Index < MedalCount; ++Index)
            {
                UUserWidget* Row = CreateWidget<UUserWidget>(World, RowClass);
                if (!Row || !Row->WidgetTree) continue;
                const bool bUnlocked = IsUnlocked(FName(Medals[Index].Id));
                if (UImage* Badge = Cast<UImage>(Row->WidgetTree->FindWidget(TEXT("Medal"))))
                {
                    if (MedalTextures.IsValidIndex(Index) && MedalTextures[Index]) Badge->SetBrushFromTexture(MedalTextures[Index]);
                    Badge->SetColorAndOpacity(bUnlocked ? FLinearColor::White : FLinearColor(0.13f, 0.11f, 0.09f, 1.0f));
                }
                if (UTextBlock* Lock = Cast<UTextBlock>(Row->WidgetTree->FindWidget(TEXT("Lock"))))
                    Lock->SetVisibility(bUnlocked ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
                if (UTextBlock* MedalName = Cast<UTextBlock>(Row->WidgetTree->FindWidget(TEXT("Name"))))
                    MedalName->SetText(FText::FromString(Medals[Index].Name));
                if (UTextBlock* MedalDesc = Cast<UTextBlock>(Row->WidgetTree->FindWidget(TEXT("Desc"))))
                    MedalDesc->SetText(FText::FromString(bUnlocked ? Medals[Index].Description : TEXT("???")));
                if (UVerticalBoxSlot* RowSlot = MedalList->AddChildToVerticalBox(Row))
                    RowSlot->SetPadding(FMargin(0.0f, 3.0f));
            }
        }

        Journal->AddToViewport(700);
        JournalWidget = Journal;
        MemoryScroll = Cast<UScrollBox>(Journal->WidgetTree->FindWidget(TEXT("Scroll")));
    }

    SyncRecipeSheetVisibility();
}

void UFoodAchievementSubsystem::SyncRecipeSheetVisibility()
{
    // The journal replaces the recipe sheet instead of stacking on top of it, so the tab row reads
    // as a real switch. Restored as soon as the journal closes.
    UWorld* World = GetWorld();
    if (!World) return;
    UClass* RecipeClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_RecipeGuide.WBP_RecipeGuide_C"));
    if (!RecipeClass) return;
    TArray<UUserWidget*> Widgets;
    UWidgetBlueprintLibrary::GetAllWidgetsOfClass(World, Widgets, RecipeClass, false);
    for (UUserWidget* Widget : Widgets)
    {
        if (Widget && Widget->IsInViewport())
            Widget->SetVisibility(bJournalOpen ? ESlateVisibility::Collapsed : ESlateVisibility::Visible);
    }
}

void UFoodAchievementSubsystem::RemoveJournal()
{
    MemoryScroll.Reset();
    if (JournalWidget.IsValid()) JournalWidget->RemoveFromParent();
    JournalWidget.Reset();
    if (JournalTabStrip.IsValid() && GetWorld() && GetWorld()->GetGameViewport())
        GetWorld()->GetGameViewport()->RemoveViewportWidgetContent(JournalTabStrip.ToSharedRef());
    JournalTabStrip.Reset();
    if (!bJournalOpen) SyncRecipeSheetVisibility();
}

void UFoodAchievementSubsystem::ShowNextPopup()
{
    if (PopupQueue.IsEmpty() || !GetWorld() || !GetWorld()->GetGameViewport()) return;
    const int32 Index = PopupQueue[0];
    PopupQueue.RemoveAt(0);
    const bool bCore = FCString::Strcmp(Medals[Index].Id, TEXT("chef_approval")) == 0 || FCString::Strcmp(Medals[Index].Id, TEXT("shared_pie")) == 0;
    const TCHAR* SoundPath = bCore ? TEXT("/Game/FoodAudio/SFX_CoreMotifPlan.SFX_CoreMotifPlan") : TEXT("/Game/FoodAudio/SFX_AchievementPlan.SFX_AchievementPlan");
    if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, SoundPath)) UGameplayStatics::PlaySound2D(GetWorld(), Sound, bCore ? 0.30f : 0.35f);

    // 外观布局在 WBP_AchievementPopup 里，代码只填勋章和三条文字
    UClass* PopupClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/HUD/WBP_AchievementPopup.WBP_AchievementPopup_C"));
    UUserWidget* Popup = PopupClass ? CreateWidget<UUserWidget>(GetWorld(), PopupClass) : nullptr;
    if (!Popup || !Popup->WidgetTree)
    {
        UE_LOG(LogTemp, Warning, TEXT("Missing widget blueprint: /Game/UI/Widgets/HUD/WBP_AchievementPopup"));
        return;
    }
    UBorder* Border = Cast<UBorder>(Popup->WidgetTree->FindWidget(TEXT("Bg")));
    UImage* Medal = Cast<UImage>(Popup->WidgetTree->FindWidget(TEXT("Medal")));
    UTextBlock* Sparkle = Cast<UTextBlock>(Popup->WidgetTree->FindWidget(TEXT("Sparkle")));
    if (UTextBlock* Caption = Cast<UTextBlock>(Popup->WidgetTree->FindWidget(TEXT("Caption"))))
        Caption->SetText(FText::FromString(TEXT("成就达成！")));
    if (UTextBlock* Title = Cast<UTextBlock>(Popup->WidgetTree->FindWidget(TEXT("Name"))))
        Title->SetText(FText::FromString(Medals[Index].Name));
    if (UTextBlock* Desc = Cast<UTextBlock>(Popup->WidgetTree->FindWidget(TEXT("Desc"))))
        Desc->SetText(FText::FromString(Medals[Index].Description));
    if (Medal)
    {
        Medal->SetBrush(MedalBrushes[Index]);
        Medal->SetRenderTransformPivot(FVector2D(0.5f, 0.5f));
    }
    if (Border) Border->SetRenderOpacity(0.0f);

    PopupWidget = Popup;
    PopupBorder = Border;
    PopupMedal = Medal;
    PopupSparkle = Sparkle;
    Popup->AddToViewport(10000);
    PopupStartTime = FPlatformTime::Seconds();
    UE_LOG(LogTemp, Display, TEXT("Food achievement popup mounted in gameplay viewport: %s"), Medals[Index].Name);
}

void UFoodAchievementSubsystem::RemovePopup()
{
    if (PopupWidget.IsValid()) PopupWidget->RemoveFromParent();
    PopupWidget.Reset();
    PopupBorder.Reset();
    PopupMedal.Reset();
    PopupSparkle.Reset();
}
