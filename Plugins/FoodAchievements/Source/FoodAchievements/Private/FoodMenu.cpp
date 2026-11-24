#include "FoodMenu.h"
#include "FoodProgress.h"
#include "FoodGraphTool.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/Image.h"
#include "Engine/Texture2D.h"
#include "Components/Slider.h"
#include "Components/TextBlock.h"
#include "Engine/Engine.h"
#include "EngineUtils.h"
#include "UObject/UnrealType.h"
#include "HAL/PlatformMisc.h"
#include "Engine/GameViewportClient.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "InputCoreTypes.h"
#include "Misc/CommandLine.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundMix.h"
#include "Misc/ConfigCacheIni.h"
#include "UObject/StrongObjectPtr.h"
#include "UnrealClient.h"
#include "Widgets/SCompoundWidget.h"

// 菜单布局全部在 /Game/UI/Widgets/Menus 下的蓝图里，这里只负责创建与回调。
namespace FoodMenu
{
enum class EPage { None, Main, Pause, SettingsMain, SettingsPause, ConfirmRestart, ConfirmMain, Ending };

static TWeakObjectPtr<UWorld> ActiveWorld;
static TSharedPtr<SWidget> Root;
static EPage Page = EPage::None;
static bool bInitialized = false, bSkipMain = false, bWasEnding = false, bEndingShown = false;
static bool bEndingAudioVisible = false;
static bool bEscapeHeld = false;
static TWeakObjectPtr<UUserWidget> PageWidget;
static TArray<TStrongObjectPtr<UFoodMenuAction>> ActionPool;
static TWeakObjectPtr<UUserWidget> OldPauseWidget;
static float MasterVolume = 1.f, EnvironmentVolume = 1.f, MusicVolume = 0.7f, EffectsVolume = 1.f;

static void Show(UWorld* W, EPage NewPage);
static void Close(UWorld* W);
static void ClearPage(UWorld* W);
static void HandleEscape(UWorld* W);

static void LoadVolumes()
{
    GConfig->GetFloat(TEXT("FoodAudio"), TEXT("Master"), MasterVolume, GGameUserSettingsIni);
    GConfig->GetFloat(TEXT("FoodAudio"), TEXT("Environment"), EnvironmentVolume, GGameUserSettingsIni);
    GConfig->GetFloat(TEXT("FoodAudio"), TEXT("Music"), MusicVolume, GGameUserSettingsIni);
    GConfig->GetFloat(TEXT("FoodAudio"), TEXT("Effects"), EffectsVolume, GGameUserSettingsIni);
    MasterVolume=FMath::Clamp(MasterVolume,0.f,1.f); EnvironmentVolume=FMath::Clamp(EnvironmentVolume,0.f,1.f); MusicVolume=FMath::Clamp(MusicVolume,0.f,1.f); EffectsVolume=FMath::Clamp(EffectsVolume,0.f,2.f);
}
static void SaveVolumes()
{
    GConfig->SetFloat(TEXT("FoodAudio"), TEXT("Master"), MasterVolume, GGameUserSettingsIni);
    GConfig->SetFloat(TEXT("FoodAudio"), TEXT("Environment"), EnvironmentVolume, GGameUserSettingsIni);
    GConfig->SetFloat(TEXT("FoodAudio"), TEXT("Music"), MusicVolume, GGameUserSettingsIni);
    GConfig->SetFloat(TEXT("FoodAudio"), TEXT("Effects"), EffectsVolume, GGameUserSettingsIni);
    GConfig->Flush(false,GGameUserSettingsIni);
}
static void ApplyVolumes(UWorld* W, bool bPush=false)
{
    if (!W) return;
    USoundMix* Mix=LoadObject<USoundMix>(nullptr,TEXT("/Game/FoodAudio/SM_Volumes.SM_Volumes"));
    USoundClass* Master=LoadObject<USoundClass>(nullptr,TEXT("/Game/FoodAudio/SC_Master.SC_Master"));
    USoundClass* Env=LoadObject<USoundClass>(nullptr,TEXT("/Game/FoodAudio/SC_Environment.SC_Environment"));
    USoundClass* Music=LoadObject<USoundClass>(nullptr,TEXT("/Game/FoodAudio/SC_Music.SC_Music"));
    USoundClass* Effects=LoadObject<USoundClass>(nullptr,TEXT("/Game/FoodAudio/SC_Effects.SC_Effects"));
    if (!Mix || !Master || !Env || !Music || !Effects) return;
    UGameplayStatics::SetSoundMixClassOverride(W,Mix,Master,MasterVolume,1.f,0.f,true);
    UGameplayStatics::SetSoundMixClassOverride(W,Mix,Env,EnvironmentVolume,1.f,0.f,false);
    UGameplayStatics::SetSoundMixClassOverride(W,Mix,Music,MusicVolume,1.f,0.f,false);
    UGameplayStatics::SetSoundMixClassOverride(W,Mix,Effects,EffectsVolume,1.f,0.f,false);
    if (bPush) UGameplayStatics::PushSoundMixModifier(W,Mix);
}

/** 只负责键盘兜底：菜单本体是 UMG，Esc 行为与之前一致。 */
class SFoodMenuRoot : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SFoodMenuRoot) {} SLATE_END_ARGS()
    void Construct(const FArguments&, TSharedRef<SWidget> Content) { ChildSlot[Content]; }
    virtual bool SupportsKeyboardFocus() const override { return true; }
    virtual FReply OnKeyDown(const FGeometry&, const FKeyEvent& E) override
    {
        if (E.GetKey() == EKeys::Escape && ActiveWorld.IsValid())
        {
            HandleEscape(ActiveWorld.Get());
            return FReply::Handled();
        }
        return FReply::Unhandled();
    }
};

template <typename T>
static T* FindWidget(UUserWidget* Widget, const TCHAR* Name)
{
    if (!Widget || !Widget->WidgetTree) return nullptr;
    return Cast<T>(Widget->WidgetTree->FindWidget(FName(Name)));
}

static void PlayClick(UWorld* W)
{
    static double LastClick = -100.0;
    if (!W) return;
    const double Now = FPlatformTime::Seconds();
    if (Now - LastClick < 0.2) return;
    LastClick = Now;
    if (USoundBase* Click = LoadObject<USoundBase>(nullptr, TEXT("/Game/FoodAudio/SFX_TraySwitch.SFX_TraySwitch")))
        UGameplayStatics::PlaySound2D(W, Click, Page == EPage::Main ? 0.24f : 0.22f);
}

static void BindClick(UWorld* W, const TCHAR* WidgetName, TFunction<void()> Action)
{
    if (!PageWidget.IsValid()) return;
    UButton* Button = FindWidget<UButton>(PageWidget.Get(), WidgetName);
    if (!Button) return;
    UFoodMenuAction* Proxy = NewObject<UFoodMenuAction>(PageWidget.Get());
    TWeakObjectPtr<UWorld> WeakWorld(W);
    Proxy->ClickAction = [WeakWorld, Action]()
    {
        UWorld* World = WeakWorld.Get();
        PlayClick(World);
        Action();
    };
    ActionPool.Emplace(Proxy);
    Button->OnClicked.AddDynamic(Proxy, &UFoodMenuAction::HandleClick);
}

/** Scale：滑条 0..1 对应 0..Scale 的实际音量值。 */
static void BindSlider(UWorld* W, const TCHAR* WidgetName, float* Value, float Scale)
{
    if (!PageWidget.IsValid()) return;
    USlider* Slider = FindWidget<USlider>(PageWidget.Get(), WidgetName);
    if (!Slider) return;
    UFoodMenuAction* Proxy = NewObject<UFoodMenuAction>(PageWidget.Get());
    TWeakObjectPtr<UWorld> WeakWorld(W);
    Proxy->SlideAction = [WeakWorld, Value, Scale](float Normalized)
    {
        *Value = FMath::Clamp(Normalized, 0.f, 1.f) * Scale;
        if (UWorld* World = WeakWorld.Get())
        {
            ApplyVolumes(World);
            SaveVolumes();
        }
    };
    ActionPool.Emplace(Proxy);
    Slider->OnValueChanged.AddDynamic(Proxy, &UFoodMenuAction::HandleSlide);
}

static void SetText(const TCHAR* WidgetName, const TCHAR* Text)
{
    if (UTextBlock* Block = FindWidget<UTextBlock>(PageWidget.Get(), WidgetName))
        Block->SetText(FText::FromString(Text));
}

/** 界面挂在自建 Slate 容器里，只能整体摘掉容器（UWidget::RemoveFromParent 对 TakeWidget 无效）。 */
static void ClearPage(UWorld* W)
{
    if (Root.IsValid() && W && W->GetGameViewport())
        W->GetGameViewport()->RemoveViewportWidgetContent(Root.ToSharedRef());
    Root.Reset();
    PageWidget.Reset();
    ActionPool.Empty();
}

static void Travel(UWorld* W, bool bMain)
{
    if (!W) return;
    if (bMain) FoodProgress::Save(W);
    FoodProgress::SetActive(W, false);
    bSkipMain = !bMain;
    Close(W);
    UGameplayStatics::OpenLevel(W, FName(TEXT("/Game/0Input/map/Kitchen_white_final_supply")));
}

static void Close(UWorld* W)
{
    if (!W) return;
    const bool bBeginGame = Page == EPage::Main;
    if (OldPauseWidget.IsValid()) { OldPauseWidget->RemoveFromParent(); OldPauseWidget.Reset(); }
    ClearPage(W);
    Page = EPage::None;
    bEscapeHeld = true;
    UGameplayStatics::SetGamePaused(W, false);
    if (bBeginGame) UFoodGraphTool::SetBackgroundMusic(W, false);
    if (APlayerController* PC = W->GetFirstPlayerController()) { PC->bShowMouseCursor = false; PC->SetInputMode(FInputModeGameOnly()); }
}

static const TCHAR* PagePath(EPage InPage)
{
    switch (InPage)
    {
    case EPage::Main:           return TEXT("/Game/UI/Widgets/Menus/WBP_MainMenu.WBP_MainMenu_C");
    case EPage::Pause:          return TEXT("/Game/UI/Widgets/Menus/WBP_PauseMenu.WBP_PauseMenu_C");
    case EPage::SettingsMain:
    case EPage::SettingsPause:  return TEXT("/Game/UI/Widgets/Menus/WBP_SettingsMenu.WBP_SettingsMenu_C");
    case EPage::ConfirmRestart:
    case EPage::ConfirmMain:    return TEXT("/Game/UI/Widgets/Menus/WBP_ConfirmDialog.WBP_ConfirmDialog_C");
    case EPage::Ending:         return TEXT("/Game/UI/Widgets/Menus/WBP_EndingMenu.WBP_EndingMenu_C");
    default:                    return nullptr;
    }
}

static void Show(UWorld* W, EPage NewPage)
{
    if (!W || !W->GetGameViewport()) return;
    ClearPage(W);
    Page = NewPage;

    const TCHAR* ClassPath = PagePath(NewPage);
    UClass* WidgetClass = ClassPath ? LoadClass<UUserWidget>(nullptr, ClassPath) : nullptr;
    if (!WidgetClass)
    {
        UE_LOG(LogTemp, Warning, TEXT("[FoodMenu] 找不到菜单蓝图：%s"), ClassPath ? ClassPath : TEXT("(null)"));
        return;
    }

    UUserWidget* Widget = CreateWidget<UUserWidget>(W, WidgetClass);
    if (!Widget) return;
    PageWidget = Widget;

    const bool bMain = NewPage == EPage::Main || NewPage == EPage::SettingsMain;

    if (NewPage == EPage::Main)
    {
        UCanvasPanel* Canvas = Widget->WidgetTree ? Cast<UCanvasPanel>(Widget->WidgetTree->RootWidget) : nullptr;
        UButton* Start = FindWidget<UButton>(Widget, TEXT("Btn_Start"));
        UButton* Settings = FindWidget<UButton>(Widget, TEXT("Btn_Settings"));
        UButton* Quit = FindWidget<UButton>(Widget, TEXT("Btn_Quit"));
        if (Canvas && Start && Settings && Quit)
        {
            UButton* Continue = Widget->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("Btn_Continue"));
            Continue->SetStyle(Start->GetStyle());
            Continue->SetIsEnabled(FoodProgress::HasSave(W));
            UImage* StartLabel = FindWidget<UImage>(Widget, TEXT("Img_Start"));
            UTexture2D* ContinueLabel = LoadObject<UTexture2D>(nullptr, TEXT("/Game/UI/Art/Buttons/T_Label_continue.T_Label_continue"));
            if (StartLabel && ContinueLabel)
            {
                UCanvasPanel* LabelCanvas = Widget->WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Canvas_Continue"));
                UImage* Label = Widget->WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("Img_Continue"));
                FSlateBrush Brush = StartLabel->GetBrush();
                Brush.SetResourceObject(ContinueLabel);
                Label->SetBrush(Brush);
                if (UCanvasPanelSlot* S = LabelCanvas->AddChildToCanvas(Label))
                    if (UCanvasPanelSlot* StartSlot = Cast<UCanvasPanelSlot>(StartLabel->Slot)) { S->SetLayout(StartSlot->GetLayout()); S->SetAutoSize(StartSlot->GetAutoSize()); }
                if (UButtonSlot* S = Cast<UButtonSlot>(Continue->AddChild(LabelCanvas)))
                {
                    if (UButtonSlot* StartSlot = Cast<UButtonSlot>(Start->GetContentSlot()))
                    { S->SetHorizontalAlignment(StartSlot->GetHorizontalAlignment()); S->SetVerticalAlignment(StartSlot->GetVerticalAlignment()); S->SetPadding(StartSlot->GetPadding()); }
                }
            }
            else
            {
                UTextBlock* Label = Widget->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Txt_Continue"));
                Label->SetText(FText::FromString(TEXT("继续游戏")));
                Label->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 42));
                if (UButtonSlot* S=Cast<UButtonSlot>(Continue->AddChild(Label))) { S->SetHorizontalAlignment(HAlign_Center); S->SetVerticalAlignment(VAlign_Center); }
            }
            if(UCanvasPanelSlot* S=Canvas->AddChildToCanvas(Continue)){S->SetPosition(FVector2D(680.f,565.f));S->SetSize(FVector2D(560.f,125.f));}
            if(UCanvasPanelSlot* S=Cast<UCanvasPanelSlot>(Start->Slot))S->SetPosition(FVector2D(680.f,430.f));
            if(UCanvasPanelSlot* S=Cast<UCanvasPanelSlot>(Settings->Slot))S->SetPosition(FVector2D(680.f,700.f));
            if(UCanvasPanelSlot* S=Cast<UCanvasPanelSlot>(Quit->Slot))S->SetPosition(FVector2D(680.f,835.f));
            BindClick(W, TEXT("Btn_Continue"), [W] {
                if (FoodProgress::Restore(W)) { FoodProgress::SetActive(W,true); Close(W); }
                else { UE_LOG(LogTemp,Error,TEXT("Food progress restore failed; returning to a clean menu")); FoodProgress::SetActive(W,false); bSkipMain=false; UGameplayStatics::OpenLevel(W,FName(TEXT("/Game/0Input/map/Kitchen_white_final_supply"))); }
            });
        }
        BindClick(W, TEXT("Btn_Start"), [W] {
            if (!FoodProgress::Save(W)) { UE_LOG(LogTemp,Error,TEXT("Food new game save failed; menu retained")); return; }
            FoodProgress::SetActive(W,true); Close(W);
        });
        BindClick(W, TEXT("Btn_Settings"), [W] { Show(W, EPage::SettingsMain); });
        BindClick(W, TEXT("Btn_Quit"),     [W] { if (APlayerController* PC = W->GetFirstPlayerController()) PC->ConsoleCommand(TEXT("quit")); });
    }
    else if (NewPage == EPage::Pause)
    {
        FoodProgress::Save(W);
        BindClick(W, TEXT("Btn_Resume"),   [W] { Close(W); });
        BindClick(W, TEXT("Btn_Restart"),  [W] { Show(W, EPage::ConfirmRestart); });
        BindClick(W, TEXT("Btn_Settings"), [W] { Show(W, EPage::SettingsPause); });
        BindClick(W, TEXT("Btn_MainMenu"), [W] { Show(W, EPage::ConfirmMain); });
    }
    else if (NewPage == EPage::ConfirmRestart || NewPage == EPage::ConfirmMain)
    {
        const bool bRestart = NewPage == EPage::ConfirmRestart;
        SetText(TEXT("Txt_Confirm"), bRestart ? TEXT("确定重新开始") : TEXT("确定返回"));
        BindClick(W, TEXT("Btn_Confirm"), [W, bRestart] { Travel(W, !bRestart); });
        BindClick(W, TEXT("Btn_Cancel"),  [W] { Show(W, EPage::Pause); });
    }
    else if (NewPage == EPage::Ending)
    {
        // Extend the existing ending menu at runtime while preserving the original widget asset.
        UCanvasPanel* Canvas = Widget->WidgetTree ? Cast<UCanvasPanel>(Widget->WidgetTree->RootWidget) : nullptr;
        UButton* Again = FindWidget<UButton>(Widget, TEXT("Btn_Again"));
        UButton* Main = FindWidget<UButton>(Widget, TEXT("Btn_MainMenu"));
        if (Canvas && Again && Main)
        {
            UButton* Explore = Widget->WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("Btn_Explore"));
            UTextBlock* Label = Widget->WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Txt_Explore"));
            Explore->SetStyle(Again->GetStyle());
            if (UTextBlock* Reference = FindWidget<UTextBlock>(Widget, TEXT("Txt_Again")))
            {
                Label->SetFont(Reference->GetFont());
                Label->SetColorAndOpacity(Reference->GetColorAndOpacity());
                Label->SetShadowOffset(Reference->GetShadowOffset());
                Label->SetShadowColorAndOpacity(Reference->GetShadowColorAndOpacity());
            }
            Label->SetText(FText::FromString(TEXT("自由探索")));
            Label->SetJustification(ETextJustify::Center);
            if (UButtonSlot* LabelSlot = Cast<UButtonSlot>(Explore->AddChild(Label))) { LabelSlot->SetHorizontalAlignment(HAlign_Center); LabelSlot->SetVerticalAlignment(VAlign_Center); }
            if (UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Explore))
            { Slot->SetPosition(FVector2D(750.f, 430.f)); Slot->SetSize(FVector2D(420.f, 86.f)); }
            if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Again->Slot)) Slot->SetPosition(FVector2D(750.f, 526.f));
            if (UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Main->Slot)) Slot->SetPosition(FVector2D(750.f, 622.f));
            BindClick(W, TEXT("Btn_Explore"), [W] {
                Close(W);
                if (APlayerController* PC = W->GetFirstPlayerController()) { PC->ResetIgnoreMoveInput(); PC->ResetIgnoreLookInput(); }
                UFoodGraphTool::SetBackgroundMusic(W, true);
            });
        }
        BindClick(W, TEXT("Btn_Again"),    [W] { Travel(W, false); });
        BindClick(W, TEXT("Btn_MainMenu"), [W] { Travel(W, true); });
    }
    else
    {
        BindSlider(W, TEXT("Slider_Master"),      &MasterVolume,      1.f);
        BindSlider(W, TEXT("Slider_Environment"), &EnvironmentVolume, 1.f);
        BindSlider(W, TEXT("Slider_Effects"),     &EffectsVolume,     2.f);
        BindSlider(W, TEXT("Slider_Music"),       &MusicVolume,       1.f);
        if (USlider* S = FindWidget<USlider>(Widget, TEXT("Slider_Master")))      S->SetValue(MasterVolume);
        if (USlider* S = FindWidget<USlider>(Widget, TEXT("Slider_Environment"))) S->SetValue(EnvironmentVolume);
        if (USlider* S = FindWidget<USlider>(Widget, TEXT("Slider_Effects")))     S->SetValue(EffectsVolume / 2.f);
        if (USlider* S = FindWidget<USlider>(Widget, TEXT("Slider_Music")))       S->SetValue(MusicVolume);
        BindClick(W, TEXT("Btn_Fullscreen"), [W] { if (APlayerController* PC = W->GetFirstPlayerController()) PC->ConsoleCommand(TEXT("fullscreen")); });
        BindClick(W, TEXT("Btn_Back"),       [W, bMain] { Show(W, bMain ? EPage::Main : EPage::Pause); });
    }

    TSharedRef<SFoodMenuRoot> MenuWidget = SNew(SFoodMenuRoot, Widget->TakeWidget());
    Root = MenuWidget;
    // 30000：保证盖住托盘/提示等 HUD（它们也在万级层级）
    W->GetGameViewport()->AddViewportWidgetContent(MenuWidget, 30000);
    UGameplayStatics::SetGamePaused(W, true);
    if (APlayerController* PC = W->GetFirstPlayerController())
    {
        PC->bShowMouseCursor = true;
        FInputModeGameAndUI Mode;
        Mode.SetWidgetToFocus(MenuWidget);
        Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
        PC->SetInputMode(Mode);
    }
}

static void HandleEscape(UWorld* W)
{
    if (!W) return;
    if (Page == EPage::Pause) Close(W);
    else if (Page == EPage::SettingsPause || Page == EPage::ConfirmRestart || Page == EPage::ConfirmMain) Show(W, EPage::Pause);
    else if (Page == EPage::SettingsMain) Show(W, EPage::Main);
}

void Tick(UWorld* W)
{
    if (!W || !W->GetGameViewport() || !W->GetFirstPlayerController()) return;
    if (ActiveWorld.Get() != W) { ActiveWorld = W; bInitialized = false; bWasEnding = false; bEndingShown = false; bEndingAudioVisible = false; bEscapeHeld = false; OldPauseWidget.Reset(); Root.Reset(); Page = EPage::None; PageWidget.Reset(); ActionPool.Empty(); }
    if (!bInitialized) { bInitialized = true; LoadVolumes(); ApplyVolumes(W, true); if (bSkipMain) { bSkipMain = false; if (FoodProgress::Save(W)) FoodProgress::SetActive(W,true); UFoodGraphTool::SetBackgroundMusic(W, false); } else { Show(W,EPage::Main); return; } }
    const bool bMenuRestoreTest=FParse::Param(FCommandLine::Get(),TEXT("FoodProgressMenuRestore"));
    const bool bMenuNewTest=FParse::Param(FCommandLine::Get(),TEXT("FoodProgressMenuNew"));
    if ((bMenuRestoreTest || bMenuNewTest) && Page==EPage::Main && PageWidget.IsValid()) {
        static bool bTestClicked=false;
        if(!bTestClicked){bTestClicked=true;UButton* Button=FindWidget<UButton>(PageWidget.Get(),bMenuNewTest?TEXT("Btn_Start"):TEXT("Btn_Continue"));
            if(Button && Button->GetIsEnabled()){UE_LOG(LogTemp,Warning,TEXT("[FoodMenuTest] activating %s"),bMenuNewTest?TEXT("Start"):TEXT("Continue"));Button->OnClicked.Broadcast();}
            else UE_LOG(LogTemp,Error,TEXT("[FoodMenuTest] button missing or disabled"));
        }
    }
#if !UE_BUILD_SHIPPING
    if (FParse::Param(FCommandLine::Get(),TEXT("FoodProgressMenuRestart"))) {
        static int32 TestStage=0;
        static double ExitAt=0.0;
        auto FindBowl=[W]()->AActor* {for(TActorIterator<AActor> It(W);It;++It)if(It->GetClass()->GetName()==TEXT("BP_FillingBowl_C"))return *It;return nullptr;};
        if(TestStage==0 && Page==EPage::Main && PageWidget.IsValid()) {
            UButton* Start=FindWidget<UButton>(PageWidget.Get(),TEXT("Btn_Start"));
            if(Start){Start->OnClicked.Broadcast();AActor* Bowl=FindBowl();if(Bowl){if(FBoolProperty* P=FindFProperty<FBoolProperty>(Bowl->GetClass(),TEXT("HasFish")))P->SetPropertyValue_InContainer(Bowl,true);}
              const bool Saved=FoodProgress::Save(W);UE_LOG(LogTemp,Warning,TEXT("[FoodRestartTest] old progress saved=%d"),Saved);TestStage=1;Show(W,EPage::ConfirmRestart);
              if(UButton* Confirm=FindWidget<UButton>(PageWidget.Get(),TEXT("Btn_Confirm")))Confirm->OnClicked.Broadcast();
            }
        }else if(TestStage==1 && Page==EPage::None && !bSkipMain){
            TestStage=2;AActor* Bowl=FindBowl();if(Bowl){if(FBoolProperty* P=FindFProperty<FBoolProperty>(Bowl->GetClass(),TEXT("HasFish")))P->SetPropertyValue_InContainer(Bowl,true);}
            const bool Restored=FoodProgress::Restore(W);const FBoolProperty* Flag=Bowl?FindFProperty<FBoolProperty>(Bowl->GetClass(),TEXT("HasFish")):nullptr;
            const bool Passed=Restored && Flag && !Flag->GetPropertyValue_InContainer(Bowl);UE_LOG(LogTemp,Warning,TEXT("[FoodRestartTest] %s restored=%d"),Passed?TEXT("PASS"):TEXT("FAIL"),Restored);ExitAt=FPlatformTime::Seconds()+8.0;
        }
        else if(TestStage==2 && ExitAt>0.0 && FPlatformTime::Seconds()>=ExitAt){FPlatformMisc::RequestExit(false);return;}
    }
    if (FParse::Param(FCommandLine::Get(),TEXT("FoodProgressExplore"))) {
        static int32 ExploreStage=0;
        static double ExitAt=0.0;
        if(ExploreStage==0 && Page==EPage::Main) {
            ExploreStage=1; Show(W,EPage::Ending);
            UButton* Button=PageWidget.IsValid()?FindWidget<UButton>(PageWidget.Get(),TEXT("Btn_Explore")):nullptr;
            if(Button) Button->OnClicked.Broadcast();
            APlayerController* PC=W->GetFirstPlayerController();
            const bool Passed=Button && Page==EPage::None && !W->IsPaused() && PC && !PC->IsMoveInputIgnored() && !PC->IsLookInputIgnored();
            UE_LOG(LogTemp,Warning,TEXT("[FoodExploreTest] %s"),Passed?TEXT("PASS"):TEXT("FAIL")); ExitAt=FPlatformTime::Seconds()+8.0;
        } else if(ExploreStage==1 && FPlatformTime::Seconds()>=ExitAt){FPlatformMisc::RequestExit(false);return;}
    }
#endif
    if (Page == EPage::None && W->IsPaused())
    {
        UClass* PauseClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_PauseBasic.WBP_PauseBasic_C"));
        if (PauseClass) { TArray<UUserWidget*> Widgets; UWidgetBlueprintLibrary::GetAllWidgetsOfClass(W, Widgets, PauseClass, false); for (UUserWidget* Widget : Widgets) if (Widget && Widget->IsInViewport()) { OldPauseWidget = Widget; Widget->SetVisibility(ESlateVisibility::Collapsed); Show(W,EPage::Pause); return; } }
    }
    UClass* EndingClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_ChefEnding.WBP_ChefEnding_C"));
    bool bEndingVisible = false;
    if (EndingClass) { TArray<UUserWidget*> Widgets; UWidgetBlueprintLibrary::GetAllWidgetsOfClass(W, Widgets, EndingClass, false); for (UUserWidget* Widget : Widgets) if (Widget && Widget->IsInViewport() && Widget->IsVisible()) { bEndingVisible = true; break; } }
    if (bEndingVisible && !bEndingAudioVisible)
    {
        if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, TEXT("/Game/FoodAudio/SFX_PageFlip.SFX_PageFlip")))
            UGameplayStatics::PlaySound2D(W, Sound, 0.26f);
        UFoodGraphTool::SetEndingJournalMusic(W, true);
        UE_LOG(LogTemp, Log, TEXT("[FoodMenu] Ending journal opened: page sound"));
    }
    else if (!bEndingVisible && bEndingAudioVisible)
        UFoodGraphTool::SetEndingJournalMusic(W, false);
    bEndingAudioVisible = bEndingVisible;
    if (bWasEnding && !bEndingVisible && !bEndingShown && Page == EPage::None) { bEndingShown = true; Show(W,EPage::Ending); }
    bWasEnding |= bEndingVisible;

    // 临时自检：带 -FoodShot 启动时，菜单出现 1.5 秒后自动截图到 Saved/Screenshots
    static bool bShotTaken = false;
    static double ShotDeadline = 0.0;
    static bool bPageForced = false;
    FString PageArg;
    if (!bPageForced && FParse::Value(FCommandLine::Get(), TEXT("FoodPage="), PageArg))
    {
        bPageForced = true;
        if (PageArg.Equals(TEXT("Settings"), ESearchCase::IgnoreCase)) Show(W, EPage::SettingsMain);
        else if (PageArg.Equals(TEXT("Pause"), ESearchCase::IgnoreCase)) Show(W, EPage::Pause);
        else if (PageArg.Equals(TEXT("Confirm"), ESearchCase::IgnoreCase)) Show(W, EPage::ConfirmRestart);
        else if (PageArg.Equals(TEXT("Ending"), ESearchCase::IgnoreCase)) Show(W, EPage::Ending);
    }
    // TEMP-VERIFY 手记最后一页渲染，验证后删除
    static bool bChefEndingForced = false;
    if (!bChefEndingForced && FParse::Param(FCommandLine::Get(), TEXT("FoodChefEnding")))
    {
        bChefEndingForced = true;
        if (UClass* ChefClass = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_ChefEnding.WBP_ChefEnding_C")))
            if (UUserWidget* ChefWidget = CreateWidget<UUserWidget>(W, ChefClass)) ChefWidget->AddToViewport(20000);
    }
    if (!bShotTaken && (Page != EPage::None || bChefEndingForced) && FParse::Param(FCommandLine::Get(), TEXT("FoodShot")))
    {
        if (ShotDeadline == 0.0) ShotDeadline = FPlatformTime::Seconds() + 14.0;
        else if (FPlatformTime::Seconds() >= ShotDeadline)
        {
            bShotTaken = true;
            if (bChefEndingForced && W && W->GetGameViewport())
            {
                // TEMP-VERIFY 量一下实际几何，验证后删除
                const FVector2D VS = FVector2D(W->GetGameViewport()->Viewport->GetSizeXY());
                if (UClass* KC = LoadClass<UUserWidget>(nullptr, TEXT("/Game/UI/Widgets/Panels/WBP_ChefEnding.WBP_ChefEnding_C")))
                {
                    TArray<UUserWidget*> Ws;
                    UWidgetBlueprintLibrary::GetAllWidgetsOfClass(W, Ws, KC, false);
                    for (UUserWidget* Wd : Ws)
                    {
                        if (!Wd || !Wd->IsInViewport()) continue;
                        const FGeometry G = Wd->GetCachedGeometry();
                        UE_LOG(LogTemp, Warning, TEXT("[FoodMenu] ChefEnding widget pos=(%.1f,%.1f) size=(%.1f,%.1f) viewport=(%.1f,%.1f)"),
                               G.GetAbsolutePosition().X, G.GetAbsolutePosition().Y, G.GetAbsoluteSize().X, G.GetAbsoluteSize().Y, VS.X, VS.Y);
                        if (Wd->WidgetTree)
                        {
                            Wd->WidgetTree->ForEachWidget([&G](UWidget* C)
                            {
                                if (!C) return;
                                const FGeometry CG = C->GetTickSpaceGeometry();
                                UE_LOG(LogTemp, Warning, TEXT("[FoodMenu]   child %s abs=(%.1f,%.1f) size=(%.1f,%.1f)"),
                                       *C->GetName(), CG.GetAbsolutePosition().X, CG.GetAbsolutePosition().Y, CG.GetAbsoluteSize().X, CG.GetAbsoluteSize().Y);
                            });
                        }
                    }
                }
            }
            FScreenshotRequest::RequestScreenshot(FString(), true, true);
            UE_LOG(LogTemp, Warning, TEXT("[FoodMenu] 已请求截图，当前页 %d"), (int32)Page);
        }
    }
}

void Shutdown(UWorld* W)
{
    if (ActiveWorld.Get() == W)
    {
        ClearPage(W);
        ActiveWorld.Reset(); Page = EPage::None;
    }
}
}
