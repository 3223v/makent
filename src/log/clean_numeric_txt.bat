@echo off
setlocal enabledelayedexpansion

:: 切换到脚本所在目录
cd /d "%~dp0"

echo 开始清理当前目录下以纯数字命名的 .txt 文件...

:: 使用 dir 列出所有 .txt 文件，并通过 findstr 正则过滤出纯数字命名的文件
:: ^[0-9][0-9]*\.txt$ 匹配：以数字开头，后跟0个或多个数字，以 .txt 结尾
for /f "delims=" %%F in ('dir /b /a-d *.txt 2^>nul ^| findstr /r "^[0-9][0-9]*\.txt$"') do (
    del /f /q "%%F"
    echo [已删除] %%F
)

echo 清理完成。
pause
