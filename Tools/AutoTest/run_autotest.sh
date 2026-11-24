#!/usr/bin/env bash
# 厨房场景一键自动验证
#   编译 FoodAchievements  ->  无窗口启动 stand-alone 游戏并附带 -FoodTest  ->  打印检查报告
# 用途：改完 C++ 或关卡后自检，不需要人工进 PIE。
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
PROJ="$(pwd -W 2>/dev/null || pwd)"
UE="${UE_ROOT:-D:/ue/UE_5.8}"
MAP="/Game/0Input/map/Kitchen_white_final_supply"
LOG=/tmp/food_autotest.log

# UBT 偶尔会用 UTF-8 重新生成 .rsp，而 VS 装在中文路径下 -> 先转成 UTF-16LE 再编
echo "[1/3] 编译 FoodAchievements ..."
python Tools/EditorScripts/fix_rsp_utf16.py > /dev/null 2>&1 || true
# 第一次可能因为 VS 装在中文路径下、UBT 生成的 .rsp 是 UTF-8 而失败；转码后再编一次。
"$UE/Engine/Build/BatchFiles/Build.bat" FoodEditor Win64 Development -Project="$PROJ/Food.uproject" \
    -Module=FoodAchievements -NoUBA -WaitMutex > /tmp/food_build1.log 2>&1
if ! grep -q "Result: Succeeded" /tmp/food_build1.log; then
    python Tools/EditorScripts/fix_rsp_utf16.py > /dev/null 2>&1
    "$UE/Engine/Build/BatchFiles/Build.bat" FoodEditor Win64 Development -Project="$PROJ/Food.uproject" \
        -Module=FoodAchievements -NoUBA -WaitMutex > /tmp/food_build2.log 2>&1
fi
if grep -q "Result: Succeeded" /tmp/food_build1.log /tmp/food_build2.log 2>/dev/null; then
    echo "      编译通过 (UBT)"
else
    # UBT 的动作执行器在这台机器上有时会被安全策略打断（cl 启动即退出、无诊断），
    # 这时直接用 UBT 生成好的 .rsp 调 cl/link，等价且稳定。
    echo "      UBT 未通过，改用手动 cl/link ..."
    MOD="$(pwd -W)/Plugins/FoodAchievements/Intermediate/Build/Win64/x64/UnrealEditor/Development/FoodAchievements"
    BIN="$(pwd -W)/Plugins/FoodAchievements/Binaries/Win64/UnrealEditor-FoodAchievements.dll"
    BEFORE=$(stat -c %Y "$BIN" 2>/dev/null || echo 0)
    rm -f "$BIN" 2>/dev/null || true
    powershell -NoProfile -Command "
\$vc = 'D:\新建文件夹\VC\Auxiliary\Build\vcvars64.bat'
\$d  = '$MOD'
\$chain = \"\`\"\$vc\`\" && cd /d \`\"D:\ue\UE_5.8\Engine\Source\`\" && cl.exe @\`\"\$d\Module.FoodAchievements.cpp.obj.rsp\`\" /nologo && cl.exe @\`\"\$d\FoodAutoTestSubsystem.cpp.obj.rsp\`\" /nologo && cl.exe @\`\"\$d\FoodIngredientVisualSubsystem.cpp.obj.rsp\`\" /nologo && link.exe @\`\"\$d\UnrealEditor-FoodAchievements.dll.rsp\`\" /NOLOGO\"
cmd /c \$chain 2>&1 | Select-Object -Last 5
" | grep -aE "error|LNK|\.cpp$" | head -10
    AFTER=$(stat -c %Y "$BIN" 2>/dev/null || echo 0)
    if [ -f "$BIN" ] && [ "$AFTER" != "$BEFORE" ]; then
        echo "      编译通过 (cl/link)"
    else
        echo "      编译失败，看 /tmp/food_build2.log"
        exit 1
    fi
fi

echo "[2/3] 启动游戏跑自动检查 ..."
rm -f Saved/FoodAutoTest.json
MSYS_NO_PATHCONV=1 timeout 180 "$UE/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "$PROJ/Food.uproject" "$MAP" \
    -game -nullrhi -nosplash -stdout -FoodTest > "$LOG" 2>&1

echo "[3/3] 报告"
python Tools/AutoTest/report.py
