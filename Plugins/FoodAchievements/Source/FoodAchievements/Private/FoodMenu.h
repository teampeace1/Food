#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"

#include "FoodMenu.generated.h"

class UWorld;

namespace FoodMenu
{
    void Tick(UWorld* World);
    void Shutdown(UWorld* World);
}

/** 把 UMG 按钮/滑条的动态委托转发到普通 lambda（随 Widget 一起回收）。 */
UCLASS()
class UFoodMenuAction : public UObject
{
    GENERATED_BODY()

public:
    TFunction<void()> ClickAction;
    TFunction<void(float)> SlideAction;

    UFUNCTION()
    void HandleClick()
    {
        if (ClickAction) ClickAction();
    }

    UFUNCTION()
    void HandleSlide(float Value)
    {
        if (SlideAction) SlideAction(Value);
    }
};
