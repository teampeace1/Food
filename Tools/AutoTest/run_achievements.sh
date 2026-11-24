#!/usr/bin/env bash
# 成就链路诊断：真实跑一次「擀面 + 烘烤」，让成就系统自己的扫描去解锁，然后报告 6 枚勋章的落点。
#   用法: bash Tools/AutoTest/run_achievements.sh
# 会临时重置成就存档，跑完（无论成败）自动还原。
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
PROJ="$(pwd -W 2>/dev/null || pwd)"
UE="${UE_ROOT:-D:/ue/UE_5.8}"
MAP="/Game/0Input/map/Kitchen_white_final_supply"
LOG=/tmp/food_ach.log

# UBT 偶尔会用 UTF-8 重新生成 .rsp，而 VS 装在中文路径下 -> 先转成 UTF-16LE 再编
echo "[1/3] 编译 FoodAchievements ..."
python Tools/EditorScripts/fix_rsp_utf16.py > /dev/null 2>&1 || true
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
    echo "      UBT 未通过，改用手动 cl/link ..."
    MOD="$(pwd -W)/Plugins/FoodAchievements/Intermediate/Build/Win64/x64/UnrealEditor/Development/FoodAchievements"
    BIN="$(pwd -W)/Plugins/FoodAchievements/Binaries/Win64/UnrealEditor-FoodAchievements.dll"
    BEFORE=$(stat -c %Y "$BIN" 2>/dev/null || echo 0)
    rm -f "$BIN" 2>/dev/null || true
    powershell -NoProfile -Command "
\$vc = 'D:\新建文件夹\VC\Auxiliary\Build\vcvars64.bat'
\$d  = '$MOD'
\$chain = \"\`\"\$vc\`\" && cd /d \`\"D:\ue\UE_5.8\Engine\Source\`\" && cl.exe @\`\"\$d\Module.FoodAchievements.cpp.obj.rsp\`\" /nologo && cl.exe @\`\"\$d\FoodAchievementSubsystem.cpp.obj.rsp\`\" /nologo && cl.exe @\`\"\$d\FoodAutoTestSubsystem.cpp.obj.rsp\`\" /nologo && cl.exe @\`\"\$d\FoodIngredientVisualSubsystem.cpp.obj.rsp\`\" /nologo && link.exe @\`\"\$d\UnrealEditor-FoodAchievements.dll.rsp\`\" /NOLOGO\"
cmd /c \$chain 2>&1 | Select-Object -Last 6
" | grep -aE "error|LNK|\.cpp$" | head -12
    AFTER=$(stat -c %Y "$BIN" 2>/dev/null || echo 0)
    if [ -f "$BIN" ] && [ "$AFTER" != "$BEFORE" ]; then
        echo "      编译通过 (cl/link)"
    else
        echo "      编译失败，看 /tmp/food_build2.log"
        exit 1
    fi
fi

echo "[2/3] 启动游戏跑成就诊断 ..."
rm -f Saved/FoodAutoTest.json
MSYS_NO_PATHCONV=1 timeout 200 "$UE/Engine/Binaries/Win64/UnrealEditor-Cmd.exe" "$PROJ/Food.uproject" "$MAP" \
    -game -nullrhi -nosplash -stdout -FoodAch > "$LOG" 2>&1

echo "[3/3] 报告"
python Tools/AutoTest/report.py
echo "      成就事件日志:"
grep -a "Food achievement unlocked\|ach diag\|mock:\|\[waiting\|\[before mock\|\[after mock" "$LOG" | sed 's/^.*LogTemp: //' | head -40
