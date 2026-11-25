#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Styling/SlateBrush.h"
#include "FoodAchievementSubsystem.generated.h"

class AActor;
class SBorder;
class SImage;
class STextBlock;
class SWidget;
class UScrollBox;
class UBorder;
class UImage;
class UTextBlock;
class UUserWidget;
class UFoodAchievementSaveGame;
class UTexture2D;

UCLASS()
class FOODACHIEVEMENTS_API UFoodAchievementSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    virtual void Tick(float DeltaTime) override;
    virtual bool IsTickableWhenPaused() const override { return true; }
    virtual TStatId GetStatId() const override;

    UFUNCTION(BlueprintCallable, Category="Food|Achievements")
    void ReportDoughCompleted(bool bPerfect);
    UFUNCTION(BlueprintCallable, Category="Food|Achievements")
    void ReportIngredientChopped(const FString& IngredientName);
    UFUNCTION(BlueprintCallable, Category="Food|Achievements")
    void ReportFishHeadPlaced(int32 TotalPlaced);
    UFUNCTION(BlueprintCallable, Category="Food|Achievements")
    void ReportPieFinished(const FString& Quality);
    UFUNCTION(BlueprintCallable, Category="Food|Achievements")
    void ReportEndingStarted();
    bool HasSessionEnding() const { return bEndingSeen; }
    void RestoreSessionEnding(bool bSeen) { bEndingSeen = bSeen; }
    UFUNCTION(BlueprintPure, Category="Food|Achievements")
    bool IsUnlocked(FName AchievementId) const;

    /** Wipes the medal list (memory + save slot). Not wired to any UI on purpose - it exists so the
     *  automated check can observe a clean unlock run, and so a designer can re-test the popups. */
    UFUNCTION(BlueprintCallable, Category="Food|Achievements")
    void ResetProgress();

    /** Human-readable dump of the live milestone flags, used by the automated check. */
    UFUNCTION(BlueprintPure, Category="Food|Achievements")
    FString DescribeMilestones() const;

    /** True while a medal popup is actually mounted in the viewport. */
    UFUNCTION(BlueprintPure, Category="Food|Achievements")
    bool IsPopupShowing() const;

    /** Switches the recipe overlay between the recipe sheet and the medal journal. */
    UFUNCTION(BlueprintCallable, Category="Food|Achievements")
    void SetJournalOpen(bool bOpen);

    /** True when the journal panel is mounted. */
    UFUNCTION(BlueprintPure, Category="Food|Achievements")
    bool IsJournalShowing() const;

    /** True while the recipe sheet (the journal's host overlay) is on screen. */
    UFUNCTION(BlueprintPure, Category="Food|Achievements")
    bool IsRecipeVisible() const;

private:
    void InspectActor(AActor* Actor);
    void CheckChefApproval();
    void Unlock(FName Id);
    void Save();
    void BuildMedalBrushes();
    void UpdateRecipeUI();
    void StyleTextPanels();
    void FixRecipeTitleLayout();
    void RebuildJournal();
    void RemoveJournal();
    void SyncRecipeSheetVisibility();
    void ShowNextPopup();
    void RemovePopup();
    void UpdateMemoryNotifications();
    int32 FindDefinition(FName Id) const;

    UPROPERTY(Transient)
    TObjectPtr<UFoodAchievementSaveGame> SaveData;
    UPROPERTY(Transient)
    TArray<TObjectPtr<UTexture2D>> MedalTextures;
    UPROPERTY(Transient)
    TObjectPtr<UTexture2D> TextPanelTexture;
    FSlateBrush TextPanelBrush;
    TArray<TWeakObjectPtr<UObject>> StyledTextPanels;
    TArray<FSlateBrush> MedalBrushes;
    TArray<int32> PopupQueue;
    // 成就弹窗与手记提示都由控件蓝图驱动（内容/背景/位置都在蓝图里改）
    TWeakObjectPtr<UUserWidget> PopupWidget;
    TWeakObjectPtr<UBorder> PopupBorder;
    TWeakObjectPtr<UImage> PopupMedal;
    TWeakObjectPtr<UTextBlock> PopupSparkle;
    // 手记面板由 WBP_Journal 驱动；顶部的“食谱 / 厨房手记”切换条还留在 Slate，因为它带点击回调
    TWeakObjectPtr<UUserWidget> JournalWidget;
    TWeakObjectPtr<UScrollBox> MemoryScroll;
    TSharedPtr<SWidget> JournalTabStrip;
    TWeakObjectPtr<UUserWidget> MemoryToast;
    TArray<int32> MemoryToastQueue;
    bool bMemoryNotified[6] = {};
    double MemoryToastStart = 0.0;
    double PopupStartTime = 0.0;
    float RecipeScanAccumulator = 0.0f;
    bool bRecipeVisible = false;
    bool bJournalOpen = false;
    bool bRecipeTitleAligned = false;
    bool bLeftHeld = false;
    bool bRightHeld = false;
    bool bUpHeld = false;
    bool bDownHeld = false;
    bool bRecipeMovementLocked = false;
    bool bDoughComplete = false;
    bool bDoughPerfect = false;
    bool bFishCut = false;
    bool bOnionCut = false;
    bool bParsleyCut = false;
    bool bHeadsComplete = false;
    bool bFillingReady = false;
    bool bBakePerfect = false;
    bool bPieFinished = false;
    bool bEndingSeen = false;
};
