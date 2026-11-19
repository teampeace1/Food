@echo off
cd /d "D:\ue\UE_5.8\Engine\Binaries\Win64"
start "" "UnrealEditor.exe" "D:\ue\FirstPersonGame58\FirstPersonGame58.uproject" "D:\ue\FirstPersonGame58\Content\Maps\L_Kitchen_Whitebox.umap" -ExecCmds="py D:/ue/setcam.py"
exit
