@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo [INFO] Scanning for __pycache__ directories under: %CD%
set /a count=0

for /d /r %%D in (__pycache__) do (
    if exist "%%D" (
        echo [DELETE] %%D
        rd /s /q "%%D"
        set /a count+=1
    )
)

echo [DONE] Removed !count! __pycache__ directorie(s).
endlocal
