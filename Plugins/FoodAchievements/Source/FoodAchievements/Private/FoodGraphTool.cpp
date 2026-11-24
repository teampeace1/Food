#include "FoodGraphTool.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Components/AudioComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "UObject/UnrealType.h"
#if WITH_EDITOR
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "K2Node_Self.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#endif
FString UFoodGraphTool::InspectPieGraph()
{
    FString Out;
#if WITH_EDITOR
    UBlueprint* BP = LoadObject<UBlueprint>(nullptr, TEXT("/Game/FoodGameplay/BP_Pie.BP_Pie"));
    if (!BP) return TEXT("missing blueprint");
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (UEdGraph* Graph : Graphs) for (UEdGraphNode* Node : Graph->Nodes)
    {
        Out += FString::Printf(TEXT("\nGRAPH %s NODE %s %s\n"), *Graph->GetName(), *Node->GetName(), *Node->GetNodeTitle(ENodeTitleType::ListView).ToString());
        for (UEdGraphPin* Pin : Node->Pins) if (Pin) Out += FString::Printf(TEXT("  %s = [%s] text=[%s] links=%d\n"), *Pin->PinName.ToString(), *Pin->DefaultValue, *Pin->DefaultTextValue.ToString(), Pin->LinkedTo.Num());
    }
#endif
    return Out;
}
int32 UFoodGraphTool::ChangePieToFour()
{
#if WITH_EDITOR
    UBlueprint* BP = LoadObject<UBlueprint>(nullptr, TEXT("/Game/FoodGameplay/BP_Pie.BP_Pie"));
    if (!BP) return -1;
    int32 Changed = 0;
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (UEdGraph* Graph : Graphs) for (UEdGraphNode* Node : Graph->Nodes) for (UEdGraphPin* Pin : Node->Pins)
    {
        if (!Pin || Pin->LinkedTo.Num()) continue;
        FString NewValue = Pin->DefaultValue;
        if (Graph->GetName() == TEXT("PlaceHead") && Node->GetName() == TEXT("K2Node_CallFunction_57") && Pin->PinName == TEXT("B") && NewValue == TEXT("7")) NewValue = TEXT("4");
        NewValue.ReplaceInline(TEXT("7/7"), TEXT("4/4"));
        NewValue.ReplaceInline(TEXT("/7 个鱼头"), TEXT("/4 个鱼头"));
        NewValue.ReplaceInline(TEXT("放满 7 个鱼头"), TEXT("放满 4 个鱼头"));
        NewValue.ReplaceInline(TEXT("七个鱼头放好了"), TEXT("四个鱼头放好了"));
        if (NewValue != Pin->DefaultValue) { Node->Modify(); Pin->DefaultValue = NewValue; ++Changed; }
    }
    if (Changed) { FBlueprintEditorUtils::MarkBlueprintAsModified(BP); FKismetEditorUtilities::CompileBlueprint(BP); }
    return Changed;
#else
    return -1;
#endif
}
FString UFoodGraphTool::InspectGraph(const FString& AssetPath)
{
    FString Out;
#if WITH_EDITOR
    UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *AssetPath);
    if (!BP) return TEXT("missing blueprint");
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (UEdGraph* Graph : Graphs) for (UEdGraphNode* Node : Graph->Nodes)
    {
        Out += FString::Printf(TEXT("\nGRAPH %s NODE %s %s\n"), *Graph->GetName(), *Node->GetName(), *Node->GetNodeTitle(ENodeTitleType::ListView).ToString());
        for (UEdGraphPin* Pin : Node->Pins) if (Pin)
        {
            Out += FString::Printf(TEXT("  %s [%s] default=[%s] object=[%s]"), *Pin->PinName.ToString(), Pin->Direction == EGPD_Input ? TEXT("in") : TEXT("out"), *Pin->DefaultValue, *GetNameSafe(Pin->DefaultObject));
            for (UEdGraphPin* Link : Pin->LinkedTo) if (Link && Link->GetOwningNode()) Out += FString::Printf(TEXT(" -> %s.%s"), *Link->GetOwningNode()->GetName(), *Link->PinName.ToString());
            Out += TEXT("\n");
        }
    }
#endif
    return Out;
}
void UFoodGraphTool::PlayChop(AActor* Context)
{
    if (!Context || !Context->GetWorld()) return;
    static TMap<TWeakObjectPtr<AActor>, double> LastPlay;
    const double Now = Context->GetWorld()->GetTimeSeconds();
    if (const double* Last = LastPlay.Find(Context); Last && Now >= *Last && Now - *Last < 0.2) return;
    LastPlay.Add(Context, Now);
    if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, TEXT("/Game/FoodAudio/SFX_ChopHit.SFX_ChopHit")))
        UGameplayStatics::PlaySoundAtLocation(Context, Sound, Context->GetActorLocation(), 0.35f);
}
FString UFoodGraphTool::WireChopAudio()
{
#if WITH_EDITOR
    UBlueprint* BP = LoadObject<UBlueprint>(nullptr, TEXT("/Game/FoodGameplay/BP_ChoppingBoard.BP_ChoppingBoard"));
    if (!BP) return TEXT("missing blueprint");
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (UEdGraph* Graph : Graphs) if (Graph->GetName() == TEXT("Interact"))
    {
        UEdGraphNode* Source = nullptr; UEdGraphNode* Target = nullptr;
        for (UEdGraphNode* Node : Graph->Nodes)
        {
            if (Node->GetName() == TEXT("K2Node_VariableSet_3")) Source = Node;
            if (Node->GetName() == TEXT("K2Node_IfThenElse_6")) Target = Node;
            if (UK2Node_CallFunction* Existing = Cast<UK2Node_CallFunction>(Node); Existing && Existing->GetTargetFunction() == StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool, PlayChop))) { UEdGraphPin* ContextPin = Existing->FindPin(TEXT("Context")); if (!ContextPin) return TEXT("context missing"); if (ContextPin->LinkedTo.Num()) return TEXT("already wired"); Graph->Modify(); UK2Node_Self* Self = NewObject<UK2Node_Self>(Graph); Graph->AddNode(Self, true, false); Self->CreateNewGuid(); Self->PostPlacedNewNode(); Self->AllocateDefaultPins(); Self->NodePosX = Existing->NodePosX - 150; Self->NodePosY = Existing->NodePosY + 100; if (!GetDefault<UEdGraphSchema_K2>()->TryCreateConnection(Self->FindPin(TEXT("self")), ContextPin)) { Graph->RemoveNode(Self); return TEXT("self link failed"); } FBlueprintEditorUtils::MarkBlueprintAsModified(BP); FKismetEditorUtilities::CompileBlueprint(BP); return BP->Status == BS_Error ? TEXT("compile failed; do not save") : TEXT("context linked; save required"); }
        }
        if (!Source || !Target) return TEXT("nodes missing");
        UEdGraphPin* Out = Source->FindPin(TEXT("then")); UEdGraphPin* In = Target->FindPin(TEXT("execute"));
        if (!Out || !In || !Out->LinkedTo.Contains(In)) return TEXT("unexpected connection");
        Graph->Modify(); Source->Modify(); Target->Modify();
        UK2Node_CallFunction* Call = NewObject<UK2Node_CallFunction>(Graph);
        Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool, PlayChop)));
        Graph->AddNode(Call, true, false); Call->CreateNewGuid(); Call->PostPlacedNewNode(); Call->AllocateDefaultPins();
        Call->NodePosX = Source->NodePosX + 200; Call->NodePosY = Source->NodePosY + 160;
        const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
        Out->BreakLinkTo(In);
        if (!Schema->TryCreateConnection(Out, Call->GetExecPin()) || !Schema->TryCreateConnection(Call->GetThenPin(), In))
        { Graph->RemoveNode(Call); Schema->TryCreateConnection(Out, In); return TEXT("connection failed"); }
        FBlueprintEditorUtils::MarkBlueprintAsModified(BP); FKismetEditorUtilities::CompileBlueprint(BP);
        if (BP->Status == BS_Error) return TEXT("compile failed; do not save");
        return TEXT("wired and compiled; save required");
    }
    return TEXT("graph missing");
#else
    return TEXT("editor only");
#endif
}
namespace { TMap<TWeakObjectPtr<AActor>, TWeakObjectPtr<UAudioComponent>> WashSounds; }
void UFoodGraphTool::StartWashAudio(AActor* Context)
{
    if (!IsValid(Context) || !Context->GetRootComponent()) return;
    if (auto Existing = WashSounds.Find(Context); Existing && Existing->IsValid() && Existing->Get()->IsPlaying()) return;
    if (USoundBase* Start = LoadObject<USoundBase>(nullptr, TEXT("/Game/FoodAudio/SFX_WashStartPlan.SFX_WashStartPlan"))) UGameplayStatics::PlaySoundAtLocation(Context, Start, Context->GetActorLocation(), 0.35f);
    USoundBase* Sound = LoadObject<USoundBase>(nullptr, TEXT("/Game/FoodAudio/SFX_WaterPlan.SFX_WaterPlan"));
    if (!Sound) return;
    UAudioComponent* C = UGameplayStatics::SpawnSoundAttached(Sound, Context->GetRootComponent(), NAME_None, FVector::ZeroVector, EAttachLocation::KeepRelativeOffset, true, 0.30f, 1.f, 0.f, nullptr, nullptr, false);
    if (C) { C->bOverrideAttenuation = true; C->AttenuationOverrides.bAttenuate = true; C->AttenuationOverrides.bSpatialize = true; C->AttenuationOverrides.AttenuationShapeExtents = FVector(150.f, 0.f, 0.f); C->AttenuationOverrides.FalloffDistance = 1200.f; WashSounds.Add(Context, C); }
}
void UFoodGraphTool::StopWashAudio(AActor* Context)
{
    if (auto Entry = WashSounds.Find(Context)) { if (UAudioComponent* C = Entry->Get()) { C->Stop(); C->DestroyComponent(); } WashSounds.Remove(Context); }
}
FString UFoodGraphTool::WireWashAudio()
{
#if WITH_EDITOR
    UBlueprint* BP = LoadObject<UBlueprint>(nullptr, TEXT("/Game/FoodGameplay/BP_Sink.BP_Sink")); if (!BP) return TEXT("missing BP");
    struct FWire { const TCHAR* Graph; const TCHAR* Source; const TCHAR* Target; FName Function; };
    const FWire Wires[] = {
      {TEXT("Interact"), TEXT("K2Node_VariableSet_2"), TEXT("K2Node_CallFunction_12"), GET_FUNCTION_NAME_CHECKED(UFoodGraphTool, StartWashAudio)},
      {TEXT("Interact"), TEXT("K2Node_VariableSet_0"), TEXT("K2Node_CallFunction_18"), GET_FUNCTION_NAME_CHECKED(UFoodGraphTool, StopWashAudio)},
      {TEXT("EventGraph"), TEXT("K2Node_VariableSet_0"), TEXT("K2Node_CallFunction_10"), GET_FUNCTION_NAME_CHECKED(UFoodGraphTool, StopWashAudio)}
    };
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (const FWire& W : Wires) {
        UEdGraph* Graph = nullptr; for (UEdGraph* G : Graphs) if (G->GetName() == W.Graph) { Graph = G; break; }
        if (!Graph) return TEXT("missing graph");
        UEdGraphNode *Source=nullptr,*Target=nullptr; for (UEdGraphNode* N : Graph->Nodes) { if (N->GetName()==W.Source) Source=N; if (N->GetName()==W.Target) Target=N; }
        if (!Source || !Target) return TEXT("missing node");
        UEdGraphPin* Out=Source->FindPin(TEXT("then")); UEdGraphPin* In=Target->FindPin(TEXT("execute"));
        if (!Out || !In || !Out->LinkedTo.Contains(In)) return TEXT("unexpected edge");
        Graph->Modify(); Source->Modify(); Target->Modify();
        UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(Graph); Call->SetFromFunction(StaticClass()->FindFunctionByName(W.Function)); Graph->AddNode(Call,true,false); Call->CreateNewGuid(); Call->PostPlacedNewNode(); Call->AllocateDefaultPins(); Call->NodePosX=Source->NodePosX+180; Call->NodePosY=Source->NodePosY+120;
        UK2Node_Self* Self=NewObject<UK2Node_Self>(Graph); Graph->AddNode(Self,true,false); Self->CreateNewGuid(); Self->PostPlacedNewNode(); Self->AllocateDefaultPins(); Self->NodePosX=Call->NodePosX-100; Self->NodePosY=Call->NodePosY+120;
        const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();
        if (!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context")))) return TEXT("self connect failed");
        Out->BreakLinkTo(In); if (!Schema->TryCreateConnection(Out,Call->GetExecPin()) || !Schema->TryCreateConnection(Call->GetThenPin(),In)) return TEXT("exec connect failed");
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(BP); FKismetEditorUtilities::CompileBlueprint(BP);
    return BP->Status == BS_Error ? TEXT("compile failed; do not save") : TEXT("wired and compiled; save required");
#else
    return TEXT("editor only");
#endif
}
void UFoodGraphTool::FinishWashAudio(AActor* Context)
{
    if (!IsValid(Context)) return;
    if (USoundBase* Sound = LoadObject<USoundBase>(nullptr, TEXT("/Game/FoodAudio/SFX_WashFinish.SFX_WashFinish"))) UGameplayStatics::PlaySoundAtLocation(Context, Sound, Context->GetActorLocation(), 0.32f);
}
FString UFoodGraphTool::WireWashFinishAudio()
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/FoodGameplay/BP_Sink.BP_Sink")); if (!BP) return TEXT("missing BP");
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (UEdGraph* G : Graphs) if (G->GetName()==TEXT("EventGraph")) {
        UK2Node_CallFunction* Stop=nullptr; UEdGraphNode* Target=nullptr;
        for (UEdGraphNode* N : G->Nodes) { if (auto C=Cast<UK2Node_CallFunction>(N); C && C->GetTargetFunction()==StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,StopWashAudio))) Stop=C; if (N->GetName()==TEXT("K2Node_CallFunction_10")) Target=N; }
        if (!Stop || !Target) return TEXT("missing nodes");
        UEdGraphPin* Out=Stop->GetThenPin(); UEdGraphPin* In=Target->FindPin(TEXT("execute")); if (!Out || !In || !Out->LinkedTo.Contains(In)) return TEXT("unexpected edge");
        G->Modify(); Stop->Modify(); Target->Modify();
        UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G); Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,FinishWashAudio))); G->AddNode(Call,true,false); Call->CreateNewGuid(); Call->PostPlacedNewNode(); Call->AllocateDefaultPins(); Call->NodePosX=Stop->NodePosX+200; Call->NodePosY=Stop->NodePosY+120;
        UK2Node_Self* Self=NewObject<UK2Node_Self>(G); G->AddNode(Self,true,false); Self->CreateNewGuid(); Self->PostPlacedNewNode(); Self->AllocateDefaultPins(); Self->NodePosX=Call->NodePosX-100; Self->NodePosY=Call->NodePosY+100;
        const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();
        if (!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context")))) return TEXT("self link failed");
        Out->BreakLinkTo(In); if (!Schema->TryCreateConnection(Out,Call->GetExecPin()) || !Schema->TryCreateConnection(Call->GetThenPin(),In)) return TEXT("exec link failed");
        FBlueprintEditorUtils::MarkBlueprintAsModified(BP); FKismetEditorUtilities::CompileBlueprint(BP); return BP->Status==BS_Error ? TEXT("compile failed") : TEXT("wired; save required");
    }
    return TEXT("missing graph");
#else
    return TEXT("editor only");
#endif
}
void UFoodGraphTool::PlayTraySwitch(AActor* Context)
{
    if (!IsValid(Context) || !Context->GetWorld()) return;
    static TMap<TWeakObjectPtr<AActor>, double> Last; const double Now=Context->GetWorld()->GetTimeSeconds();
    if (const double* Prev=Last.Find(Context); Prev && Now>=*Prev && Now-*Prev<0.2) return;
    Last.Add(Context,Now);
    if (USoundBase* Sound=LoadObject<USoundBase>(nullptr,TEXT("/Game/FoodAudio/SFX_TrayPlan.SFX_TrayPlan"))) UGameplayStatics::PlaySound2D(Context,Sound,0.25f);
}
void UFoodGraphTool::PlayRecipeOpen(AActor* Context)
{
    if (!IsValid(Context)) return;
    if (USoundBase* Sound=LoadObject<USoundBase>(nullptr,TEXT("/Game/FoodAudio/SFX_TraySwitch.SFX_TraySwitch"))) UGameplayStatics::PlaySound2D(Context,Sound,0.28f);
    static TSet<TWeakObjectPtr<AActor>> MotifPlayed;
    for (auto It = MotifPlayed.CreateIterator(); It; ++It) if (!It->IsValid()) It.RemoveCurrent();
    if (!MotifPlayed.Contains(Context)) {
        MotifPlayed.Add(Context);
        if (USoundBase* Motif=LoadObject<USoundBase>(nullptr,TEXT("/Game/FoodAudio/SFX_MotifPlan.SFX_MotifPlan"))) UGameplayStatics::PlaySound2D(Context,Motif,0.20f);
    }

}
FString UFoodGraphTool::WireCharacterAudio()
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter")); if (!BP) return TEXT("missing BP");
    struct FWire { const TCHAR* Graph; const TCHAR* Source; const TCHAR* Target; FName Function; };
    const FWire Wires[]={
      {TEXT("EventGraph"),TEXT("K2Node_VariableSet_4"),TEXT("K2Node_VariableSet_5"),GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayTraySwitch)},
      {TEXT("EventGraph"),TEXT("K2Node_VariableSet_8"),TEXT("K2Node_VariableSet_9"),GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayTraySwitch)},
      {TEXT("EventGraph"),TEXT("K2Node_VariableSet_12"),TEXT("K2Node_VariableSet_13"),GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayTraySwitch)},
      {TEXT("OpenRecipePanel"),TEXT("K2Node_VariableSet_0"),TEXT("K2Node_VariableSet_1"),GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayRecipeOpen)}
    };
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (const auto& W:Wires) {
      UEdGraph* G=nullptr; for (auto Graph:Graphs) if (Graph->GetName()==W.Graph) {G=Graph;break;} if (!G) return TEXT("missing graph");
      UEdGraphNode *Source=nullptr,*Target=nullptr; for (auto N:G->Nodes) {if(N->GetName()==W.Source)Source=N; if(N->GetName()==W.Target)Target=N;} if(!Source||!Target)return TEXT("missing node");
      UEdGraphPin* Out=Source->FindPin(TEXT("then")); UEdGraphPin* In=Target->FindPin(TEXT("execute")); if(!Out||!In||!Out->LinkedTo.Contains(In))return TEXT("unexpected edge");
      G->Modify(); Source->Modify(); Target->Modify();
      UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G); Call->SetFromFunction(StaticClass()->FindFunctionByName(W.Function)); G->AddNode(Call,true,false); Call->CreateNewGuid(); Call->PostPlacedNewNode(); Call->AllocateDefaultPins(); Call->NodePosX=Source->NodePosX+200; Call->NodePosY=Source->NodePosY+120;
      UK2Node_Self* Self=NewObject<UK2Node_Self>(G); G->AddNode(Self,true,false); Self->CreateNewGuid(); Self->PostPlacedNewNode(); Self->AllocateDefaultPins(); Self->NodePosX=Call->NodePosX-100; Self->NodePosY=Call->NodePosY+100;
      const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>(); if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self link failed");
      Out->BreakLinkTo(In); if(!Schema->TryCreateConnection(Out,Call->GetExecPin())||!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("exec link failed");
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(BP); FKismetEditorUtilities::CompileBlueprint(BP); return BP->Status==BS_Error ? TEXT("compile failed") : TEXT("wired; save required");
#else
    return TEXT("editor only");
#endif
}
void UFoodGraphTool::PlayCookingCue(AActor* Context, FName Cue)
{
    if (!IsValid(Context) || !Context->GetWorld()) return;
    const TCHAR* Path = nullptr; float Volume = 0.33f;
    if (Cue == TEXT("RollSuccess")) Path=TEXT("/Game/FoodAudio/SFX_RollSuccess.SFX_RollSuccess");
    else if (Cue == TEXT("RollFailure")) Path=TEXT("/Game/FoodAudio/SFX_RollFailure.SFX_RollFailure");
    else if (Cue == TEXT("FillingReady")) { Path=TEXT("/Game/FoodAudio/SFX_FillingReady.SFX_FillingReady"); Volume=0.32f; }
    else if (Cue == TEXT("IngredientPlacement")) { Path=TEXT("/Game/FoodAudio/SFX_IngredientPlacement.SFX_IngredientPlacement"); Volume=0.30f; }
    else if (Cue == TEXT("Seasoning")) { Path=TEXT("/Game/FoodAudio/SFX_Seasoning.SFX_Seasoning"); Volume=0.27f; }
    else if (Cue == TEXT("HeadPlaced")) { Path=TEXT("/Game/FoodAudio/SFX_IngredientPickup.SFX_IngredientPickup"); Volume=0.30f; }
    else if (Cue == TEXT("OvenInsert")) { Path=TEXT("/Game/FoodAudio/SFX_OvenInsert.SFX_OvenInsert"); Volume=0.33f; }
    else if (Cue == TEXT("BakeSuccess")) { Path=TEXT("/Game/FoodAudio/SFX_BakeSuccess.SFX_BakeSuccess"); Volume=0.34f; }
    else if (Cue == TEXT("BakeFailure")) { Path=TEXT("/Game/FoodAudio/SFX_RollFailure.SFX_RollFailure"); Volume=0.34f; }
    else if (Cue == TEXT("IngredientPickup")) { Path=TEXT("/Game/FoodAudio/SFX_IngredientPickup.SFX_IngredientPickup"); Volume=0.30f; }
    else if (Cue == TEXT("IngredientDrop")) {
        const FObjectPropertyBase* P=FindFProperty<FObjectPropertyBase>(Context->GetClass(),TEXT("HeldActor"));
        const AActor* Held=P ? Cast<AActor>(P->GetObjectPropertyValue_InContainer(Context)) : nullptr;
        if (!Held || !Held->GetClass()->GetName().Contains(TEXT("BP_Ingredient"))) return;
        Path=TEXT("/Game/FoodAudio/SFX_IngredientDrop.SFX_IngredientDrop"); Volume=0.28f;
    }
    else if (Cue == TEXT("Warning") || Cue == TEXT("TrayFull")) {
        static TMap<TWeakObjectPtr<AActor>,double> LastWarning;
        const double Now=Context->GetWorld()->GetTimeSeconds();
        if(const double* Prev=LastWarning.Find(Context);Prev && Now>=*Prev && Now-*Prev<0.2)return;
        LastWarning.Add(Context,Now);
        if(USoundBase* Warning=LoadObject<USoundBase>(nullptr,TEXT("/Game/FoodAudio/SFX_Warning.SFX_Warning"))) UGameplayStatics::PlaySound2D(Context,Warning,Cue==TEXT("TrayFull")?0.35f:0.32f);
        return;
    }
    else if (Cue == TEXT("HeadComplete")) { Path=TEXT("/Game/FoodAudio/SFX_FillingReady.SFX_FillingReady"); Volume=0.30f; }
    else if (Cue == TEXT("RecipeClose")) {
        const FStrProperty* P=FindFProperty<FStrProperty>(Context->GetClass(),TEXT("PanelKind"));
        if (!P || P->GetPropertyValue_InContainer(Context)!=TEXT("Recipe")) return;
        if(USoundBase* Sound=LoadObject<USoundBase>(nullptr,TEXT("/Game/FoodAudio/SFX_TraySwitch.SFX_TraySwitch"))) UGameplayStatics::PlaySound2D(Context,Sound,0.28f);
        return;
    }
    else if (Cue == TEXT("PieBase")) { Path=TEXT("/Game/FoodAudio/SFX_PieBase.SFX_PieBase"); Volume=0.28f; }
    if (!Path) return;
    static TMap<TWeakObjectPtr<AActor>,TMap<FName,double>> Last; const double Now=Context->GetWorld()->GetTimeSeconds();
    if (const double* Previous=Last.FindOrAdd(Context).Find(Cue); Previous && Now>=*Previous && Now-*Previous<0.2) return;
    Last.FindOrAdd(Context).Add(Cue,Now);
    if (USoundBase* Sound=LoadObject<USoundBase>(nullptr,Path)) UGameplayStatics::PlaySoundAtLocation(Context,Sound,Context->GetActorLocation(),Volume);
}
FString UFoodGraphTool::WirePlanCues(const FString& AssetPath)
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,*AssetPath); if (!BP) return TEXT("missing blueprint");
    struct FWire { const TCHAR* Graph; const TCHAR* Source; const TCHAR* Target; const TCHAR* Cue; };
    TArray<FWire> Wires;
    if (AssetPath.Contains(TEXT("BP_RollingStation"))) {
      Wires.Add({TEXT("FinishRolling"),TEXT("K2Node_VariableSet_12"),TEXT("K2Node_CallFunction_25"),TEXT("RollFailure")});
      Wires.Add({TEXT("FinishRolling"),TEXT("K2Node_VariableSet_15"),TEXT("K2Node_CallFunction_28"),TEXT("RollSuccess")});
      Wires.Add({TEXT("FinishRolling"),TEXT("K2Node_VariableSet_1"),TEXT("K2Node_CallFunction_1"),TEXT("RollFailure")});
    } else if (AssetPath.Contains(TEXT("BP_FillingBowl"))) {
      Wires.Add({TEXT("ConsumeHeld"),TEXT("K2Node_VariableSet_4"),TEXT("K2Node_DynamicCast_2"),TEXT("FillingReady")});
    } else return TEXT("unsupported BP");
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs); const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();
    for (const auto& W:Wires) {
      UEdGraph* G=nullptr; for (auto Graph:Graphs) if (Graph->GetName()==W.Graph) {G=Graph;break;} if(!G)return TEXT("missing graph");
      UEdGraphNode *Source=nullptr,*Target=nullptr; for(auto N:G->Nodes) {if(N->GetName()==W.Source) Source=N; if(N->GetName()==W.Target) Target=N;}
      if(!Source||!Target)return TEXT("missing node"); UEdGraphPin* Out=Source->FindPin(TEXT("then")); UEdGraphPin* In=Target->FindPin(TEXT("execute")); if(!Out||!In||!Out->LinkedTo.Contains(In))return TEXT("unexpected edge");
      G->Modify(); Source->Modify(); Target->Modify(); UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G); Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayCookingCue))); G->AddNode(Call,true,false); Call->CreateNewGuid(); Call->PostPlacedNewNode(); Call->AllocateDefaultPins(); Call->NodePosX=Source->NodePosX+200; Call->NodePosY=Source->NodePosY+120;
      UK2Node_Self* Self=NewObject<UK2Node_Self>(G);G->AddNode(Self,true,false);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX-100;Self->NodePosY=Call->NodePosY+100;
      UEdGraphPin* CuePin=Call->FindPin(TEXT("Cue"));if(!CuePin)return TEXT("missing cue pin");CuePin->DefaultValue=W.Cue;
      if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self connect failed");
      Out->BreakLinkTo(In);if(!Schema->TryCreateConnection(Out,Call->GetExecPin())||!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("exec connect failed");
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error ? TEXT("compile failed") : TEXT("wired; save required");
#else
    return TEXT("editor only");
#endif
}
FString UFoodGraphTool::WireAdditionalCues(const FString& AssetPath)
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,*AssetPath);if(!BP)return TEXT("missing blueprint");
    struct FWire {const TCHAR* Graph;const TCHAR* Source;const TCHAR* Target;const TCHAR* Cue;};TArray<FWire> Wires;
    if(AssetPath.Contains(TEXT("BP_FillingBowl"))){
      Wires.Add({TEXT("Interact"),TEXT("K2Node_VariableSet_6"),TEXT("K2Node_CallFunction_16"),TEXT("IngredientPlacement")});
      Wires.Add({TEXT("Interact"),TEXT("K2Node_VariableSet_7"),TEXT("K2Node_CallFunction_21"),TEXT("IngredientPlacement")});
      Wires.Add({TEXT("Interact"),TEXT("K2Node_VariableSet_8"),TEXT("K2Node_CallFunction_26"),TEXT("IngredientPlacement")});
      Wires.Add({TEXT("Interact"),TEXT("K2Node_VariableSet_9"),TEXT("K2Node_CallFunction_30"),TEXT("Seasoning")});
    }else if(AssetPath.Contains(TEXT("BP_Oven"))){
      Wires.Add({TEXT("ReceivePie"),TEXT("K2Node_VariableSet_5"),TEXT("K2Node_VariableSet_6"),TEXT("OvenInsert")});
      Wires.Add({TEXT("Interact"),TEXT("K2Node_VariableSet_2"),TEXT("K2Node_CallFunction_3"),TEXT("BakeSuccess")});
      Wires.Add({TEXT("Interact"),TEXT("K2Node_VariableSet_3"),TEXT("K2Node_CallFunction_5"),TEXT("BakeFailure")});
    }else if(AssetPath.Contains(TEXT("BP_Pie"))){Wires.Add({TEXT("PlaceHead"),TEXT("K2Node_VariableSet_17"),TEXT("K2Node_IfThenElse_2"),TEXT("HeadPlaced")});}
    else if(AssetPath.Contains(TEXT("BP_FirstPersonCharacter"))){
      Wires.Add({TEXT("EventGraph"),TEXT("K2Node_VariableSet_36"),TEXT("K2Node_VariableSet_37"),TEXT("IngredientPickup")});
      Wires.Add({TEXT("DropHeldItem"),TEXT("K2Node_CallFunction_2"),TEXT("K2Node_VariableSet_0"),TEXT("IngredientDrop")});
    }
    else return TEXT("unsupported BP");
    TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();
    for(const auto& W:Wires){
      UEdGraph* G=nullptr;for(auto Graph:Graphs)if(Graph->GetName()==W.Graph){G=Graph;break;}if(!G)return TEXT("missing graph");
      UEdGraphNode *Source=nullptr,*Target=nullptr;for(auto N:G->Nodes){if(N->GetName()==W.Source)Source=N;if(N->GetName()==W.Target)Target=N;}if(!Source||!Target)return TEXT("missing node");
      UEdGraphPin* Out=Source->FindPin(TEXT("then"));UEdGraphPin* In=Target->FindPin(TEXT("execute"));if(!Out||!In||!Out->LinkedTo.Contains(In))return TEXT("unexpected edge");
      G->Modify();Source->Modify();Target->Modify();UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayCookingCue)));G->AddNode(Call,true,false);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodePosX=Source->NodePosX+200;Call->NodePosY=Source->NodePosY+120;
      UK2Node_Self* Self=NewObject<UK2Node_Self>(G);G->AddNode(Self,true,false);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX-100;Self->NodePosY=Call->NodePosY+100;
      UEdGraphPin* CuePin=Call->FindPin(TEXT("Cue"));if(!CuePin)return TEXT("missing cue pin");CuePin->DefaultValue=W.Cue;if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self connect failed");
      Out->BreakLinkTo(In);if(!Schema->TryCreateConnection(Out,Call->GetExecPin())||!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("exec connect failed");
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error?TEXT("compile failed"):TEXT("wired; save required");
#else
    return TEXT("editor only");
#endif
}
namespace {
TMap<TWeakObjectPtr<AActor>,TWeakObjectPtr<UAudioComponent>> CookingLoops;
enum class EFoodMusic : uint8 { Game, Baking, Ending };
void SetFoodMusic(UWorld* World, EFoodMusic Track, bool bJournalVisible=false);
}
void UFoodGraphTool::SetCookingLoop(AActor* Context, FName Loop, bool bStart)
{
    if (!IsValid(Context)) return;
    // Baking music continues until the ending track takes over, including after the oven loop stops.
    if (bStart && Loop==TEXT("Oven")) SetFoodMusic(Context->GetWorld(), EFoodMusic::Baking);
    if (!bStart) { if(auto Entry=CookingLoops.Find(Context)) { if(UAudioComponent* Audio=Entry->Get()) { Audio->Stop();Audio->DestroyComponent(); } CookingLoops.Remove(Context); } return; }
    if (auto Entry=CookingLoops.Find(Context);Entry && Entry->IsValid() && Entry->Get()->IsPlaying()) return;
    const TCHAR* Path=nullptr;float Volume=0.3f;
    if(Loop==TEXT("Roll"))Path=TEXT("/Game/FoodAudio/SFX_RollLoop.SFX_RollLoop");
    else if(Loop==TEXT("Oven")){Path=TEXT("/Game/FoodAudio/SFX_OvenLoop.SFX_OvenLoop");Volume=0.20f;}
    if(!Path||!Context->GetRootComponent())return;
    if(USoundBase* Sound=LoadObject<USoundBase>(nullptr,Path)) {
      UAudioComponent* Audio=UGameplayStatics::SpawnSoundAttached(Sound,Context->GetRootComponent(),NAME_None,FVector::ZeroVector,EAttachLocation::KeepRelativeOffset,true,Volume,1.f,0.f,nullptr,nullptr,false);
      if(Audio)CookingLoops.Add(Context,Audio);
    }
}
FString UFoodGraphTool::WireCookingLoops(const FString& AssetPath)
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,*AssetPath);if(!BP)return TEXT("missing BP");
    struct FWire{const TCHAR* Graph;const TCHAR* Source;const TCHAR* Target;const TCHAR* Loop;bool Start;};TArray<FWire> W;
    if(AssetPath.Contains(TEXT("BP_RollingStation"))){
      W.Add({TEXT("BeginRolling"),TEXT("K2Node_VariableSet_8"),TEXT("K2Node_CreateWidget_1"),TEXT("Roll"),true});
      W.Add({TEXT("StartRolling"),TEXT("K2Node_VariableSet_7"),TEXT("K2Node_CallFunction_8"),TEXT("Roll"),true});
      W.Add({TEXT("FinishRolling"),TEXT("K2Node_VariableSet_10"),TEXT("K2Node_IfThenElse_12"),TEXT("Roll"),false});
      W.Add({TEXT("CancelRolling"),TEXT("K2Node_VariableSet_3"),TEXT("K2Node_IfThenElse_1"),TEXT("Roll"),false});
    }else if(AssetPath.Contains(TEXT("BP_Oven"))){
      W.Add({TEXT("Interact"),TEXT("K2Node_VariableSet_5"),TEXT("K2Node_VariableSet_6"),TEXT("Oven"),true});
      W.Add({TEXT("EventGraph"),TEXT("K2Node_VariableSet_4"),TEXT("K2Node_VariableSet_5"),TEXT("Oven"),false});
    }else return TEXT("unsupported BP");
    TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();
    for(const auto& R:W){
      UEdGraph* G=nullptr;for(auto X:Graphs)if(X->GetName()==R.Graph){G=X;break;}if(!G)return TEXT("missing graph");
      UEdGraphNode *S=nullptr,*T=nullptr;for(auto N:G->Nodes){if(N->GetName()==R.Source)S=N;if(N->GetName()==R.Target)T=N;}if(!S||!T)return TEXT("missing node");
      UEdGraphPin* Out=S->FindPin(TEXT("then"));UEdGraphPin* In=T->FindPin(TEXT("execute"));if(!Out||!In||!Out->LinkedTo.Contains(In))return TEXT("unexpected edge");
      G->Modify();S->Modify();T->Modify();UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,SetCookingLoop)));G->AddNode(Call,true,false);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodePosX=S->NodePosX+200;Call->NodePosY=S->NodePosY+120;
      UK2Node_Self* Self=NewObject<UK2Node_Self>(G);G->AddNode(Self,true,false);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX-100;Self->NodePosY=Call->NodePosY+100;
      UEdGraphPin* LoopPin=Call->FindPin(TEXT("Loop"));UEdGraphPin* StartPin=Call->FindPin(TEXT("bStart"));if(!LoopPin||!StartPin)return TEXT("missing pin");LoopPin->DefaultValue=R.Loop;StartPin->DefaultValue=R.Start?TEXT("true"):TEXT("false");
      if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self failed");Out->BreakLinkTo(In);if(!Schema->TryCreateConnection(Out,Call->GetExecPin())||!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("exec failed");
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error?TEXT("compile failed"):TEXT("wired; save required");
#else
    return TEXT("editor only");
#endif
}
FString UFoodGraphTool::WirePlacementWarnings(const FString& AssetPath)
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,*AssetPath);if(!BP)return TEXT("missing BP");
    struct FTarget{const TCHAR* Graph;const TCHAR* Node;const TCHAR* Text;const TCHAR* Cue;};TArray<FTarget> Targets;
    if(AssetPath.Contains(TEXT("BP_ChoppingBoard"))){
      Targets.Add({TEXT("Interact"),TEXT("K2Node_CallFunction_3"),TEXT("这个食材不能切配"),TEXT("Warning")});
      Targets.Add({TEXT("Interact"),TEXT("K2Node_CallFunction_7"),TEXT("请先清洗"),TEXT("Warning")});
    }else if(AssetPath.Contains(TEXT("BP_RollingStation"))){
      Targets.Add({TEXT("BeginRolling"),TEXT("K2Node_CallFunction_15"),TEXT("这里只能擀面团"),TEXT("Warning")});
      Targets.Add({TEXT("BeginRolling"),TEXT("K2Node_CallFunction_18"),TEXT("这里只能擀面团"),TEXT("Warning")});
      Targets.Add({TEXT("BeginRolling"),TEXT("K2Node_CallFunction_20"),TEXT("需要原始面团；失败后请领取备用面团重做"),TEXT("Warning")});
      Targets.Add({TEXT("StartRolling"),TEXT("K2Node_CallFunction_3"),TEXT("这个食材不能擀制"),TEXT("Warning")});
    }else if(AssetPath.Contains(TEXT("BP_FillingBowl"))){Targets.Add({TEXT("Interact"),TEXT("K2Node_CallFunction_31"),TEXT("这个不能放进馅料"),TEXT("Warning")});}
    else if(AssetPath.Contains(TEXT("BP_Pie"))){
      Targets.Add({TEXT("Interact"),TEXT("K2Node_CallFunction_68"),TEXT("这里只能放鱼头"),TEXT("Warning")});
      Targets.Add({TEXT("Interact"),TEXT("K2Node_CallFunction_73"),TEXT("只能是洗干净的鱼头"),TEXT("Warning")});
      Targets.Add({TEXT("PickupPie"),TEXT("K2Node_CallFunction_7"),TEXT("托盘已满，请先腾出一个格子"),TEXT("TrayFull")});
    }else if(AssetPath.Contains(TEXT("BP_Oven"))){
      Targets.Add({TEXT("ReceivePie"),TEXT("K2Node_CallFunction_6"),TEXT("请先从装配台拿起完整的派"),TEXT("Warning")});
      Targets.Add({TEXT("ReceivePie"),TEXT("K2Node_CallFunction_7"),TEXT("请先完成馅料、派底和七个鱼头"),TEXT("Warning")});
      Targets.Add({TEXT("RetrievePie"),TEXT("K2Node_CallFunction_18"),TEXT("托盘已满，请先腾出一个格子"),TEXT("TrayFull")});
    }else if(AssetPath.Contains(TEXT("BP_FirstPersonCharacter"))){Targets.Add({TEXT("EventGraph"),TEXT("K2Node_CallFunction_111"),TEXT("托盘已满，请先按 G 放下食材"),TEXT("TrayFull")});}
    else return TEXT("unsupported BP");
    TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();
    for(const auto& R:Targets){
      UEdGraph* G=nullptr;for(auto X:Graphs)if(X->GetName()==R.Graph){G=X;break;}if(!G)return TEXT("missing graph");
      UEdGraphNode* T=nullptr;for(auto N:G->Nodes)if(N->GetName()==R.Node){T=N;break;}if(!T)return TEXT("missing node");
      UEdGraphPin* In=T->FindPin(TEXT("execute"));UEdGraphPin* Message=T->FindPin(TEXT("InString"));if(!In||!Message||Message->DefaultValue!=R.Text||In->LinkedTo.IsEmpty())return TEXT("unexpected target");
      TArray<UEdGraphPin*> Sources=In->LinkedTo;G->Modify();T->Modify();for(auto P:Sources)if(P->GetOwningNode())P->GetOwningNode()->Modify();
      UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayCookingCue)));G->AddNode(Call,true,false);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodePosX=T->NodePosX-200;Call->NodePosY=T->NodePosY+120;
      UK2Node_Self* Self=NewObject<UK2Node_Self>(G);G->AddNode(Self,true,false);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX-100;Self->NodePosY=Call->NodePosY+100;
      UEdGraphPin* Cue=Call->FindPin(TEXT("Cue"));if(!Cue)return TEXT("missing cue");Cue->DefaultValue=R.Cue;if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self connect failed");
      for(auto P:Sources){P->BreakLinkTo(In);if(!Schema->TryCreateConnection(P,Call->GetExecPin()))return TEXT("source link failed");}
      if(!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("target link failed");
    }
    FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error?TEXT("compile failed"):TEXT("wired; save required");
#else
    return TEXT("editor only");
#endif
}
FString UFoodGraphTool::FinishCueCorrections(const FString& AssetPath)
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,*AssetPath);if(!BP)return TEXT("missing BP");TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);
    if(AssetPath.Contains(TEXT("BP_RollingStation"))){
      for(UEdGraph* G:Graphs)if(G->GetName()==TEXT("FinishRolling"))for(UEdGraphNode* N:G->Nodes)if(N->GetName()==TEXT("K2Node_VariableSet_1")){
        UEdGraphPin* Out=N->FindPin(TEXT("then"));if(!Out||Out->LinkedTo.Num()!=1)return TEXT("unexpected thin edge");
        UK2Node_CallFunction* Call=Cast<UK2Node_CallFunction>(Out->LinkedTo[0]->GetOwningNode());if(!Call||Call->GetTargetFunction()!=StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayCookingCue)))return TEXT("missing cue");
        UEdGraphPin* Cue=Call->FindPin(TEXT("Cue"));if(!Cue||Cue->DefaultValue!=TEXT("RollFailure"))return TEXT("unexpected cue");Call->Modify();Cue->DefaultValue=TEXT("RollNormal");FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error?TEXT("compile failed"):TEXT("corrected; save required");
      }return TEXT("missing thin node");
    }
    if(AssetPath.Contains(TEXT("BP_Pie"))){
      for(UEdGraph* G:Graphs)if(G->GetName()==TEXT("PlaceHead")){
        UEdGraphNode *S=nullptr,*T=nullptr;for(auto N:G->Nodes){if(N->GetName()==TEXT("K2Node_VariableSet_19"))S=N;if(N->GetName()==TEXT("K2Node_CallFunction_58"))T=N;}
        if(!S||!T)return TEXT("missing completion node");UEdGraphPin* Out=S->FindPin(TEXT("then"));UEdGraphPin* In=T->FindPin(TEXT("execute"));UEdGraphPin* Msg=T->FindPin(TEXT("InString"));if(!Out||!In||!Out->LinkedTo.Contains(In)||!Msg||Msg->DefaultValue!=TEXT("四个鱼头放好了"))return TEXT("unexpected completion edge");
        G->Modify();S->Modify();T->Modify();UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayCookingCue)));G->AddNode(Call,true,false);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodePosX=S->NodePosX+180;Call->NodePosY=S->NodePosY+100;
        UK2Node_Self* Self=NewObject<UK2Node_Self>(G);G->AddNode(Self,true,false);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX-100;Self->NodePosY=Call->NodePosY+100;
        UEdGraphPin* Cue=Call->FindPin(TEXT("Cue"));if(!Cue)return TEXT("missing cue");Cue->DefaultValue=TEXT("HeadComplete");const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self failed");Out->BreakLinkTo(In);if(!Schema->TryCreateConnection(Out,Call->GetExecPin())||!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("edge failed");
        FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error?TEXT("compile failed"):TEXT("corrected; save required");
      }return TEXT("missing graph");
    }return TEXT("unsupported BP");
#else
    return TEXT("editor only");
#endif
}
FString UFoodGraphTool::WireRecipeClose()
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,TEXT("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter.BP_FirstPersonCharacter"));if(!BP)return TEXT("missing BP");TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);
    for(auto G:Graphs)if(G->GetName()==TEXT("CloseCookingPanel")){
      UEdGraphNode *S=nullptr,*T=nullptr;for(auto N:G->Nodes){if(N->GetName()==TEXT("K2Node_CallFunction_1"))S=N;if(N->GetName()==TEXT("K2Node_VariableSet_0"))T=N;}if(!S||!T)return TEXT("missing node");
      UEdGraphPin* Out=S->FindPin(TEXT("then"));UEdGraphPin* In=T->FindPin(TEXT("execute"));if(!Out||!In||!Out->LinkedTo.Contains(In))return TEXT("unexpected edge");
      G->Modify();S->Modify();T->Modify();UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayCookingCue)));G->AddNode(Call,true,false);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodePosX=S->NodePosX+200;Call->NodePosY=S->NodePosY+120;
      UK2Node_Self* Self=NewObject<UK2Node_Self>(G);G->AddNode(Self,true,false);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX-100;Self->NodePosY=Call->NodePosY+100;
      UEdGraphPin* Cue=Call->FindPin(TEXT("Cue"));if(!Cue)return TEXT("missing cue");Cue->DefaultValue=TEXT("RecipeClose");const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self failed");Out->BreakLinkTo(In);if(!Schema->TryCreateConnection(Out,Call->GetExecPin())||!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("exec failed");
      FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error?TEXT("compile failed"):TEXT("wired; save required");
    }return TEXT("missing graph");
#else
    return TEXT("editor only");
#endif
}
namespace {
void SetFoodMusic(UWorld* World, EFoodMusic Track, bool bJournalVisible)
{
    if(!World)return;
    struct FMusicState { TWeakObjectPtr<UAudioComponent> Audio; EFoodMusic Track=EFoodMusic::Game; };
    static TMap<TWeakObjectPtr<UWorld>,FMusicState> States;
    for(auto It=States.CreateIterator();It;++It)if(!It.Key().IsValid())It.RemoveCurrent();
    FMusicState& State=States.FindOrAdd(World);
    // A menu close or save restore must not replace later-stage music with an earlier track.
    if(State.Audio.IsValid() && static_cast<uint8>(State.Track)>=static_cast<uint8>(Track)){
        if(State.Track==EFoodMusic::Ending && Track==EFoodMusic::Ending) State.Audio->SetUISound(bJournalVisible);
        return;
    }
    const TCHAR* Path=Track==EFoodMusic::Ending?TEXT("/Game/FoodAudio/BGM_Ending.BGM_Ending"):
        Track==EFoodMusic::Baking?TEXT("/Game/FoodAudio/BGM_Baking.BGM_Baking"):TEXT("/Game/FoodAudio/BGM_Game.BGM_Game");
    USoundBase* Sound=LoadObject<USoundBase>(nullptr,Path);if(!Sound)return;
    if(UAudioComponent* Old=State.Audio.Get()){Old->Stop();Old->DestroyComponent();}
    UAudioComponent* Audio=UGameplayStatics::CreateSound2D(World,Sound,Track==EFoodMusic::Ending?0.32f:Track==EFoodMusic::Baking?0.28f:0.30f,1.f,0.f,nullptr,false,false);
    if(Audio){Audio->SetUISound(bJournalVisible && Track==EFoodMusic::Ending);Audio->Play();State.Audio=Audio;State.Track=Track;UE_LOG(LogTemp,Log,TEXT("[FoodMusic] %s"),Path);}
}
}
void UFoodGraphTool::SetBackgroundMusic(UWorld* World, bool bEnding)
{ SetFoodMusic(World,bEnding?EFoodMusic::Ending:EFoodMusic::Game); }
void UFoodGraphTool::SetEndingJournalMusic(UWorld* World, bool bJournalVisible)
{ SetFoodMusic(World,EFoodMusic::Ending,bJournalVisible); }
void UFoodGraphTool::SetBakingMusic(UWorld* World)
{ SetFoodMusic(World,EFoodMusic::Baking); }
FString UFoodGraphTool::WirePlacementCues(const FString& AssetPath)
{
#if WITH_EDITOR
    UBlueprint* BP=LoadObject<UBlueprint>(nullptr,*AssetPath);if(!BP)return TEXT("missing BP");
    const bool Station=AssetPath.Contains(TEXT("BP_Workstation"));const bool Bowl=AssetPath.Contains(TEXT("BP_FillingBowl"));if(!Station&&!Bowl)return TEXT("unsupported BP");
    const TCHAR* Graph=Station?TEXT("PlaceStationItem"):TEXT("Interact");const TCHAR* Source=Station?TEXT("K2Node_VariableSet_0"):TEXT("K2Node_VariableSet_2");const TCHAR* Target=Station?TEXT("K2Node_DynamicCast_7"):TEXT("K2Node_CallFunction_8");
    TArray<UEdGraph*> Graphs;BP->GetAllGraphs(Graphs);for(auto G:Graphs)if(G->GetName()==Graph){
      UEdGraphNode *S=nullptr,*T=nullptr;for(auto N:G->Nodes){if(N->GetName()==Source)S=N;if(N->GetName()==Target)T=N;}if(!S||!T)return TEXT("missing node");
      UEdGraphPin* Out=S->FindPin(TEXT("then"));UEdGraphPin* In=T->FindPin(TEXT("execute"));if(!Out||!In||!Out->LinkedTo.Contains(In))return TEXT("unexpected edge");
      if(Bowl){UEdGraphPin* Label=S->FindPin(TEXT("PromptLabel"));if(!Label||Label->DefaultValue!=TEXT("馅料碗（派底已放好）"))return TEXT("unexpected bowl branch");}
      G->Modify();S->Modify();T->Modify();UK2Node_CallFunction* Call=NewObject<UK2Node_CallFunction>(G);Call->SetFromFunction(StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UFoodGraphTool,PlayCookingCue)));G->AddNode(Call,true,false);Call->CreateNewGuid();Call->PostPlacedNewNode();Call->AllocateDefaultPins();Call->NodePosX=S->NodePosX+180;Call->NodePosY=S->NodePosY+120;
      UK2Node_Self* Self=NewObject<UK2Node_Self>(G);G->AddNode(Self,true,false);Self->CreateNewGuid();Self->PostPlacedNewNode();Self->AllocateDefaultPins();Self->NodePosX=Call->NodePosX-100;Self->NodePosY=Call->NodePosY+100;
      UEdGraphPin* Cue=Call->FindPin(TEXT("Cue"));if(!Cue)return TEXT("missing cue");Cue->DefaultValue=Station?TEXT("IngredientPlacement"):TEXT("PieBase");const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();if(!Schema->TryCreateConnection(Self->FindPin(TEXT("self")),Call->FindPin(TEXT("Context"))))return TEXT("self failed");Out->BreakLinkTo(In);if(!Schema->TryCreateConnection(Out,Call->GetExecPin())||!Schema->TryCreateConnection(Call->GetThenPin(),In))return TEXT("edge failed");
      FBlueprintEditorUtils::MarkBlueprintAsModified(BP);FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status==BS_Error?TEXT("compile failed"):TEXT("wired; save required");
    }return TEXT("missing graph");
#else
    return TEXT("editor only");
#endif
}
